from __future__ import print_function

import logging
import os
from collections import OrderedDict

import click
import tabulate

from configuration import Config
from consts import CONF_PATH, CONF_HOSTS_PATH, CONF_FILE_PATH, NGINX_CONF_FILE_PATH, MAC_ALIAS_IP, NGINX_DOCKER_IMAGE, \
    PROXY_CONTAINER_NAME, COMMON_EXTENSIONS, DEBUG
from errors import handle_error
from utils import warp_join, require_root

log = logging.getLogger('lhc')
hdlr = logging.StreamHandler()
# hdlr.setFormatter(logging.Formatter('%(filename)-25s %(lineno)4d %(levelname)-8s %(message)s'))
hdlr.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
log.addHandler(hdlr)

log.setLevel(logging.INFO)
if DEBUG:
    log.setLevel(logging.DEBUG)


class OrderedGroup(click.Group):
    def __init__(self, name=None, commands=None, **attrs):
        super(OrderedGroup, self).__init__(name=name, commands=commands, **attrs)
        self.commands = self.commands or OrderedDict()

    def list_commands(self, ctx):
        return self.commands


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.group(cls=OrderedGroup, context_settings=CONTEXT_SETTINGS)
def main():
    """
    LHC (Local HTTP Cache), cache static files to your local machine
    """


config = Config.load()


@main.command()
@click.option('-v', '--verbose', is_flag=True, default=False, help='verbose info')
@handle_error
def info(verbose):
    """
    show the running status of LHC
    """
    config = Config.load()
    running = config.proxy.running()
    print('Proxy:')
    print('    Mode: %s' % config.mode)
    print('    Status: %s' % ('Running' if running else 'Stopped'))
    print('    CA Cert: %s' % config.proxy.ca_status())
    print('    HTTP Port: %s' % config.http_port)
    print('    HTTPS Port: %s' % config.https_port)
    print('    SSL: %s' % config.ssl)

    print()
    print('Hosts:')
    print('    Status: %s' % ('Activated' if config.hosts_activated() else 'Deactivated'))
    print('    Count: %s' % len(config.hosts))
    if running:
        print('    IP: %s' % config.proxy.get_ip())
    print('    CachePath: %s' % config.cache_path)
    print()
    if verbose:
        print('Defaults:')
        print('    Extensions: %s' % config.extensions)
        print('    CacheSizeLimit: %s' % config.cache_size_limit)
        print('    CacheExpire: %s' % config.cache_expire)
        print('    CacheKey: %s' % config.cache_key)
        print('    DnsResolver: %s' % config.dns_resolver)
        print()
        print('Consts:')
        print('    CONF_PATH: %s' % CONF_PATH)
        print('    CONF_HOSTS_PATH: %s' % CONF_HOSTS_PATH)
        print('    CONF_FILE_PATH: %s' % CONF_FILE_PATH)
        print('    NGINX_CONF_FILE_PATH: %s' % NGINX_CONF_FILE_PATH)
        print('    MAC_ALIAS_IP: %s' % MAC_ALIAS_IP)
        print('    NGINX_DOCKER_IMAGE: %s' % NGINX_DOCKER_IMAGE)
        print('    PROXY_DOCKER_NAME: %s' % PROXY_CONTAINER_NAME)
        print()
        print('Built-in extensions:')
        for k, es in COMMON_EXTENSIONS.items():
            print('    %s: %s' % (k, warp_join(',', es, newline='\n' + ' ' * (len(k) + 6))))
        print()


@main.command()
@handle_error
def run():
    """
    run LHC proxy
    """
    require_root()
    config.proxy.run()


@main.command()
@handle_error
def stop():
    """
    stop LHC proxy
    """
    require_root()
    config.proxy.stop()


@main.command()
@handle_error
def reload():
    """
    reload configurations
    """
    require_root()
    config.proxy.stop()
    config.proxy.run()


@main.command()
@handle_error
def ls():
    """
    list hosts
    """
    headers = ('NAME', 'EXTENSIONS', 'LIMIT', 'EXPIRE',
               'KEY', 'PROXY IP', 'DNS RESOLVER', 'CONF PATH')
    fields = ('name', 'extensions_display', 'cache_size_limit', 'cache_expire',
              'cache_key', 'proxy_ip', 'dns_resolver', 'path')
    data = []
    for h in config.hosts.values():
        record = []
        for f in fields:
            record.append(getattr(h, f))
        data.append(record)
    print(tabulate.tabulate(data, headers))


@main.command()
@click.option('-e', '--extensions', help="cache files with specified filename extensions (separated by ',')")
@click.option('-s', '--cache-size-limit', help='the max cache size of the host')
@click.option('-t', '--cache-expire', help='the cache expire time of the host')
@click.option('-k', '--cache-key', help='key of the the cache file')
@click.option('-p', '--proxy-ip', help='proxy ip of the host, you can set it if you want to use a external address')
@click.option('-n', '--dns-resolver', help='the dns resolver to resolve the host')
@click.argument('hostname')
@handle_error
def set(hostname, extensions, cache_size_limit, cache_expire, cache_key, proxy_ip, dns_resolver):
    """
    add a host
    """
    h = config.set_host(hostname=hostname, extensions=extensions, cache_size_limit=cache_size_limit,
                        cache_expire=cache_expire, cache_key=cache_key, proxy_ip=proxy_ip, dns_resolver=dns_resolver)
    log.info('OK, host config wrote to ' + h._path)
    log.info('To take effect, you need to reload proxy and activate hosts')


@main.command('del')
@click.argument('hostname')
@handle_error
def delete(hostname):
    """
    delete a host
    """
    print(config.delete_host(hostname).name)
    log.info('To take effect, you need to reload proxy and activate hosts')


@main.command()
@handle_error
def activate():
    """
    activate hosts
    """
    require_root()
    config.activate_hosts()


@main.command()
@handle_error
def deactivate():
    """
    activate hosts
    """
    require_root()
    config.deactivate_hosts()


@main.command()
@click.option('-h', is_flag=True, default=False, help='human friendly size unit')
@handle_error
def df(h):
    """
    show cache file disk usage
    """
    from utils import get_dir_size
    import bitmath
    bitmath.format_string = "{value:.1f} {unit}"
    headers = ('HOST', 'CACHE PATH', 'LIMIT', 'DISK USAGE')
    data = []
    for host in config.hosts.values():
        if not os.path.exists(host.cache_path):
            size = 0
        else:
            size = get_dir_size(host.cache_path)
        if h and size:
            size = bitmath.Byte(size).best_prefix(bitmath.NIST)
        data.append((host.name, host.cache_path, host.cache_size_limit, str(size)))
    print(tabulate.tabulate(data, headers))


@main.command()
@click.argument('hostname')
@handle_error
def purge(hostname):
    """
    purge cache of a host
    """
    config.purge(hostname)
    log.info('OK')


@main.command('gen-ca')
@handle_error
def gen_ca():
    """
    generate self-signed ca certificate
    """
    require_root()

    config.proxy.gen_ca_certs()
    log.info('OK')


@main.command('install-ca')
@handle_error
def install_ca():
    """
    install ca to system's certificate chain
    """
    require_root()

    config.proxy.install_ca_cert()
    log.info('OK')


if __name__ == '__main__':
    main()
