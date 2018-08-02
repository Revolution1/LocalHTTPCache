# LocalHTTPCache

Tool that helps you setting up a local proxy to cache static files

## Quick Start


### 1. Install

By git

```
git clone git@github.com:Revolution1/LocalHTTPCache.git
cd LocalHTTPCache
python ./setup.py install
```

By pip

```
pip install https://github.com/Revolution1/LocalHTTPCache/archive/master.zip

or

pip install git+https://github.com/Revolution1/LocalHTTPCache.git
```

### 2. Read Help Message

```
$ lhc
Usage: lhc [OPTIONS] COMMAND [ARGS]...

  LHC (Local HTTP Cache), cache static files to your local machine

Options:
  -h, --help  Show this message and exit.

Commands:
  info        show the running status of LHC
  run         run LHC proxy
  stop        stop LHC proxy
  reload      reload configurations
  ls          list hosts
  set         add a host
  del         delete a host
  activate    activate hosts
  deactivate  activate hosts
  df          show cache file disk usage
  purge       purge cache of a host
  gen-ca      generate self-signed ca certificate
  install-ca  install ca to system's certificate chain
```

### 3. Generate and install CA Cert for HTTPS

```
$ sudo lhc gen-ca
Password:
[INFO] /usr/bin/openssl genrsa -out /etc/lhc/certs/ca/ca.key 2048
Generating RSA private key, 2048 bit long modulus
............................+++
.....+++
e is 65537 (0x10001)
[INFO] /usr/bin/openssl req -new -subj /O=Wakanda/OU=LHC/CN=LHC Self-Signed CA -key /etc/lhc/certs/ca/ca.key -out /etc/lhc/certs/ca/ca.csr
[INFO] /usr/bin/openssl x509 -req -days 3560 -sha256 -extensions v3_ca -signkey /etc/lhc/certs/ca/ca.key -in /etc/lhc/certs/ca/ca.csr -out /etc/lhc/certs/ca/ca.crt
Signature ok
subject=/O=Wakanda/OU=LHC/CN=LHC Self-Signed CA
Getting Private key
[INFO] OK

$ sudo lhc install-ca
[INFO] installing LHC CA Certificate
[INFO] copying cert file to /etc/pki/ca-trust/source/anchors/lhc-ca.crt
[INFO] activating
[INFO] OK
```

### 4. Add a host

```
$ sudo lhc del mirrors.fedoraproject.org
mirrors.fedoraproject.org
[INFO] To take effect, you need to reload proxy and activate hosts
[root@revol-centos74-1 tmp]# lhc set mirrors.ustc.edu.cn -e __PKG__
[INFO] generating cert for mirrors.ustc.edu.cn
[INFO] /usr/bin/openssl genrsa -out /etc/lhc/certs/hosts/mirrors.ustc.edu.cn/mirrors.ustc.edu.cn.key 2048
Generating RSA private key, 2048 bit long modulus
..................................................................................................................+++
..........................+++
e is 65537 (0x10001)
[INFO] /usr/bin/openssl req -new -subj /O=Wakanda/OU=LHC/CN=mirrors.ustc.edu.cn -reqexts SAN -config /tmp/tmpBrkGo5 -key /etc/lhc/certs/hosts/mirrors.ustc.edu.cn/mirrors.ustc.edu.cn.key -out /etc/lhc/certs/hosts/mirrors.ustc.edu.cn/mirrors.ustc.edu.cn.csr
[INFO] /usr/bin/openssl x509 -req -days 3560 -sha256 -CAcreateserial -extfile /tmp/tmpWdMBvn -CA /etc/lhc/certs/ca/ca.crt -CAkey /etc/lhc/certs/ca/ca.key -in /etc/lhc/certs/hosts/mirrors.ustc.edu.cn/mirrors.ustc.edu.cn.csr -out /etc/lhc/certs/hosts/mirrors.ustc.edu.cn/mirrors.ustc.edu.cn.crt
Signature ok
subject=/O=Wakanda/OU=LHC/CN=mirrors.ustc.edu.cn
Getting CA Private Key
[INFO] OK, host config wrote to /etc/lhc/hosts/mirrors.ustc.edu.cn
[INFO] To take effect, you need to reload proxy and activate hosts

$ sudo lhc ls
NAME                 EXTENSIONS    LIMIT    EXPIRE    KEY                     PROXY IP    DNS RESOLVER     CONF PATH
-------------------  ------------  -------  --------  ----------------------  ----------  ---------------  ----------------------------------
mirrors.ustc.edu.cn  __PKG__       10g      3d        $host$uri$is_args$args  172.17.0.2  114.114.114.114  /etc/lhc/hosts/mirrors.ustc.edu.cn
```

### 5. Run the proxy

```
$ sudo lhc run
staring proxy container
/usr/bin/docker run --name lhc-proxy -d --restart always -v /etc/lhc/nginx.conf:/etc/nginx/nginx.conf -v /root/.local/lhc.cache:/root/.local/lhc.cache -v /etc/lhc:/etc/lhc --dns 114.114.114.114 -p 80:80 -p 443:443 daocloud.io/nginx
Unable to find image 'daocloud.io/nginx:latest' locally
latest: Pulling from nginx
be8881be8156: Pull complete
32d9726baeef: Pull complete
87e5e6f71297: Pull complete
Digest: sha256:4ffd9758ea9ea360fd87d0cee7a2d1cf9dba630bb57ca36b3108dcd3708dc189
Status: Downloaded newer image for daocloud.io/nginx:latest
09fd17503def206e4400800cddb1fdaecc10935ba7fcfc4ec832833b2ce76305
OK
```

