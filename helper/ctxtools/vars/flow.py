

from helper.ctxtools.mgr import ContextManager, ContextNamespace

# 主编号
a = ContextManager('a')

# 分支号
b = ContextManager('b')

# 分支层索引
c = ContextManager('c', default=-1)

# 执行层所在深度
d = ContextManager('d')

# 主层下并行流索引
e = ContextManager('e')

# 节点编号
f = ContextManager('f')

# 子流程编号，父流程为()
g = ContextManager('g', default=(0,))


a5g = ContextManager('a5g')
# a5g = abcdef

tempdir = ContextManager('tempdir')

# local
local = ContextNamespace('local', )
local.contextmanager('__task__')
local.contextmanager('request')
local.contextmanager('__layer__')
local.contextmanager('layer')
# global 全局属性
glb = ContextNamespace('glb')
glb.globalcontext('config')
glb.contextmanager('script')
glb.contextmanager('info')
glb.contextmanager('task')
glb.contextmanager('worker')
glb.contextmanager('base')
# ctx.local.script

# glb.contextmanager('test')

# flow
# flow = ContextManager('flow')
flow = ContextNamespace('flow')
flow_mgr = flow.objectmappingcontext(
    attr='branch key',
    meths="""
    run_async add get_by_a5g get_subflow
    find_by_name iternodes enter_node enter_layer
    
    """,
)
flow.contextmanager('__layer__')
flow.contextmanager('next')
flow.contextmanager('last')

flow.contextmanager('next_layer')
flow.contextmanager('last_layer')

#
