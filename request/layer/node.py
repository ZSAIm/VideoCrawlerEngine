from .base import BaseLayer
from typing import Tuple
from helper.ctxtools.vars.flow import (
    c, a, b, d, e, f, g, glb, a5g, local, flow
)
from helper.ctxtools import ctx
from helper.ctxtools.mgr import get_ctx
from contextlib import ExitStack


class NodeLayer(BaseLayer):
    """ 工作层。"""
    def __init__(self, depth, node, *args, **kwargs):
        self.depth = depth

        self.node = node
        self.point: Tuple = ()

    def __len__(self):
        return 1

    def __iter__(self):
        return iter([self.node])

    def setpoint(self):
        # 确定执行层深度
        with d.apply(self.depth):
            try:
                get_ctx(ctx.glb.script)
                # abcde以当前工作节点为父节点
                point = (
                    ctx.a,
                    ctx.b,
                    ctx.c,
                    ctx.d,
                    ctx.e,
                    ctx.f,
                    (b.get(), c.get(), d.get(), e.get(), f.get())
                )
            except LookupError:
                point = (
                    a.get(),
                    b.get(),
                    c.get(),
                    d.get(),
                    e.get(),
                    f.get(),
                    g.get(),
                )

            self.node.__point__ = point
            # self.point = tuple(point[:3])
            self.point = point
            # 添加到当前执行主层
            # layer.append(point)
            ctx.flow.mount_node(self.node)

    async def run(self):
        assert self.point

        _a, _b, _c, _d, _e, _f, _g = _a5g = self.node.__point__
        ctxmgr_value = {
            a: _a,
            b: _b,
            c: _c,
            d: _d,
            e: _e,
            f: _f,
            g: _g,
            a5g: _a5g,
            local['request']: self.node,
        }
        # try:
        with ExitStack() as ctx_stack:
            for ctxmgr, value in ctxmgr_value.items():
                ctx_stack.enter_context(ctxmgr.apply(value))
            with ctx.flow.enter_node():
                return await self.node.start_request()
        # except Exception:
        #     from traceback import print_exc
        #     print_exc()
        #     print_exc()
        #     raise

    async def stop(self):
        await self.node.stop()

    def __repr__(self):
        return f'<WorkLayer depth={self.depth}>'
