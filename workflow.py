from context import RootInfo, FlowNodeContext
from debugger import dbg
from weakref import proxy
from debugger import dbg
from _request import Request, Option, Optional, get_requester, RootRequest
import asyncio


class Node:
    __slots__ = ('abcde', )

    a = property(lambda self: self.abcde[0])
    b = property(lambda self: self.abcde[1])
    c = property(lambda self: self.abcde[2])
    d = property(lambda self: self.abcde[3])
    e = property(lambda self: self.abcde[4:])

    def __eq__(self, other):
        return other.abcde == self.abcde


class RequestNode(Node):
    __slots__ = 'parent', 'abcde', 'request', 'children'

    def __init__(self, parent, abcde, request):
        """
        Args:
            abcde:
                a: script id
                b: branch id
                c: stage id
                d: request/s id
                *e: sub request
            request: request object
        """
        self.abcde = abcde
        self.parent = parent
        self.request = request
        self.children = []

    @property
    def name(self):
        return self.request.name

    def start_request(self, context=None):
        async def _async_run():
            nonlocal context
            if context is None:
                context = {}

            ctx = self.parent.get_context(self.abcde)
            ctx.update(context)

            if self.children:
                await asyncio.wait([child.start_request(ctx)
                                    for child in self.children])
            return await self.request.start_request(ctx)
        return _async_run()

    def get_data(self, name, default=None):
        return self.request.get_data(name, default)

    def getresponse(self):
        return self.request.getresponse()

    def is_active(self):
        return self.request.is_active()

    def __len__(self):
        return len(self.children)

    def __iter__(self):
        return iter(self.children)

    def __repr__(self):
        return f'<RequestNode: {len(self)}, abcde={self.abcde} request="{self.name}">'

    def __getitem__(self, item):
        assert isinstance(item, int)
        return self.children[item]

    def __contains__(self, item):
        return item in self.children

    def add_child(self, request):
        a, b, c, d, e = self.abcde
        e = list(e)
        e.append(len(self.children))
        abcde = (a, b, c, d, tuple(e))
        node = RequestNode(self.parent, abcde, request)
        self.children.append(node)
        return node


class StageNodes(Node):
    def __init__(self, abcde, nodes, prev, next):
        self.nodes = nodes
        self.abcde = abcde
        self.prev = prev
        self.next = next

    def __getitem__(self, d):
        assert isinstance(d, int)

        *_, e = self.abcde

        return_node = self.nodes[d]
        for i in e:
            return_node = return_node[i]
        return return_node

    def __iter__(self):
        return iter(self.nodes)

    def __len__(self):
        return len(self.nodes)

    def __repr__(self):
        return f'<StageNode: {len(self)} - {self.abcde}>'


