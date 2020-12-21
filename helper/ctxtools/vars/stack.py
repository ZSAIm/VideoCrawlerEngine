

from helper.ctxtools.mgr import (
    ContextManager,
    ContextNamespace,
    GlobalContext,
    ObjectMappingContext,
)

# 栈命名空间
stack = ContextNamespace('stack')

stack.contextmanager('task')
