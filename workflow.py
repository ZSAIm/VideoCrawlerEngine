from context import NodeContext
from debugger import dbg
from _request import (Request, Option, Optional, RootRequest,
                      _all_status, REQ_QUEUING, REQ_ERROR)
from utils import concat_abcde
from traceback import format_exc
from threading import Thread
import asyncio


class WorkflowStoppedError(Exception):
    pass


class BaseNode:
    __slots__ = ('abcde', )

    a = property(lambda self: self.abcde[0])
    b = property(lambda self: self.abcde[1])
    c = property(lambda self: self.abcde[2])
    d = property(lambda self: self.abcde[3])
    e = property(lambda self: self.abcde[4:])

    def __eq__(self, other):
        return other.abcde == self.abcde

    __hash__ = object.__hash__


class RequestNode(BaseNode):
    __slots__ = 'abcde', 'cont', 'children'

    def __init__(self, abcde, request):
        """
        Args:
            abcde:
                a: script id
                b: branches id
                c: stage id
                d: request/s id
                *e: sub request
            request: request object
        """
        self.abcde = abcde
        self.cont = request
        self.children = []

    @property
    def name(self):
        return self.cont.name

    def start_request(self, context=None):
        async def _async_run():
            nonlocal context
            if context is None:
                context = {}
            if self.children:
                await asyncio.wait([child.start_request(dict(context))
                                    for child in self.children])

            return await self.cont.start_request(context)
        return _async_run()

    def sketch(self):
        sketch = self.cont.sketch()
        sketch.update({
            'abcde': concat_abcde(self.abcde),
        })
        return sketch

    def percent(self):
        all_percent = sum([n.percent() * n.cont.WEIGHT for n in self.children] +
                         [self.cont.WEIGHT * self.cont.progress.percent])
        all_weight = sum([n.cont.WEIGHT for n in self.children] + [self.cont.WEIGHT])
        if not all_weight:
            return 0
        return all_percent / all_weight

    def timeleft(self):
        return sum([n.timeleft() for n in self.children] + [self.cont.progress.timeleft])

    def status(self):
        return self.cont.progress.status

    def get_data(self, name, default=None):
        return self.cont.get_data(name, default)

    def stop(self):
        for node in self.children:
            node.stop()
        self.cont.stop()

    def getresponse(self):
        return self.cont.getresponse()

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
        node = RequestNode(abcde, request)
        self.children.append(node)
        return node


class BranchFlow(BaseNode):
    def __init__(self, parent, abcde, nodes):
        self.parent = parent
        self.abcde = abcde
        self.nodes = nodes
        self.running = set()
        self._stopped = False

    async def run(self):
        """ 执行工作流分支。
        Args:
        """

        async def _serial_worker(work):
            """ 串行工作。
            Args:
                work: 执行工作流节点/阶段。
            """
            nonlocal wf
            if type(work) not in (list, tuple):
                work = [work]
            for node in work:
                if self._stopped:
                    raise WorkflowStoppedError(wf)
                if type(work) in (list, tuple) and len(node) > 1:
                    await _parallel_worker(node)
                else:
                    self.running.add(node)
                    try:
                        await node.start_request(
                            wf.get_context(node.abcde))
                    except BaseException:
                        dbg.warning(format_exc())
                        raise
                    else:
                        dbg.success(
                            f'Node Finished: \n'
                            f'abcde={concat_abcde(node.abcde)}\n'
                            f'name={node.name}\n')
                    finally:
                        self.running.remove(node)

        async def _parallel_worker(work):
            """ 并行工作。
            Args:
                work: 执行工作流节点/阶段
            """
            done, pending = await asyncio.wait(
                [_serial_worker(w) for w in work],
                return_when=asyncio.FIRST_EXCEPTION)
            # 取消工作流任务
            for unfinished_task in pending:
                unfinished_task.cancel()

            if pending:
                # 等待取消工作完成
                done, pending = await asyncio.wait(pending)
                raise RuntimeError()

        wf = self.parent
        for step in self:
            try:
                await _parallel_worker(step)
            except RuntimeError:
                break

    def sketch(self):
        nodes = list(self.every())
        timeleft = sum([node.timeleft() for node in nodes]) / len(nodes)
        return {
            'abcde': concat_abcde(self.abcde),
            'percent': self.percent(),
            'status': _all_status(nodes),
            'timeleft': timeleft,
            'running': [concat_abcde(node.abcde) for node in self.running],
            'n': len(nodes),
            'all': [node.sketch() for node in nodes]
        }

    def timeleft(self):
        nodes = list(self.every())
        return sum([node.timeleft() for node in nodes]) / len(nodes)

    def percent(self):
        nodes = list(self.every())
        all_percent = sum([n.percent() * n.cont.WEIGHT for n in nodes])
        all_weight = sum([n.cont.WEIGHT for n in nodes])
        if not all_weight:
            return 0
        return round(all_percent / all_weight, 2)

    def status(self):
        return _all_status(list(self.every()))

    def stop(self):
        self._stopped = True
        for node in self.every():
            node.stop()

    def every(self):
        for stage in self:
            for node in stage:
                yield node

    def __iter__(self):
        return iter(self.nodes)

    def __len__(self):
        return len(self.nodes)


