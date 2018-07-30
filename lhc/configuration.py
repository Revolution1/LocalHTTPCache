import ConfigParser
import logging
import os
import re
import shutil

from consts import CONF_FILE_PATH, DEFAULT_CONF, DEFAULT_CONF_ITEMS, CONF_HOSTS_PATH, COMMON_EXTENSIONS
from consts import SYS_HOSTS_PATH
from errors import ConfigError
from proxy import ProxyDocker, ProxyLocal
from utils import cached_property, warp_join
from utils import is_valid_ip, is_valid_hostname, mkdirs

log = logging.getLogger('lhc')

LHC_HOSTS_HEADER = '# ---------- BEGIN LHC HOSTS CONTENT ----------'
LHC_HOSTS_FOOTER = '# ---------- END LHC HOSTS CONTENT ------------'
LHC_HOSTS_CONTENT_REG = re.compile(LHC_HOSTS_HEADER + '.*' + LHC_HOSTS_FOOTER, flags=re.DOTALL)


class Config(object):
    def __init__(self, extensions=None, cache_path=None, cache_size_limit=None, cache_expire=None,
                 cache_key=None, http_port=None, mode=None, proxy_ip=None, dns_resolver=None, conf=None):
        self.extensions = extensions
        if cache_path:
            cache_path = cache_path.rstrip('/')
        self.cache_path = cache_path
        self.cache_size_limit = cache_size_limit
        self.cache_expire = cache_expire
        self.cache_key = cache_key
        self.http_port = http_port
        self.mode = mode
        self._proxy_ip = proxy_ip
        self.dns_resolver = dns_resolver
        self._conf = conf
        self._load_hosts()

    @cached_property
    def proxy(self):
        if self.mode == 'docker':
            return ProxyDocker(self)
        elif self.mode == 'local':
            return ProxyLocal(self)
        else:
            raise ConfigError('unknown mode ' + self.mode)

    @cached_property
    def proxy_ip(self):
        if self._proxy_ip == 'auto':
            return self.proxy.get_ip()
        if not is_valid_ip(self._proxy_ip):
            raise ConfigError('invalid proxy_ip %s' % self._proxy_ip)
        return self._proxy_ip

    @classmethod
    def load(cls):
        if not os.path.exists(CONF_FILE_PATH):
            mkdirs(os.path.dirname(CONF_FILE_PATH))
            with open(CONF_FILE_PATH, 'wb') as f:
                f.write(DEFAULT_CONF)
            log.info('config file created at ' + CONF_FILE_PATH)
        cp = ConfigParser.RawConfigParser(DEFAULT_CONF_ITEMS)
        cp.read(CONF_FILE_PATH)
        return cls(
            extensions=cp.get('global', 'extensions'),
            cache_path=cp.get('global', 'cache_path'),
            cache_size_limit=cp.get('global', 'cache_size_limit'),
            cache_expire=cp.get('global', 'cache_expire'),
            cache_key=cp.get('global', 'cache_key'),
            http_port=cp.get('global', 'http_port'),
            mode=cp.get('global', 'mode'),
            dns_resolver=cp.get('global', 'dns_resolver'),
            proxy_ip=cp.get('global', 'proxy_ip'),
            conf=cp,
        )

    def save(self):
        cp = ConfigParser.RawConfigParser()
        cp.add_section('global')
        self.extensions and cp.set('global', 'extensions', self.extensions)
        self.cache_path and cp.set('global', 'cache_path', self.cache_path)
        self.cache_size_limit and cp.set('global', 'cache_size_limit', self.cache_size_limit)
        self.cache_expire and cp.set('global', 'cache_expire', self.cache_expire)
        self.cache_key and cp.set('global', 'cache_key', self.cache_key)
        self.http_port and cp.set('global', 'http_port', self.http_port)
        self.dns_resolver and cp.set('global', 'dns_resolver', self.dns_resolver)
        self.mode and cp.set('global', 'mode', self.mode)
        self._proxy_ip and cp.set('global', 'proxy_ip', self._proxy_ip)

        with open(CONF_FILE_PATH, 'wb') as f:
            cp.write(f)

        for host in self.hosts.values():
            host.save()

    def _load_hosts(self):
        self.hosts = {}
        if not os.path.exists(CONF_HOSTS_PATH):
            return
        for p in os.listdir(CONF_HOSTS_PATH):
            path = os.path.join(CONF_HOSTS_PATH, p)
            if not os.path.isfile(path):
                continue
            host = Host.from_path(path, g=self)
            if host.name in self.hosts:
                raise ConfigError(
                    "duplicate hostname '%s' of file %s and %s" % (host.name, host._path, self.hosts[host.name]._path))
            self.hosts[host.name] = host

    def _dumps_hosts(self):
        if not self.proxy.running():
            raise ConfigError('you should run proxy first')
        tpl = '\n'.join([LHC_HOSTS_HEADER, '%s', LHC_HOSTS_FOOTER]) + '\n'
        content = tpl % '\n'.join('%s %s' % (host.proxy_ip, host.name) for host in self.hosts.values())
        return content

    def deactivate_hosts(self):
        with open(SYS_HOSTS_PATH, 'r+') as f:
            content = f.read()
            content = LHC_HOSTS_CONTENT_REG.sub('', content)
            f.seek(0)
            f.truncate()
            f.write(content.strip() + '\n')

    def activate_hosts(self):
        self.deactivate_hosts()
        with open(SYS_HOSTS_PATH, 'ab') as f:
            f.write('\n')
            f.write(self._dumps_hosts())

    def hosts_activated(self):
        with open(SYS_HOSTS_PATH, 'r') as f:
            return LHC_HOSTS_CONTENT_REG.search(f.read())

    def get_host(self, hostname):
        return self.hosts.get(hostname)

    def set_host(self, hostname, host=None, **kwargs):
        if host:
            if not isinstance(host, Host):
                raise ConfigError('host should be instance of ' + str(type(Host)))
            if not host._g:
                host._g = self
        if not host:
            host = Host(hostname, g=self, **kwargs)
        if hostname in self.hosts:
            if host._path != self.hosts[hostname]._path:
                os.remove(host._path)
        self.hosts[hostname] = host
        host.save()
        if self.hosts_activated():
            self.activate_hosts()
        return host

    def delete_host(self, hostname):
        if hostname not in self.hosts:
            raise ConfigError('hostname not found')
        host = self.hosts.pop(hostname)
        if os.path.isfile(host._path):
            os.remove(host._path)
        if self.hosts_activated():
            self.activate_hosts()
        return host

    def purge(self, hostname):
        if hostname not in self.hosts:
            raise ConfigError('hostname not found')
        host = self.hosts[hostname]
        shutil.rmtree(host.cache_path)


