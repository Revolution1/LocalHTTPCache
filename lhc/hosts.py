# deprecated

import logging
import os
import re

import ipaddress

from consts import LHC_HOSTS_PATH, SYS_HOSTS_PATH

log = logging.getLogger('lhc')

HOSTNAME_REG = re.compile(
    r'^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$')


def is_valid_hostname(h):
    return HOSTNAME_REG.match(h)


def is_valid_ip(ip):
    try:
        ipaddress.ip_address(unicode(ip))
    except ValueError:
        return False
    return True


LHC_HOSTS_HEADER = '# ---------- BEGIN LHC HOSTS FILE ----------'
LHC_HOSTS_FOOTER = '# ---------- END LHC HOSTS FILE ------------'
LHC_HOSTS_CONTENT_REG = re.compile(LHC_HOSTS_HEADER + '.*' + LHC_HOSTS_FOOTER, flags=re.DOTALL)


class LHCHosts(object):
    def __init__(self, lhc_hosts_path=LHC_HOSTS_PATH):
        if lhc_hosts_path == SYS_HOSTS_PATH:
            log.warn("lhc_hosts_path '%s' and system hosts path '%s' are the same" % (lhc_hosts_path, SYS_HOSTS_PATH))
        self.lhc_hosts_path = lhc_hosts_path
        self.load()

    def load(self):
        hosts = {}
        if not os.path.exists(self.lhc_hosts_path):
            self.hosts = {}
            return
        with open(self.lhc_hosts_path) as f:
            for ln, l in enumerate(f.readlines()):
                l = l.strip()
                if l.startswith('#'):
                    continue
                split = l.split()
                if not len(split) == 2:
                    raise SyntaxError("hosts file '%s' syntax error at line %s" % (self.lhc_hosts_path, ln + 1))
                addr, host = split
                if not is_valid_ip(addr):
                    raise ValueError("Invalid IP address, %s:line %s" % (self.lhc_hosts_path, ln + 1))
                if not is_valid_hostname(host):
                    raise ValueError("Invalid DNS Hostname, %s':line %s" % (self.lhc_hosts_path, ln + 1))
                if host in hosts:
                    log.warn("Duplicate DNS Hostname %s, %s:line %s" % (host, self.lhc_hosts_path, ln + 1))
                hosts[host] = addr
            self.hosts = hosts

    def _dumps(self):
        tpl = '\n'.join([LHC_HOSTS_HEADER, '%s', LHC_HOSTS_FOOTER]) + '\n'
        content = tpl % '\n'.join('%s %s' % (ip, host) for host, ip in self.hosts.items())
        return content

    def save(self):
        with open(self.lhc_hosts_path, 'w') as f:
            f.write(self._dumps())

    def deactivate(self):
        with open(SYS_HOSTS_PATH, 'r+') as f:
            content = f.read()
            content = LHC_HOSTS_CONTENT_REG.sub('', content)
            f.seek(0)
            f.truncate()
            f.write(content.strip() + '\n')

    def activate(self):
        self.deactivate()
        with open(SYS_HOSTS_PATH, 'ab') as f:
            with open(self.lhc_hosts_path, 'r') as g:
                f.write('\n')
                f.write(g.read())

    def is_activated(self):
        with open(SYS_HOSTS_PATH, 'r') as f:
            return LHC_HOSTS_CONTENT_REG.search(f.read())

    def get(self, hostname):
        return self.hosts.get(hostname)

    def set(self, ip, hostname):
        if not is_valid_ip(ip):
            raise ValueError("Invalid IP address")
        if not is_valid_hostname(hostname):
            raise ValueError("Invalid DNS Hostname")
        self.hosts[hostname] = ip

    def delete(self, hostname):
        return self.hosts.pop(hostname)


if __name__ == '__main__':
    LHC_HOSTS_PATH = '/tmp/lhc_hosts_path'
    SYS_HOSTS_PATH = '/tmp/sys_hosts_path'
    lh = LHCHosts(LHC_HOSTS_PATH)
    print(lh.hosts)
    lh.set('127.0.0.1', 'example.com')
    print(lh.hosts)
    lh.save()
    with open(LHC_HOSTS_PATH) as f:
        print('set:\n' + f.read())
    lh.activate()
    with open(SYS_HOSTS_PATH) as f:
        print('activate:\n' + f.read())

    lh.deactivate()
    with open(SYS_HOSTS_PATH) as f:
        print('deactivate:\n' + f.read())
