# LocalHTTPCache

Tool that helps you setting up a local proxy to cache static files

## Install

By git

```
git clone git@github.com:Revolution1/LocalHTTPCache.git
cd LocalHTTPCache
python ./setup.py install
```

By pip

```
pip install git+https://github.com/Revolution1/LocalHTTPCache.git
```

## Usage

```
$ lhc -h

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
```
