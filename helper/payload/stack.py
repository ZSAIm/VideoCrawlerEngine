from binascii import crc32
from typing import Any
from collections import defaultdict
from functools import partial
from helper.ctxtools import ctx
from helper.ctxtools.mgr import get_ctx
from datetime import datetime


_STACK_OBJECT_POOL = defaultdict(dict)


class TaskStack(object):
    def __init__(self, obj):
        self.obj = obj
        self.last_active = datetime.now()
        self.miss_num = 0

    @property
    def key(self):
        return f'{id(self.obj):x}'

    def __call__(self, *args, **kwargs):
        return self.obj(*args, **kwargs)

    def hit(self):
        self.miss_num = 0
        self.last_active = datetime.now()

    def miss(self):
        pass


def push(obj: Any) -> TaskStack:
    stack = TaskStack(obj)
    _s = _STACK_OBJECT_POOL.get(stack.key)
    if _s:
        return _s
    key = get_ctx(ctx.script.key)
    _STACK_OBJECT_POOL[key][stack.key] = stack
    return stack


def get(funcid: str) -> TaskStack:
    key = get_ctx(ctx.script.key)
    return _STACK_OBJECT_POOL[key][funcid]


def pop(sign: str) -> None:
    del _STACK_OBJECT_POOL[sign]


def hit(keys):
    pass



