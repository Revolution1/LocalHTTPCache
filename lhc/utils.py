import os
import re
import sys

import ipaddress


def require_root():
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
