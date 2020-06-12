from debugger import dbg


class NodeContext(object):
    __slots__ = ()

    def __init_subclass__(cls, name, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.name = name


class RootInfo(NodeContext, name='root_info'):
    """
    Attributes:
        ...

    Methods:
        def get_data(name: str): -> Any
            返回启动请求的键名为name的信息。

    """
    __slots__ = ('get_data', )

    def __init__(self, wf, abcde):
        self.get_data = wf.root.get_data

    def __getitem__(self, item):
        return self.get_data(item)


class FlowNodeContext(NodeContext, name='flow'):
    """
    Attributes:
        abcde: 工作流节点标号

    Methods:
        def prev(): -> workflow.StageNodes
            返回上一个阶段的请求节点。 等效于 RequestWorkflow.prev_stage(abcde)

        def next(): -> workflow.StageNodes
            返回下一个阶段的请求阶段。 等效于 RequestWorkflow.prev_stage(abcde)

        def find_by_name(name: str): -> workflow.RequestNode
            搜索当前分支b中名称为name的请求节点。
            Returns:
                返回请求名称匹配的请求节点。

        def append_node(request: Request): -> workflow.RequestNode
            将请求添加入当前工作流节点中，以子节点的形式存在于当前节点。
            Returns:
                返回被添加请求的节点。

        def get_node(abcde): -> workflow.RequestNode
            获取节点标号为abcde的请求节点，等效于 RequestWorkflow.get_node(abcde)

    """
    __slots__ = ('abcde', 'prev', 'next', 'find_by_name',
                 'append_node', 'get_node')

    def __init__(self, wf, abcde):
        self.abcde = abcde
        self.prev = lambda: wf.prev_stage(abcde)
        self.next = lambda: wf.next_stage(abcde)
        self.find_by_name = wf.find_by_name
        self.get_node = wf.get_node
        self.append_node = lambda request: self.get_node(dbg.flow.abcde).add_child(request)

    a = property(lambda self: self.abcde[0])
    b = property(lambda self: self.abcde[1])
    c = property(lambda self: self.abcde[2])
    d = property(lambda self: self.abcde[3])
    e = property(lambda self: self.abcde[4:])


def _not_impl(*args, **kwargs):
    raise NotImplementedError


def impl_ctx(context):

    return context
















