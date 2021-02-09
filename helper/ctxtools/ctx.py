

from helper.ctxtools.mgr import (
    _InvokeChain,
    _lookup_scope,
    __scope__,
)

__debug_mode__ = False
__path__ = None


def __getattr__(name):
    try:
        return _lookup_scope(name)
    except (KeyError, LookupError):
        return _InvokeChain('', name)


