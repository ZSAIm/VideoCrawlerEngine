import asyncio

from helper.ctxtools.vars.flow import a, c, d, b, f, local, flow, e, flow_mgr
from contextlib import ExitStack

from helper.payload import FlowPayload, gen_linear_flow, Requester
from .base import BaseLayer
from .node import NodeLayer
from typing import List, Tuple, Union, Any, Sequence
from helper.worker import get_worker, executor
from helper.ctxtools import ctx


class ParallelLayer(BaseLayer):
    """ 并行工作流层。
    """
    NAME = 'parallel'

    def __init__(
        self,
        depth: int,
        flows: List[Union[List[FlowPayload], FlowPayload]],
        sema=None,
        is_scriptlayer: bool = False
    ):
        self.depth = depth

        # 可并行的分支流
        self.layers = [_unwrap_parallel_flows(depth, flo, is_scriptlayer) for flo in flows]
        self.sema = sema
        self.is_scriptlayer = is_scriptlayer

        self.point: Tuple = ()

    def __iter__(self):
        return iter(self.layers)

    def __len__(self):
        return len(self.layers)

    def __enter__(self):
        self.setpoint()
        return self

    async def stop(self):
        return await asyncio.wait([layer.stop() for layer in self.layers])

    def setpoint(self):
        """ """
        for index, layer in enumerate(self.layers):
            with ExitStack() as stack:
                # 确定当前深度下的工作流编号
                stack.enter_context(
                    e.apply(index)
                )
                if self.is_scriptlayer:
                    stack.enter_context(
                        b.apply(index)
                    )
                self.point = (a.get(), b.get(), c.get(), self.depth)
                # ctx.glb.task.layers[self.point] = self
                # stack.enter_context(local['layer'].apply(self.point))
                layer.setpoint()

    async def run(self):
        assert self.point

        async def _serial_worker(layer, index):
            try:
                with ExitStack() as stack:
                    if self.is_scriptlayer:
                        stack.enter_context(
                            b.apply(index)
                        )
                    async with sema:
                        # with local['__task__'].apply(tasks[index]):
                        return await layer.run()
            except BaseException as err:
                # 某一条分支发生异常，如果这是头并行层，也就是分支并行层，
                # 进行额外的处理。
                from traceback import print_exc
                print_exc()
                if not self.is_scriptlayer:
                    # 非分支并行层，不对异常做处理
                    raise
                raise

        sema = self.sema
        if not sema:
            sema = asyncio.Semaphore(float('inf'))
        tasks = [
            asyncio.create_task(_serial_worker(layer, i))
            for i, layer in enumerate(self.layers)
        ]
        done, pending = await asyncio.wait(
            tasks,
            # 某一条分支出现错误没必要取消所有的分支
            return_when=(
                asyncio.FIRST_EXCEPTION if not self.is_scriptlayer
                else asyncio.ALL_COMPLETED
            ),
        )

        # TODO: 在这里需要找出是哪一个节点发生的异常。

        # 当某一个节点出现异常的时候，取消所有的任务
        for unfinished_task in pending:
            unfinished_task.cancel()

        if pending:
            # 等待所有的任务停止, 然后抛出任务节点异常
            _, pending = await asyncio.wait(pending)

            done = done.union(_)
        for dn in done:
            try:
                dn.result()
            except Exception as e:
                raise RuntimeError('某一个节点发生异常导致任务停止。') from e

    def __repr__(self):
        return f'<ParallelLayer depth={self.depth}>'


