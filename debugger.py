

from contextmgr import ContextManager
from contextlib import contextmanager

__scope__ = ContextManager('__scope__')

__debug_mode__ = False
__path__ = None


@contextmanager
def run(context):
    """ 运行"""
    global __scope__
    with __scope__.enter(context):
        yield __scope__


class DebugChain:
    def __init__(self, prename, name):
        """
        Create a new instance.

        Args:
            self: (todo): write your description
            prename: (str): write your description
            name: (str): write your description
        """
        self.__prename__ = prename
        self.__name__ = name

    def __getattr__(self, item):
        """
        Returns the attribute of an object.

        Args:
            self: (todo): write your description
            item: (str): write your description
        """
        prename = [self.__prename__] if self.__prename__ else []
        obj_chain = f'{".".join(prename + [self.__name__, item])}'
        try:
            obj = _lookup_scope(obj_chain)
            return obj
        except (KeyError, LookupError):
            return DebugChain(f'{".".join(prename + [self.__name__])}', item)

    def __repr__(self):
        """
        Return a repr string representation of the __repr__.

        Args:
            self: (todo): write your description
        """
        prename = [self.__prename__] if self.__prename__ else []
        return f'<DebugChain {".".join(prename + [self.__name__])}>'

    def __len__(self):
        """
        Returns the length of the field.

        Args:
            self: (todo): write your description
        """
        return len(__scope__.get())


def __getattr__(name):
    """
    Returns a scope name.

    Args:
        name: (str): write your description
    """
    try:
        return _lookup_scope(name)
    except (KeyError, LookupError):
        return DebugChain('', name)


def _lookup_scope(chain):
    """
    Lookup a scope of the given chain.

    Args:
        chain: (todo): write your description
    """
    return __scope__[chain]


@contextmanager
def run_in_debug_mode(**options):
    """
    Run a debug mode.

    Args:
        options: (dict): write your description
    """
    from worker import init_workers
    from config import load_config
    from flow import TaskStack

    global __debug_mode__
    load_config()
    init_workers()
    __debug_mode__ = True

    task = TaskStack(None)
    yield task

