import os
import re
import subprocess
import sys

import ipaddress


def require_root():
    from consts import DEBUG

    if DEBUG:
        return
    if os.geteuid() != 0:
        sys.exit('need run as root')


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


def mkdirs(path, mode=0777):
    if os.path.exists(path):
        return
    par, this = os.path.split(path)
    if this and not os.path.exists(par):
        mkdirs(par)
    os.mkdir(path, mode)


def find_executable(executable, path=None):
    """Tries to find 'executable' in the directories listed in 'path'.

    A string listing directories separated by 'os.pathsep'; defaults to
    os.environ['PATH'].  Returns the complete filename or None if not found.
    """
    if path is None:
        path = os.environ['PATH']
    paths = path.split(os.pathsep)
    base, ext = os.path.splitext(executable)

    if (sys.platform == 'win32' or os.name == 'os2') and (ext != '.exe'):
        executable = executable + '.exe'

    if not os.path.isfile(executable):
        for p in paths:
            f = os.path.join(p, executable)
            if os.path.isfile(f):
                # the file exists, we have a shot at spawn working
                return f
        return None
    else:
        return executable


class cached_property(object):
    """A property that is only computed once per instance and then replaces
       itself with an ordinary attribute. Deleting the attribute resets the
       property.

       Source: https://github.com/bottlepy/bottle/blob/0.11.5/bottle.py#L175
    """

    def __init__(self, func):
        self.__doc__ = getattr(func, '__doc__')
        self.func = func

    def __get__(self, obj, cls):
        if obj is None:
            # We're being accessed from the class itself, not from an object
            return self
        value = obj.__dict__[self.func.__name__] = self.func(obj)
        return value


def warp_join(d, iterable, n=30, newline='\n'):
    lines = []
    if not iterable:
        return ''
    temp = ''
    for c in iterable:
        if len(temp + c + d) > n:
            lines.append(temp)
            temp = ''
        else:
            temp += c + d
    if temp:
        lines.append(temp)
    return newline.join(lines)[:-len(d)]


def get_dir_size_walk(start_path='.'):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
        for f in dirnames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size


def get_dir_size(start_path='.'):
    path = os.path.abspath(os.path.expanduser(start_path))
    out = subprocess.check_output([find_executable('du'), '-sb', path]).strip()
    return int(out.split()[0])