class RequestWorkflow:
    def __init__(self, a, root, flow):
        self.root = root
        self.id = a
        nodes = []

        for b, branch in enumerate(flow):
            _branch = []
            for c, stage in enumerate(branch):
                if not isinstance(stage, (list, tuple)):
                    stage = [stage]
                _branch.append([RequestNode(
                    proxy(self), (a, b, c, d, ()), rq
                ) for d, rq in enumerate(stage)])
            nodes.append(_branch)

        self.nodes = nodes

    def __len__(self):
        return len(self.nodes)

    def __iter__(self):
        for b in range(len(self)):
            yield list(self.step_by_step(b))

    def step_by_step(self, b):
        for stage in self.nodes[b]:
            yield stage

    def get_node(self, abcde):
        a, b, c, d, e = abcde
        assert a == self.id

        return_node = self.nodes[b][c][d]
        for _ in e:
            return_node = return_node[_]
        return return_node

    def get_context(self, abcde):
        return {
            'root_info': RootInfo(get_data=self.root.get_data),
            'flow': FlowNodeContext(
                abcde=abcde,
                prev=lambda: self.prev_stage(abcde),
                next=lambda: self.next_stage(abcde),

                find_by_name=self.find_by_name,
                append_node=self.__append_node,
                get_node=self.get_node,

            ),
        }

    def __append_node(self, request):
        rq_node = self.get_node(dbg.flow.abcde)
        return rq_node.add_child(request)

    def find_by_name(self, name):
        a, b, c, d, e = dbg.flow.abcde

        assert a == self.id
        requests = []
        for stage in self.nodes[b]:
            requests.extend([node for node in stage if node.name == name])
        return requests

    def prev_stage(self, abcde):
        a, b, c, d, e = abcde
        assert self.id == a
        if c == 0:
            return None
        c -= 1
        stage_nodes = self.nodes[b][c]

        return StageNodes(
            (a, b, c, None, ()),
            stage_nodes,
            prev=lambda: self.prev_stage((a, b, c, None, ())),
            next=lambda: self.next_stage((a, b, c, None, ()))
        )

    def next_stage(self, abcde):
        a, b, c, d, e = abcde
        assert self.id == a
        c += 1
        try:
            stage_nodes = self.nodes[b][c]
        except IndexError:
            return None

        return StageNodes(
            (a, b, c, None, ()),
            stage_nodes,
            prev=lambda: self.prev_stage((a, b, c, None, ())),
            next=lambda: self.next_stage((a, b, c, None, ()))
        )

    def every(self):
        def _every(o):
            nonlocal all_node
            if isinstance(o, (list, tuple, set)):
                _ = {_every(i) for i in o}
            else:
                all_node.append(o)
        all_node = []
        _every(self.nodes)
        return all_node


def factor_request(request,
                   rule,
                   desc_saver=None):
    """ 分解请求工作链。
    Args:
        request: 被分解的请求
        rule: 请求选择规则
        desc_saver: 选项描述信息将更新到desc_saver指定的字典。若不指定则忽略描述信息。
    """
    def _select(o):
        """ 处理选择请求的关系链。"""
        if isinstance(o, Request):
            return o
        elif isinstance(o, Option):
            dbg.success(f'[x] - <{o.content.name}> '
                        f'SELECT: {o.descriptions}')
            desc_saver.update(o.descriptions)
            return _select(o.content)
        elif isinstance(o, Optional):
            return _select(o.select(rule))

        raise RuntimeError()

    def _lookup(o):
        """ 建立工作流串并行链。"""
        o = _select(o)
        if isinstance(o, RootRequest):
            srp.append(o)
            return None

        s = []
        for req in o.subrequest():
            r = _lookup(req)
            if r is None:
                return None
            s.extend(r)

        if s:
            return [s, o]
        return [o]

    if desc_saver is None:
        desc_saver = {}
    srp = []
    flow = _lookup(request)
    return flow, srp or None


async def run_branch(branch_flow):
    """ 执行工作流分支。
    Args:
        branch_flow: 工作流RequestWorkflow对象
    """

    async def _serial_worker(work):
        """ 串行工作。
        Args:
            work: 执行工作流节点/阶段。
        """
        if type(work) not in (list, tuple):
            work = [work]
        for node in work:
            if type(work) in (list, tuple) and len(node) > 1:
                await _parallel_worker(node)
            else:
                await node.start_request()

    async def _parallel_worker(work):
        """ 并行工作。
        Args:
            work: 执行工作流节点/阶段
        """
        done, pending = await asyncio.wait(
            [_serial_worker(w) for w in work], return_when=asyncio.FIRST_EXCEPTION)

        # 取消工作流任务
        for unfinished_task in pending:
            unfinished_task.cancel()

        if pending:
            # 等待取消工作完成
            done, pending = await asyncio.wait(pending)

    for step in branch_flow:
        await _parallel_worker(step)


async def run_workflow(workflow, semaphore=None):
    """ 运行工作流。
    Args:
        workflow:
        semaphore:

    """
    async def _branch_worker(branch):
        async with semaphore:
            await run_branch(branch)

    if semaphore is None:
        # 无限制的并发
        semaphore = asyncio.Semaphore(float('inf'))
    return await asyncio.wait([_branch_worker(branch) for branch in workflow])
