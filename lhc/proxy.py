import subprocess
import sys

from consts import NGINX_DOCKER_IMAGE, PROXY_CONTAINER_NAME, NGINX_CONF_FILE_PATH, MAC, MAC_ALIAS_IP
from errors import ProxyError
from nginx_conf import get_nginx_conf
from utils import find_executable


class Proxy(object):
    def __init__(self, config):
        self.config = config

    def run(self):
        pass

    def stop(self):
        pass

    def running(self):
        pass

    def get_ip(self):
        pass

    def _dumps_nginx_conf(self):
        return get_nginx_conf(self.config)

    def dump_nginx_conf(self):
        with open(NGINX_CONF_FILE_PATH, 'wb') as f:
            f.write(self._dumps_nginx_conf().encode('utf-8'))


class ProxyLocal(Proxy):
    def __init__(self, config):
        super(ProxyLocal, self).__init__(config)

    def install(self):
        print('Installing Nginx')
        if find_executable('yum'):
            subprocess.check_call('yum install -y nginx', shell=True)
        elif find_executable('apt-get'):
            subprocess.check_call('apt-get install -y nginx', shell=True)
        elif find_executable('brew'):
            subprocess.check_call('brew install nginx', shell=True)
        try:
            subprocess.check_call('nginx -v', shell=True)
            print('OK')
        except subprocess.CalledProcessError:
            print('LHC installation failed')


class ProxyDocker(Proxy):
    def __init__(self, config):
        super(ProxyDocker, self).__init__(config)

    def install(self):
        try:
            subprocess.check_output('docker info', shell=True)
        except subprocess.CalledProcessError:
            raise ProxyError('Docker executable not found, make sure you have docker installed')
        try:
            print('pulling image')
            subprocess.check_call('docker pull %s' % NGINX_DOCKER_IMAGE, shell=True)
            print('OK')
        except subprocess.CalledProcessError:
            print('LHC installation failed')
            sys.exit(1)

    def status(self):
        try:
            return subprocess.check_output("docker container inspect %s -f '{{.State.Status}}'" % PROXY_CONTAINER_NAME,
                                           shell=True, stderr=subprocess.PIPE).strip().lower()
        except subprocess.CalledProcessError:
            return

    def running(self):
        return self.status() == 'running'

    def get_ip(self):
        if MAC and self.running():
            return MAC_ALIAS_IP
        else:
            try:
                return subprocess.check_output(
                    "docker container inspect %s -f '{{.NetworkSettings.Networks.bridge.IPAddress}}'" % PROXY_CONTAINER_NAME,
                    shell=True, stderr=subprocess.PIPE).strip()
            except subprocess.CalledProcessError:
                return RuntimeError('proxy not running')

    def run(self):
        status = self.status()
        if status == 'running':
            raise ProxyError('Already Running')
        if status:
            subprocess.check_call('docker rm -f ' + PROXY_CONTAINER_NAME, shell=True)
        self.dump_nginx_conf()
        docker = find_executable('docker')
        if not docker:
            raise ProxyError('Need docker client executable')
        cmd = [docker, 'run', '--name', PROXY_CONTAINER_NAME, '-d', '--restart', 'always',
               '-v', NGINX_CONF_FILE_PATH + ':/etc/nginx/nginx.conf',
               '-v', '{0}:{0}'.format(self.config.cache_path),
               '--dns', self.config.dns_resolver]
        if MAC:
            print('configure port binding ip')
            subprocess.check_call('sudo ifconfig lo0 alias %s/24' % MAC_ALIAS_IP, shell=True)
            # TODO
            portmapping = ['-p', MAC_ALIAS_IP + ':80:80']
        else:
            portmapping = ['-p', '80:80']
        cmd += portmapping
        cmd += [NGINX_DOCKER_IMAGE]
        print('staring proxy container')
        print(' '.join(cmd))
        try:
            subprocess.check_call(cmd)
            print('OK')
        except subprocess.CalledProcessError:
            print('fail running proxy container')
            sys.exit(1)

    def stop(self):
        if not self.status():
            raise ProxyError('proxy container not created')
        subprocess.check_call('docker rm -f ' + PROXY_CONTAINER_NAME, shell=True)
