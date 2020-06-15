
from contextlib import contextmanager
from contextvars import ContextVar
from config import get_config, SECTION_WORKER
from functools import partial


def _not_impl():
    raise NotImplementedError


class RequestDebugger(object):
    """ 脚本调试工具 """
    __slots__ = ()

    __set_debug__ = False

    __ctx__ = ContextVar('debugger', default=None)

    def __getattr__(self, item):
        try:
            return self.__ctx__.get()[item]
        except:
            _not_impl()

    @contextmanager
    def run(self, request_task, context=None):
        """
        Context:
            startupinfo:
            root_info:
            flow:
            config:
            name:
            __self__: request_task
        """
        def _get_dbg_context(name, default=None):
            try:
                return getattr(dbg, name, None)
            except NotImplementedError:
                return default

        if context is None:
            context = {}

        context.update(_export_progress(request_task.progress))
        startupinfo = {
            'name': _get_dbg_context('name'),
        }
        context.update({
            'error_handler': request_task.error_handler,
            'name': request_task.name,
            'config': get_config(SECTION_WORKER, request_task.name),
            'startupinfo': startupinfo,
            '__self__': request_task,
        })
        token = self.__ctx__.set(context)
        yield self
        self.__ctx__.reset(token)

    __bases__ = (object,)


# 脚本的调试工具
dbg = RequestDebugger()


def _export_progress(progress):
    exports = {}
    for attr in progress.EXPORT_ATTR:
        exports[f'set_{attr}'] = partial(progress.__setattr__, attr)

    for attr in progress.EXPORT_ATTR:
        exports[f'get_{attr}'] = partial(getattr, progress, attr)

    for meth in progress.EXPORT_METH:
        exports[meth] = getattr(progress, meth)

    return exports

