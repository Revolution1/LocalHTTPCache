import functools
import logging

from consts import DEBUG

log = logging.getLogger('lhc')


class LHCError(Exception):
    pass


class ProxyError(LHCError):
    pass


class ConfigError(LHCError):
    pass


class HOSTSError(LHCError):
    pass


def handle_error(func):
    @functools.wraps(func)
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except LHCError as e:
            if DEBUG:
                log.exception(e)
            else:
                log.error(e)

    return inner
