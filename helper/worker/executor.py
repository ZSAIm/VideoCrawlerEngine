from .pool import get_pool
from .worker import Worker
from typing import Union
from concurrent.futures import Future as threadFuture
from asyncio.futures import Future as asyncFuture
from typing import Any, Dict
from helper.ctxtools.mgr import copy_context_to_dict
import asyncio


def try_async_future(
    future: threadFuture
) -> Union[threadFuture, asyncFuture]:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return future
    else:
        return asyncio.wrap_future(future)


def submit(
    __worker: Worker,
    args: tuple = (),
    kwargs: Dict = None,
    context: Dict = None,
    *,
    force_sync: bool = False,
) -> Union[threadFuture, asyncFuture]:
    if context is None:
        # 如果没有指定context,那么将继承调用者的上下文环境。
        context = copy_context_to_dict(inherit_scope=True)
    kwargs = kwargs or {}
    try:
        loop = asyncio.get_running_loop()
        if force_sync:
            raise RuntimeError('强制使用同步future。')
    except RuntimeError:

        # if worker.async_type:
        # s = _submit
        # else:
        #     s = _asubmit()
        future = _submit(__worker, args, kwargs, context)

    else:
        coro = _asubmit(__worker, args, kwargs, context)
        future = asyncio.create_task(coro)
        # if worker.async_type:
        #     s = _asubmit
        # else:
        #     s = _submit
        # s = _asubmit
        # future = s(worker, *args, **kwargs)
        # if isinstance(future, threadFuture):
        #     future = try_async_future(future)
    # if isinstance(future, threadFuture):
    #     future = try_async_future(future)

    return future


def _submit(
    worker: Worker,
    args: Any,
    kwargs: Any,
    context: dict,
) -> Union[threadFuture, asyncFuture]:
    """非协程下调用submit，返回线程Future。
    使用线程锁。
    """
    pool = get_pool(worker)
    with worker:
        # if worker.async_type:
        #     ep = worker.entrypoint.arun
        # else:
        #     ep = worker.entrypoint.run
        future = pool.submit(
            worker,
            context,
            # ep,
            args,
            kwargs
        )

    return future


async def _asubmit(
    worker: Worker,
    args: Any,
    kwargs: Any,
    context: dict,
) -> Union[threadFuture, asyncFuture]:
    """ 在协程下调用submit，返回异步Future。
    使用异步锁。
    """
    pool = get_pool(worker)

    async with worker:
        # if worker.async_type:
        #     ep = worker.entrypoint.arun
        # else:
        #     ep = worker.entrypoint.run
        future = pool.submit(
            # ep,
            worker,
            context,
            args,
            kwargs,
        )
        if isinstance(future, threadFuture):
            future = asyncio.wrap_future(future)
        result = await future

    return result
    # return future