class Host(object):
    def __init__(self, name, extensions=None, cache_size_limit=None, cache_expire=None,
                 cache_key=None, proxy_ip=None, dns_resolver=None, conf=None, path=None, g=None):
        if not is_valid_hostname(name):
            raise ConfigError("invalid hostname '%s'" % (name))
        self.name = name
        self._extensions = extensions
        self._cache_size_limit = cache_size_limit
        self._cache_expire = cache_expire
        self._cache_key = cache_key
        self._proxy_ip = proxy_ip
        self._dns_resolver = dns_resolver
        self._conf = conf
        self._path = path or os.path.join(CONF_HOSTS_PATH, self.name)
        self._g = g

    @property
    def extensions_reg(self):
        exts = self._extensions or (self._g and self._g.extensions)
        exts = re.split(r'[,|]', exts)
        rt = []
        for ext in exts:
            if ext in COMMON_EXTENSIONS:
                rt.extend(COMMON_EXTENSIONS[ext])
            else:
                rt.append(ext.strip())
        return '|'.join(set(rt))

    @property
    def extensions_display(self):
        exts = self._extensions or (self._g and self._g.extensions)
        exts = re.split(r'[,|]', exts)
        return warp_join(',', exts, 20)

    @property
    def normalized_name(self):
        return self.name.replace('.', '_').replace('-', '_')

    @property
    def cache_name(self):
        return 'cache_' + self.normalized_name

    @property
    def cache_path(self):
        return os.path.join(self._g.cache_path, self.cache_name)

    @property
    def proxy_ip(self):
        if self._proxy_ip == 'auto' or not self._proxy_ip:
            return self._g.proxy_ip
        else:
            return self._proxy_ip

    @classmethod
    def from_path(cls, path, g=None):
        cp = ConfigParser.RawConfigParser()
        cp.read(path)
        if len(cp.sections()) != 1:
            raise ConfigError('host conf file %s must have exactly 1 section' % path)
        name = cp.sections()[0]

        def get(item):
            try:
                return cp.get(name, item)
            except:
                return

        return cls(name=name,
                   extensions=get('extensions'),
                   cache_size_limit=get('cache_size_limit'),
                   cache_expire=get('cache_expire'),
                   cache_key=get('cache_key'),
                   proxy_ip=get('proxy_ip'),
                   dns_resolver=get('dns_resolver'),
                   conf=cp,
                   path=path,
                   g=g)

    def __getattr__(self, item):
        if not hasattr(self, '_' + item):
            raise ConfigError("'%s' object has no attribute '%s'" % (type(self), item))
        return getattr(self, '_' + item) or getattr(self._g, item)

    def save(self):
        cp = ConfigParser.RawConfigParser()
        cp.add_section(self.name)
        self._extensions and cp.set(self.name, 'extensions', self._extensions)
        self._cache_size_limit and cp.set(self.name, 'cache_size_limit', self._cache_size_limit)
        self._cache_key and cp.set(self.name, 'cache_key', self._cache_key)
        self._proxy_ip and cp.set(self.name, 'proxy_ip', self._proxy_ip)

        if not os.path.exists(os.path.dirname(self._path)):
            mkdirs(os.path.dirname(self._path))
        with open(self._path, 'wb') as f:
            cp.write(f)
