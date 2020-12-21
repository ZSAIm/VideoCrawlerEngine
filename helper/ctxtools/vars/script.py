

from helper.ctxtools.mgr import (
    ContextManager,
    ContextNamespace,
    GlobalContext,
    ObjectMappingContext,
)

script = ContextNamespace('script')

script.contextmanager('key', default=None)
script.contextmanager('config')
script.contextmanager('basecnf')