class Stage(BaseNode):
    __slots__ = 'abcde', 'nodes', 'prev', 'next'

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


class BaseWorkflow:
    __slots__ = ()

    @staticmethod
    def __len__():
        return 0

    @staticmethod
    def __iter__():
        return iter([])

    @staticmethod
    def timeleft():
        return float('inf')

    @staticmethod
    def percent():
        return 0

    @staticmethod
    def status():
        return REQ_QUEUING

    def sketch(self):
        return {
            'abcde': '',
            'percent': self.percent(),
            'branches': [],
            'status': self.status(),
            'timeleft': self.timeleft(),
            'n': 0
        }

    def stop(self):
        pass

    def __repr__(self):
        return f'<{self.__class__.__name__}>'


class PendingWorkflow(BaseWorkflow):
    @staticmethod
    def status():
        return REQ_QUEUING


class BrokenWorkflow(BaseWorkflow):
    @staticmethod
    def status():
        return REQ_ERROR


class Workflow(BaseWorkflow):
    def __init__(self, a, root, flow):
        self.root = root
        self.id = a
        branches = []

        for b, branch in enumerate(flow):
            _branches = []
            for c, stage in enumerate(branch):
                if not isinstance(stage, (list, tuple)):
                    stage = [stage]
                _branches.append([RequestNode(
                    (a, b, c, d, ()), rq
                ) for d, rq in enumerate(stage)])

            branches.append(BranchFlow(self, (a, b, None, None, ()), _branches))

        self.branches = branches

    def __len__(self):
        return len(self.branches)

    def __iter__(self):
        for branch in self.branches:
            yield branch

    def sketch(self):
        return {
            'abcde': concat_abcde((self.id, None, None, None, ())),
            'percent': self.percent(),
            'branches': [branch.sketch() for branch in self.branches],
            'status': self.status(),
            'timeleft': self.timeleft(),
            'n': len(self.branches),
            'url': self.root.get_data('url')
        }

    def timeleft(self):
        return sum([branch.timeleft() for branch in self.branches])

    def percent(self):
        percents = [branch.percent() for branch in self.branches]
        if not percents:
            return 0
        return sum(percents) / len(percents)

    def status(self):
        return _all_status(self.branches)

    def stop(self):
        for branch in self.branches:
            Thread(target=branch.stop, name=f'BranchStopper-{self.id}:').start()

    def get_node(self, abcde):
        a, b, c, d, e = abcde
        assert a == self.id

        return_node = self.branches[b][c][d]
        for _ in e:
            return_node = return_node[_]
        return return_node

    def get_context(self, abcde):
        subclasses = NodeContext.__subclasses__()
        return {context_factor.name: context_factor(self, abcde)
                for context_factor in subclasses}

    def find_by_name(self, name):
        a, b, c, d, e = dbg.flow.abcde

        assert a == self.id
        nodes = []
        for stage in self.branches[b]:
            nodes.extend([node for node in stage if node.name == name])
        return nodes

    def prev_stage(self, abcde):
        a, b, c, d, e = abcde
        assert self.id == a
        if c == 0:
            return None
        c -= 1
        stage_nodes = self.branches[b][c]

        return Stage(
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
            stage_nodes = self.branches[b][c]
        except IndexError:
            return None

        return Stage(
            (a, b, c, None, ()),
            stage_nodes,
            prev=lambda: self.prev_stage((a, b, c, None, ())),
            next=lambda: self.next_stage((a, b, c, None, ()))
        )

    def each_branch(self):
        return iter(self.branches)

    def every(self):
        def _every(o):
            nonlocal all_node
            if isinstance(o, (list, tuple, set)):
                _ = {_every(i) for i in o}
            else:
                all_node.append(o)
        all_node = []
        _every(self.branches)
        return all_node

    def __repr__(self):
        return f'<{self.__class__.__name__} {len(self.branches)}: a={self.id} status={self.status()}>'


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


async def run_workflow(workflow, semaphore=None):
    """ 运行工作流。
    Args:
        workflow:
        semaphore:

    """
    async def _branch_worker(branch):
        async with semaphore:
            await branch.run()

    if semaphore is None:
        semaphore = asyncio.Semaphore(float('inf'))
    return await asyncio.wait([_branch_worker(branch) for branch in workflow])

