### 6. Activate hosts

```
$ sudo lhc activate

$ cat /etc/hosts
127.0.0.1   localhost localhost.localdomain localhost4 localhost4.localdomain4
::1         localhost localhost.localdomain localhost6 localhost6.localdomain6

# ---------- BEGIN LHC HOSTS CONTENT ----------
172.17.0.2 mirrors.ustc.edu.cn
# ---------- END LHC HOSTS CONTENT ------------
```

### 7. Read Status
```
$ sudo lhc info -v
Proxy:
    Mode: docker
    Status: Running
    CA Cert: /etc/lhc/certs/ca/ca.crt
    HTTP Port: 80
    HTTPS Port: 443
    SSL: True

Hosts:
    Status: Activated
    Count: 1
    IP: 172.17.0.2
    CachePath: /root/.local/lhc.cache

Defaults:
    Extensions: __WEB__
    CacheSizeLimit: 10g
    CacheExpire: 3d
    CacheKey: $host$uri$is_args$args
    DnsResolver: 114.114.114.114

Consts:
    CONF_PATH: /etc/lhc
    CONF_HOSTS_PATH: /etc/lhc/hosts
    CONF_FILE_PATH: /etc/lhc/lhc.conf
    NGINX_CONF_FILE_PATH: /etc/lhc/nginx.conf
    MAC_ALIAS_IP: 192.168.221.181
    NGINX_DOCKER_IMAGE: daocloud.io/nginx
    PROXY_DOCKER_NAME: lhc-proxy

Built-in extensions:
    __PKG__: deb,rpm,tar,gz,xz,zip,apk,iso
    __PIP__: whl
    __WEB__: bmp,ejs,jpeg,pdf,ps,ttf,class,
             jpg,pict,svg,webp,css,eps,js,
             svgz,woff,csv,gif,mid,png,swf,
             doc,ico,midi,ppt,tif,xls,docx,
             otf,pptx,tiff,xlsx
```

### 8. Enjoy

Check cache usage

```
$ sudo lhc df -h
HOST                 CACHE PATH                                        LIMIT    DISK USAGE
-------------------  ------------------------------------------------  -------  ------------
mirrors.ustc.edu.cn  /root/.local/lhc.cache/cache_mirrors_ustc_edu_cn  10g      6.0 Byte
```

Try get a file

```
$ wget https://mirrors.ustc.edu.cn/centos/7/os/x86_64/Packages/bash-4.2.46-30.el7.x86_64.rpm
--2018-08-02 16:23:52--  https://mirrors.ustc.edu.cn/centos/7/os/x86_64/Packages/bash-4.2.46-30.el7.x86_64.rpm
Resolving mirrors.ustc.edu.cn (mirrors.ustc.edu.cn)... 172.17.0.2
Connecting to mirrors.ustc.edu.cn (mirrors.ustc.edu.cn)|172.17.0.2|:443... connected.
HTTP request sent, awaiting response... 200 OK
Length: 1036536 (1012K) [application/x-redhat-package-manager]
Saving to: 'bash-4.2.46-30.el7.x86_64.rpm.3'

100%[===========================================================================================================================================>] 1,036,536   --.-K/s   in 0.04s

2018-08-02 16:23:53 (23.7 MB/s) - 'bash-4.2.46-30.el7.x86_64.rpm.3' saved [1036536/1036536]
```

See that speed is `23.7 MB/s`

Do it again

```
wget https://mirrors.ustc.edu.cn/centos/7/os/x86_64/Packages/bash-4.2.46-30.el7.x86_64.rpm
--2018-08-02 16:25:33--  https://mirrors.ustc.edu.cn/centos/7/os/x86_64/Packages/bash-4.2.46-30.el7.x86_64.rpm
Resolving mirrors.ustc.edu.cn (mirrors.ustc.edu.cn)... 172.17.0.2
Connecting to mirrors.ustc.edu.cn (mirrors.ustc.edu.cn)|172.17.0.2|:443... connected.
HTTP request sent, awaiting response... 200 OK
Length: 1036536 (1012K) [application/x-redhat-package-manager]
Saving to: 'bash-4.2.46-30.el7.x86_64.rpm.4'

100%[===========================================================================================================================================>] 1,036,536   --.-K/s   in 0.003s

2018-08-02 16:25:33 (323 MB/s) - 'bash-4.2.46-30.el7.x86_64.rpm.4' saved [1036536/1036536]
```

Now the speed is `323 MB/s` !

Check disk usage

```
lhc df -h
HOST                 CACHE PATH                                        LIMIT    DISK USAGE
-------------------  ------------------------------------------------  -------  ------------
mirrors.ustc.edu.cn  /root/.local/lhc.cache/cache_mirrors_ustc_edu_cn  10g      1013.0 KiB
```

### 9. Uninstall

```
# deactivate hosts
sudo lhc deactivate

# stop the proxy
sudo lhc stop

# remove config files
rm -rf /etc/lhc

# remove cache files
rm -rf /root/.local/lhc.cache
```

## Dependencies

* Docker
* OpenSSL

## Support OS

* RHEL/CentOS/Fedora
* Ubuntu/Debian
* OSX
