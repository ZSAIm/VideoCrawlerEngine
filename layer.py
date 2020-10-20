
import asyncio

from contexts import (
    a, b, c, d, e, f, abcde, flow, local, glb
)


class Layer:
    """ """

    def __len__(self):
        raise NotImplementedError

    def __iter__(self):
        raise NotImplementedError

    async def run(self, *args, **kwargs):
        raise NotImplementedError

    async def stop(self):
        raise NotImplementedError

    async def locale(self):
        raise NotImplementedError


class SerialLayer(Layer):
    """ 串行工作流层
    在串行层中，以所有”节点“处于同一层级。这里面的”节点“包括了以并行层作为整体的节点。
    """
    def __init__(self, depth, flows):
        self.depth = depth

        # 串行的工作流
        self.flows = [_unwrap_serial_flows(depth, f) for f in flows]

        # 任务取消状态
        self._cancelled = False

    def __iter__(self):
        return iter(self.flows)

    def __len__(self):
        return len(self.flows)

    def __getitem__(self, item):
        if not isinstance(item, int):
            raise TypeError()
        return self.flows[item]

    async def stop(self):
        self._cancelled = True
        return await asyncio.wait([f.stop() for f in self.flows])

    async def run(self):
        l = None
        try:
            # 在该层中未初始化的情况下，这里 __layer__ 的值是上一层的值
            lastl = flow['__layer__'].get()
        except LookupError:
            lastl = None

        for i, f in enumerate(self.flows):
            if self._cancelled:
                raise PermissionError('任务中止。')
            if len(self.flows) >= i + 1:
                n = None
            else:
                n = self.flows[i+1]
            # a-b-c-d-e
            # a: 全局根脚本编号
            # b: 由跟脚本生成的子脚本的分支编号
            # c: 在分支中的深度编号
            # d: 在该深度中工作流的编号
            # e: 在工作流中节点的编号
            # with c.enter(self.depth), d.enter(index), e.enter(i), \
            # with e.enter(i), \
            #      flow['__layer__'].enter(self), \
            #      flow['last'].enter(l), flow['next'].enter(n), \
            #      flow['last_layer'].enter(lastl):
            with flow['__layer__'].enter(self), \
                 flow['last'].enter(l), flow['next'].enter(n), \
                 flow['last_layer'].enter(lastl):
                await f.run()
            l = f

    async def locale(self):
        for i, f in enumerate(self.flows):
            with e.enter(i):
                await f.locale()

    def __repr__(self):
        return f'<SerialLayer depth={self.depth}>'


class ParallelLayer(Layer):
    """ 并行工作流层。
    """
    def __init__(self, depth, flows, sema=None):
        self.depth = depth

        # 可并行的分支流
        self.flows = [_unwrap_parallel_flows(depth, f) for f in flows]
        self.sema = sema

    def __iter__(self):
        return iter(self.flows)

    def __len__(self):
        return len(self.flows)

    async def stop(self):
        return await asyncio.wait([f.stop() for f in self.flows])

    async def locale(self, mark_branch_index=False):
        """ """
        async def _serial_locale(f, index):
            with d.enter(index):
                if mark_branch_index:
                    with b.enter(index):
                        return await f.locale()
                else:
                    return await f.locale()

        await asyncio.wait(
            [_serial_locale(f, i) for i, f in enumerate(self.flows)]
        )

    async def run(self):
        async def _serial_worker(f, index):
            # with c.enter(self.depth), d.enter(index), local['__task__'].enter(tasks[index]):
            async with sema:
                with local['__task__'].enter(tasks[index]):
                    return await f.run()
        sema = self.sema
        if not sema:
            sema = asyncio.Semaphore(float('inf'))
        tasks = [asyncio.create_task(_serial_worker(f, i)) for i, f in enumerate(self.flows)]
        done, pending = await asyncio.wait(
            tasks,
            return_when=asyncio.FIRST_EXCEPTION
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


def _unwrap_serial_flows(depth, flow):
    """ 打开串行层中的工作流。"""
    if isinstance(flow, (list, tuple)):
        # 串行层的下一层是并行层
        return ParallelLayer(depth + 1, list(flow))
    else:
        return WorkLayer(depth, flow)


def _unwrap_parallel_flows(depth, flow):
    """ 打开并行层中的工作流。"""
    if isinstance(flow, (list, tuple)):
        # 并行层的下一层是串行层
        return SerialLayer(depth, list(flow))
    else:
        #
        return WorkLayer(depth, flow)


class WorkLayer(Layer):
    """ 工作层。"""
    def __init__(self, depth, work):
        self.depth = depth

        self.work = work

    def __len__(self):
        return 1

    def __iter__(self):
        return iter([self.work])

    async def locale(self):
        with c.enter(self.depth):
            self.work.__locale__ = (a(), b(), c(), d(), e())
            glb['task']().add_work(self.work)

    async def run(self):
        _a, _b, _c, _d, _e = self.work.__locale__
        with a.enter(_a), b.enter(_b), c.enter(_c), d.enter(_d), e.enter(_e), f.enter(0), \
             abcde.enter(self.work.__locale__), local['request'].enter(self.work), \
             glb['task']():
            return await self.work.start_request()

    async def stop(self):
        await self.work.stop()

    def __repr__(self):
        return f'<WorkLayer depth={self.depth}>'


