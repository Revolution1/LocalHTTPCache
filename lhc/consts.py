import platform
from os import path

from utils import find_executable

SYS_HOSTS_PATH = '/etc/hosts'

CONF_PATH = '/etc/lhc'
CONF_HOSTS_PATH = path.join(CONF_PATH, 'hosts')
CONF_FILE_PATH = path.join(CONF_PATH, 'lhc.conf')
NGINX_CONF_FILE_PATH = path.join(CONF_PATH, 'nginx.conf')

COMMON_WEB_EXTENSIONS = ['bmp', 'ejs', 'jpeg', 'pdf', 'ps', 'ttf', 'class', 'eot', 'jpg', 'pict', 'svg', 'webp', 'css',
                         'eps', 'js', 'pls', 'svgz', 'woff', 'csv', 'gif', 'mid', 'png', 'swf', 'woff2', 'doc', 'ico',
                         'midi', 'ppt', 'tif', 'xls', 'docx', 'jar', 'otf', 'pptx', 'tiff', 'xlsx']

LINUX_PACKAGE_EXTENSIONS = ['deb', 'rpm', 'tar', 'gz', 'zip']

PIP_PACKAGE_EXTENSIONS = ['whl']

COMMON_EXTENSIONS = {
    '__WEB__': COMMON_WEB_EXTENSIONS,
    '__PKG__': LINUX_PACKAGE_EXTENSIONS,
    '__PIP__': PIP_PACKAGE_EXTENSIONS
}

MAC_ALIAS_IP = '192.168.221.181'

DEFAULT_CONF_ITEMS = {
    'extensions': '__WEB__',
    'cache_path': '/var/lib/lhc.cache',
    'cache_size_limit': '10g',
    'cache_expire': '5d',
    'cache_key': '$host$uri$is_args$args',
    'http_port': 80,
    'mode': 'docker',
    'proxy_ip': 'auto',
    'dns_resolver': '114.114.114.114'
}

DEFAULT_CONF = """\
# LHC Config file
# built-in exts:
# __WEB__: bmp,ejs,jpeg,pdf,ps,ttf,class,eot,jpg,pict,svg,webp,css,eps,js,pls,svgz,woff,csv,gif,mid,png,swf,woff2,doc,ico,midi,ppt,tif,xls,docx,jar,otf,pptx,tiff,xlsx
# __PKG__: deb,rpm,tar,tar.gz,zip
# __PIP__: whl
# global section defines the default values of cache and settings of proxy
[global]
# will cache files that has these filename extension
extensions = {extensions}
cache_size_limit = {cache_size_limit}
cache_expire = {cache_expire}
cache_key = {cache_key}
http_port = {http_port}
dns_resolver = {dns_resolver}

# run proxy as local process (nginx) or as docker container
# local or docker
mode = {mode}

cache_path = {cache_path}

# set it when use a outside proxy server
proxy_ip = {proxy_ip}
""".format(**DEFAULT_CONF_ITEMS)

NGINX_DOCKER_IMAGE = 'daocloud.io/nginx'
PROXY_DOCKER_NAME = 'lhc_proxy'

MAC = 'Darwin' in platform.platform()
LINUX = 'Linux' in platform.platform()
AMD64 = 'x86_64' in platform.platform()
REDHAT = find_executable('yum') or find_executable('dnf')
DEBIAN = find_executable('apt') or find_executable('apt-get')
