import logging
import os
import shutil
import subprocess
import sys
import tempfile

from consts import (NGINX_DOCKER_IMAGE, PROXY_CONTAINER_NAME, NGINX_CONF_FILE_PATH, MAC_ALIAS_IP,
                    CA_CERT_FILES_PATH, CA_SUB, HOST_CERTS_FILES_PATH, MAC, DEBIAN, REDHAT, CONF_PATH)
from errors import ProxyError, SSLError
from nginx_conf import get_nginx_conf
from utils import find_executable, mkdirs

log = logging.getLogger('lhc')

CA_KEY = os.path.join(CA_CERT_FILES_PATH, 'ca.key')
CA_CSR = os.path.join(CA_CERT_FILES_PATH, 'ca.csr')
CA_CRT = os.path.join(CA_CERT_FILES_PATH, 'ca.crt')


class Proxy(object):
    def __init__(self, config):
        self.config = config

    def run(self):
        for host in self.config.hosts.values():
            if not os.path.exists(host.cert_path):
                log.info('generating cert for ' + host.name)
                host.gen_certs()

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

    def gen_ca_certs(self):
        """
        openssl genrsa -out ca.key 2048
        openssl req -new -subj '/C=ZH/ST=wakanda/L=lhc/O=lhc/OU=lhc/CN=*' -key ca.key -out any.csr
        openssl x509 -req -days 3650 -in any.csr -signkey ca.key -out any.crt
        """
        openssl = find_executable('openssl')
        if not openssl:
            raise SSLError('openssl executable not found')
        if os.path.exists(CA_CRT):
            log.warn('ca cert file %s already exists' % CA_CRT)
        if not os.path.exists(CA_CERT_FILES_PATH):
            mkdirs(CA_CERT_FILES_PATH)
        cmds = (
            (openssl, 'genrsa', '-out', CA_KEY, '2048'),
            (openssl, 'req', '-new', '-subj', CA_SUB, '-key', CA_KEY, '-out', CA_CSR),
            (openssl, 'x509', '-req', '-days', '3560', '-sha256', '-extensions', 'v3_ca',
             '-signkey', CA_KEY, '-in', CA_CSR, '-out', CA_CRT),
        )
        for cmd in cmds:
            try:
                log.info(' '.join(cmd))
                subprocess.check_call(cmd)
            except subprocess.CalledProcessError:
                log.error('Fail')
                raise

    def check_ca(self):
        if not (os.path.exists(CA_CRT) and os.path.exists(CA_KEY)):
            raise SSLError('ca cert files not exist')
        return self.check_cert(CA_CRT)

    def ca_status(self):
        try:
            self.check_ca()
            return CA_CRT
        except SSLError as e:
            return str(e)

    def check_cert(self, path):
        openssl = find_executable('openssl')
        if not openssl:
            raise SSLError('openssl executable not found')
        try:
            return subprocess.check_output([openssl, 'x509', '-in', path, '-noout', '-text'], stderr=subprocess.PIPE)
        except subprocess.CalledProcessError:
            raise SSLError('cert ' + path + 'not valid')

    def get_host_cert_paths(self, cn):
        PATH = os.path.join(HOST_CERTS_FILES_PATH, cn)
        KEY = os.path.join(PATH, cn + '.key')
        CRT = os.path.join(PATH, cn + '.crt')
        CSR = os.path.join(PATH, cn + '.csr')
        return PATH, KEY, CRT, CSR

    def gen_and_sign_certs_for(self, cn):
        # https://my.oschina.net/itblog/blog/651434
        """
        openssl genrsa -out ca.key 2048
        openssl req -new -subj '/C=ZH/ST=wakanda/L=lhc/O=lhc/OU=lhc/CN=*' -key ca.key -out any.csr
        openssl x509 -req -days 3650 -in any.csr -signkey ca.key -out any.crt
        """
        self.check_ca()
        openssl = find_executable('openssl')
        if not openssl:
            raise SSLError('openssl executable not found')

        PATH, KEY, CRT, CSR = self.get_host_cert_paths(cn)
        SUB = '/O=Wakanda/OU=LHC/CN=' + cn

        if os.path.exists(CRT):
            log.warn('ca cert file %s already exists' % CRT)
        if not os.path.exists(PATH):
            mkdirs(PATH)

        san = 'subjectAltName=DNS:{0},DNS:www.{0},DNS:*.{0}'.format(cn)
        req = '\n'.join((
            '[ req ]',
            'req_extensions = v3_req',
            'distinguished_name	= req_distinguished_name',
            '[ v3_req ]',
            'basicConstraints = CA:FALSE',
            'keyUsage = nonRepudiation, digitalSignature, keyEncipherment',
            # 'subjectAltName = @alt_names',
            '[ req_distinguished_name ]',
            'commonName			= Common Name (eg, fully qualified host name)',
            '[SAN]',
            san
        ))
        with tempfile.NamedTemporaryFile() as f, tempfile.NamedTemporaryFile() as s:
            s.write(san)
            s.flush()
            f.write(req)
            f.flush()
            cmds = (
                (openssl, 'genrsa', '-out', KEY, '2048'),
                (openssl, 'req', '-new', '-subj', SUB, '-reqexts', 'SAN', '-config', f.name, '-key', KEY, '-out', CSR),
                (openssl, 'x509', '-req', '-days', '3560', '-sha256', '-CAcreateserial', '-extfile', s.name,
                 '-CA', CA_CRT,
                 '-CAkey', CA_KEY,
                 '-in', CSR,
                 '-out', CRT),
            )
            for cmd in cmds:
                try:
                    log.info(' '.join(cmd))
                    subprocess.check_call(cmd)
                except subprocess.CalledProcessError:
                    log.error('Fail')
                    raise

    def install_ca_cert(self):
        """
        mac: sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain <certificate>
        ubuntu: sudo cp my.crt /usr/local/share/ca-certificates/
                sudo update-ca-certificates
        centos: cp *.pem /etc/pki/ca-trust/source/anchors/
                update-ca-trust extract
        """
        if REDHAT:
            log.info('installing LHC CA Certificate')
            cert_path = '/etc/pki/ca-trust/source/anchors'
            if not os.path.exists(cert_path):
                raise SSLError(cert_path + ' not found, please check your system')
            dst = os.path.join(cert_path, 'lhc-ca.crt')
            log.info('copying cert file to ' + dst)
            shutil.copy(CA_CRT, dst)
            log.info('activating')
            subprocess.check_call('update-ca-trust extract', shell=True)
        elif DEBIAN:
            log.info('installing LHC CA Certificate')
            cert_path = '/usr/local/share/ca-certificates'
            if not os.path.exists(cert_path):
                raise SSLError(cert_path + ' not found, please check your system')
            dst = os.path.join(cert_path, 'lhc-ca.crt')
            log.info('copying cert file to ' + dst)
            shutil.copy(CA_CRT, dst)
            log.info('activating')
            subprocess.check_call('update-ca-certificates', shell=True)
        elif MAC:
            log.info('installing LHC CA Certificate')
            cmd = ['sudo', 'security', 'add-trusted-cert', '-d', '-r', 'trustRoot', '-k',
                   '/Library/Keychains/System.keychain', CA_CRT]
            log.info(' '.join(cmd))
            # subprocess.check_call(cmd, shell=True)
            os.system(' '.join(cmd))
            os.system('sudo open ' + CA_CRT)
        else:
            raise SSLError('Unknown operating system, you need to install ca cert by your self. (path: %s)' % CA_CRT)


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
        super(ProxyDocker, self).run()
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
               '-v', '{0}:{0}'.format(CONF_PATH),
               '--dns', self.config.dns_resolver]
        if MAC:
            print('configure port binding ip')
            subprocess.check_call('sudo ifconfig lo0 alias %s/24' % MAC_ALIAS_IP, shell=True)
            # TODO
            portmapping = ['-p', MAC_ALIAS_IP + ':{0}:{0}'.format(self.config.http_port),
                           '-p', MAC_ALIAS_IP + ':{0}:{0}'.format(self.config.https_port)]
        else:
            portmapping = ['-p', '{0}:{0}'.format(self.config.http_port),
                           '-p', '{0}:{0}'.format(self.config.https_port)]
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


if __name__ == '__main__':
    hdlr = logging.StreamHandler()
    hdlr.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
    log.addHandler(hdlr)
    log.setLevel(logging.INFO)
    HOST_CERTS_FILES_PATH = '/tmp/lhc/certs/hosts'
    CA_CERT_FILES_PATH = '/tmp/lhc/certs/ca'
    CA_KEY = os.path.join(CA_CERT_FILES_PATH, 'ca.key')
    CA_CSR = os.path.join(CA_CERT_FILES_PATH, 'ca.csr')
    CA_CRT = os.path.join(CA_CERT_FILES_PATH, 'ca.crt')

    p = Proxy(None)
    # p.gen_ca_certs()
    # print(p.check_ca())
    p.gen_and_sign_certs_for('mirrors.ustc.edu.cn')
    print(p.check_cert(p.get_host_cert_paths('mirrors.ustc.edu.cn')[2]))
    # p.install_ca_cert()
