from typing import Callable

from helper.client import get_client
from . import stack
from .base import BasePayload
from .flow import FlowPayload
from .request import Requester
from typing import Any
from helper.ctxtools import ctx
from helper.worker import get_worker, executor


class FunctionExportPayload(
    BasePayload,
):
    NAME = 'export_func'

    def __init__(
        self,
        callerid: str,
    ):
        self.callerid = callerid

    # def end_request(self) -> Any:
    #     caller = stack.get(self.callerid)
    #     caller()

    def _apply(self, *args, **kwargs):
        cli = get_client('script')
        result = cli.remote_apply(
            funcid=self.callerid,
            args=args,
            kwargs=kwargs
        )
        # 同步上下文
        ctx.upload(**(result['context'] or {}))
        return result['ret']

    # __call__ = apply

    def __call__(self, *args, **kwargs):
        return executor.submit(
            get_worker('remote_apply'),
            args=(self._apply,) + args,
            kwargs=kwargs,
        )


def export_func(
    func: Callable,
) -> FunctionExportPayload:
    funcstack = stack.push(func)
    return FunctionExportPayload(funcstack.key)