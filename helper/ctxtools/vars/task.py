
from helper.ctxtools.mgr import (
    ContextManager,
    ContextNamespace,
    GlobalContext,
    ObjectMappingContext,
)

task = ContextNamespace('task')
task.contextmanager('key')
task_mgr = task.objectmappingcontext(
    meths='__enter__ __exit__ __call__'
    # meths='__enter__ __exit__'
)