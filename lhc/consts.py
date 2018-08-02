import os
import platform
from os import path

from utils import find_executable

SYS_HOSTS_PATH = '/etc/hosts'

DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', 'y', '1')

CONF_PATH = os.getenv('CONF_PATH') or '/etc/lhc'
CONF_HOSTS_PATH = path.join(CONF_PATH, 'hosts')
CONF_FILE_PATH = path.join(CONF_PATH, 'lhc.conf')
NGINX_CONF_FILE_PATH = path.join(CONF_PATH, 'nginx.conf')

MAC_ALIAS_IP = os.getenv('MAC_ALIAS_IP') or '192.168.221.181'
NGINX_DOCKER_IMAGE = os.getenv('NGINX_DOCKER_IMAGE') or 'daocloud.io/nginx'
PROXY_CONTAINER_NAME = os.getenv('PROXY_DOCKER_NAME') or 'lhc-proxy'

CERT_FILES_PATH = path.join(CONF_PATH, 'certs')
CA_CERT_FILES_PATH = path.join(CERT_FILES_PATH, 'ca')
HOST_CERTS_FILES_PATH = path.join(CERT_FILES_PATH, 'hosts')
CA_CN = 'LHC Self-Signed CA'
CA_SUB = '/O=Wakanda/OU=LHC/CN=' + CA_CN

COMMON_EXTENSIONS = {
    '__WEB__': ['bmp', 'ejs', 'jpeg', 'pdf', 'ps', 'ttf', 'class', 'eot', 'jpg', 'pict', 'svg', 'webp', 'css',
                'eps', 'js', 'pls', 'svgz', 'woff', 'csv', 'gif', 'mid', 'png', 'swf', 'woff2', 'doc', 'ico',
                'midi', 'ppt', 'tif', 'xls', 'docx', 'jar', 'otf', 'pptx', 'tiff', 'xlsx'],
    '__PKG__': ['deb', 'rpm', 'tar', 'gz', 'xz', 'zip', 'apk', 'iso'],
    '__PIP__': ['whl']
}

DEFAULT_CONF_ITEMS = {
    'extensions': '__WEB__',
    'cache_path': path.expanduser('~/.local/lhc.cache'),
    'cache_size_limit': '10g',
    'cache_expire': '3d',
    'cache_key': '$host$uri$is_args$args',
    'http_port': 80,
    'https_port': 443,
    'mode': 'docker',
    'proxy_ip': 'auto',
    'dns_resolver': '114.114.114.114',
    'ssl': 'true'
}

DEFAULT_CONF = """\
# LHC Config file
# built-in exts:
# __WEB__: {WEB}
# __PKG__: {PKG}
# __PIP__: {PIP}
# global section defines the default values of cache and settings of proxy
[global]
# will cache files that has these filename extension
extensions = {extensions}
cache_size_limit = {cache_size_limit}
cache_expire = {cache_expire}
cache_key = {cache_key}
http_port = {http_port}
https_port = {https_port}
dns_resolver = {dns_resolver}

# run proxy as local process (nginx) or as docker container
# local or docker
mode = {mode}

cache_path = {cache_path}

# set it when use a outside proxy server
proxy_ip = {proxy_ip}
""".format(WEB=COMMON_EXTENSIONS['__WEB__'],
           PKG=COMMON_EXTENSIONS['__PKG__'],
           PIP=COMMON_EXTENSIONS['__PIP__'],
           **DEFAULT_CONF_ITEMS)

MAC = 'Darwin' in platform.platform()
LINUX = 'Linux' in platform.platform()
AMD64 = 'x86_64' in platform.platform()
REDHAT = os.path.exists('/etc/redhat-release')
DEBIAN = find_executable('apt-get')
