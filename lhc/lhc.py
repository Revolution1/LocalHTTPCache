import logging
from collections import OrderedDict

import click

from configuration import Config
from consts import CONF_PATH, CONF_HOSTS_PATH, CONF_FILE_PATH, NGINX_CONF_FILE_PATH, MAC_ALIAS_IP, NGINX_DOCKER_IMAGE, \
    PROXY_CONTAINER_NAME, COMMON_EXTENSIONS
from utils import warp_join

log = logging.getLogger('lhc')


class OrderedGroup(click.Group):
    def __init__(self, name=None, commands=None, **attrs):
        super(OrderedGroup, self).__init__(name=name, commands=commands, **attrs)
        self.commands = self.commands or OrderedDict()

    def list_commands(self, ctx):
        return self.commands


@click.group(cls=OrderedGroup)
def main():
    """
    LHC (Local HTTP Cache), cache static files to your local machine
    """


@main.command()
def status():
    """
    show the running status of LHC
    """
    config = Config.load()
    running = config.proxy.running()
    print('Proxy:')
    print('    Mode: %s' % config.mode)
    print('    Status: %s' % ('Running' if running else 'Not Running'))
    if running:
        print('    IP: %s' % config.proxy.get_ip())
    print('    CachePath: %s' % config.cache_path)

    print('Defaults:')
    print('    Extensions: %s' % config.extensions)
    print('    CacheSizeLimit: %s' % config.cache_size_limit)
    print('    CacheExpire: %s' % config.cache_expire)
    print('    CacheKey: %s' % config.cache_key)
    print('    HttpPort: %s' % config.http_port)
    print('    DnsResolver: %s' % config.dns_resolver)

    print('Consts:')
    print('    CONF_PATH: %s' % CONF_PATH)
    print('    CONF_HOSTS_PATH: %s' % CONF_HOSTS_PATH)
    print('    CONF_FILE_PATH: %s' % CONF_FILE_PATH)
    print('    NGINX_CONF_FILE_PATH: %s' % NGINX_CONF_FILE_PATH)
    print('    MAC_ALIAS_IP: %s' % MAC_ALIAS_IP)
    print('    NGINX_DOCKER_IMAGE: %s' % NGINX_DOCKER_IMAGE)
    print('    PROXY_DOCKER_NAME: %s' % PROXY_CONTAINER_NAME)

    print('Built-in extensions:')
    for k, es in COMMON_EXTENSIONS.items():
        print('    %s: %s' % (k, warp_join(',', es, newline='\n' + ' ' * (len(k) + 6))))

    print('Hosts:')
    print('    Status: %s' % ('Activated' if config.hosts_activated() else 'Deactivated'))

    hosts = []
    for host in config.hosts.values():
        pass


@main.command()
def run():
    """
    run LHC proxy
    """
    config = Config.load()


@main.command()
def stop():
    """
    stop LHC proxy
    """
    click.echo('Initialized the database')


@main.command()
def reload():
    """
    reload configurations
    """
    click.echo('Initialized the database')


@main.command()
def destroy():
    """
    stop LHC proxy and clean all the configures
    """
    click.echo('Initialized the database')


@main.command()
def ls():
    """
    list hosts
    """
    click.echo('Initialized the database')


@main.command()
def add():
    """
    add a host
    """
    click.echo('Initialized the database')


@main.command('del')
def delete():
    """
    delete a host
    """
    click.echo('Initialized the database')


@main.command()
def activate():
    """
    activate hosts
    """
    click.echo('Initialized the database')


@main.command()
def deactivate():
    """
    activate hosts
    """
    click.echo('Initialized the database')


if __name__ == '__main__':
    main()