class SerialLayer(BaseLayer):
    """ 串行工作流层
    在串行层中，以所有”节点“处于同一层级。这里面的”节点“包括了以并行层作为整体的节点。
    """
    NAME = 'serial'

    def __init__(
        self,
        depth: int,
        flows: List[FlowPayload],
        is_branchlayer: bool = False
    ):
        self.depth = depth

        # 串行的工作流
        self.layers = [_unwrap_serial_flows(depth, flo) for flo in flows]

        # 任务取消状态
        self._cancelled = False

        self.is_branchlayer = is_branchlayer
        self.point: Tuple = ()

    def __iter__(self):
        return iter(self.layers)

    def __len__(self):
        return len(self.layers)

    def __getitem__(self, item):
        if not isinstance(item, int):
            raise TypeError()
        return self.layers[item]

    def __enter__(self):
        self.setpoint()
        return self

    async def stop(self):
        self._cancelled = True
        return await asyncio.wait([layer.stop() for layer in self.layers])

    async def run(self):
        assert self.point

        for i, layer in enumerate(self.layers):
            if self._cancelled:
                raise PermissionError('任务中止。')
            if self.is_branchlayer:
                # with flow_mgr['enter_layer']()(self.point):
                with ctx.glb.task.enter_layer((a.get(), b.get(), i)):
                    await layer.run()
            else:
                await layer.run()

    def setpoint(self):
        for i, layer in enumerate(self.layers):
            with ExitStack() as stack:
                stack.enter_context(f.apply(i))
            # with e.apply(i):
                self.point = (a.get(), b.get(), self.depth)
                if self.is_branchlayer:
                    # 确定分支主层编号
                    stack.enter_context(c.apply(i))
                layer.setpoint()

    def __repr__(self):
        return f'<SerialLayer depth={self.depth}>'

    def append(self, *payloads):
        """ 追加工作节点。"""
        self.layers.extend([_unwrap_serial_flows(self.depth, pl) for pl in payloads])


def _unwrap_serial_flows(depth: int, flow: FlowPayload, *args, **kwargs):
    """ 打开串行层中的工作流。"""
    if isinstance(flow, (list, tuple)):
        # 串行层的下一层是并行层
        return ParallelLayer(depth + 1, list(flow), *args, **kwargs)
    else:
        return NodeLayer(depth, flow, *args, **kwargs)


def _unwrap_parallel_flows(depth: int, flow: FlowPayload, *args, **kwargs):
    """ 打开并行层中的工作流。"""
    if isinstance(flow, (list, tuple)):
        # 并行层的下一层是串行层
        return SerialLayer(depth, list(flow), *args, **kwargs)
    else:
        #
        return NodeLayer(depth, flow, *args, **kwargs)


class SubFlowLayer(BaseLayer):
    def __init__(
        self,
        parent: Any,
        source_a5g: Tuple[Union[int, Tuple[int]], ...],
        subbranch: int,
        payloads: Union[FlowPayload, Sequence[FlowPayload]],
    ):
        self.parent = parent
        self.source = source_a5g
        self.subbranch = subbranch
        # TODO: rule 从父流程继承下来
        f, s = gen_linear_flow(payloads, 1)
        layer = SerialLayer(0, f)
        self.layer = layer

    def run(self):
        with b.apply(self.subbranch):
            self.setpoint()
            return executor.submit(
                get_worker('subflow'),
                args=(self.layer.run,)
            )

    def append(self, *payloads):
        """ 在串行流尾部追加payload. """
        self.layer.append(*payloads)

    async def stop(self):
        return await self.layer.stop()

    def setpoint(self):
        self.layer.setpoint()

    def __enter__(self):
        self.layer.setpoint()
        return self

    def find_by_name(self, name: str) -> List[Requester]:
        _a, _b, _c, _d, _e, _f, _g = self.source
        branch = self.parent.allnodes[(_a, _b)]
        nodes = branch[(_c, _d, _e, _f)][self.subbranch]
        return [v for v in nodes.values() if v.NAME == name]

    # def get_by_a5g(self, abcdef: Tuple) -> Requester:
    #     _a, _b, _c, _d, _e, _f = abcdef
    #     # return self.allnodes[f'{a}-{b}'][cat_a4f(abcdef)]
    #     return self.allnodes[(_a, _b)][(_c, _d, _e)][tuple(_f)]
