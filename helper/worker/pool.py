import asyncio
import sys
import threading
from asyncio.base_events import BaseEventLoop
from asyncio.futures import Future as asyncFuture
from asyncio.runners import _cancel_all_tasks as cancel_all_tasks
from concurrent.futures import Future as threadFuture
from concurrent.futures.thread import ThreadPoolExecutor as _ThreadPoolExecutor
from inspect import iscoroutine
from typing import Any, Callable, Dict, Union
from helper.worker import Worker


class ThreadPoolExecutor(object):
    def __init__(self, *args: Any, **kwargs: Any):
        self.executor = _ThreadPoolExecutor(*args, **kwargs)
        self.semaphore = threading.Semaphore(self.executor._max_workers)
        self._lock = threading.Lock()

    def wait_ready(self):
        pass

    def submit(
        self,
        fn: Callable,
        context: Dict = None,
        args: tuple = (),
        kwargs: dict = None,
    ) -> threadFuture:
        def cb(fut):
            # 任务完成，释放线程（非真正意义上的释放）
            self.semaphore.release()

        kwargs = kwargs or {}
        context = context or {}
        with self._lock:
            # TODO: 以合理的方式控制线程数，避免空闲线程数过多造成IO负担。

            # 如果线程使用已经高于池子的最大承受力，新增线程
            while not self.semaphore.acquire(False):
                self.executor._max_workers += 1
                self.semaphore.release()

            future = self.executor.submit(
                fn,
                context,
                *args,
                **kwargs
            )

        # 任务完成回调
        future.add_done_callback(cb)
        return future

    def shutdown(self, wait=True):
        self.executor.shutdown(wait)


class AsyncPoolExecutor(object):
    def __init__(self, *args: Any, **kwargs: Any):
        self.loop: BaseEventLoop
        self.executor = ThreadPoolExecutor(max_workers=1)
        # 初始化协程事件循环
        self.executor.submit(self._forever_async_event_loop)
        self._ready_event = threading.Event()
        self._close_event = threading.Event()

    def wait_ready(self):
        return self._ready_event.wait()

    def _forever_async_event_loop(self, context=None) -> None:
        """ 维持一个异步协程事件循环。"""
        if sys.platform == 'win32':
            loop = asyncio.ProactorEventLoop()
        else:
            loop = asyncio.get_event_loop()

        asyncio.set_event_loop(loop)
        self.loop = loop
        self._ready_event.set()
        try:
            loop.run_forever()
        finally:
            try:
                cancel_all_tasks(loop)
                loop.run_until_complete(loop.shutdown_asyncgens())
            finally:
                loop.close()

        self._close_event.set()

    def submit(
        self,
        fn: Callable,
        context: Dict = None,
        args: tuple = (),
        kwargs: dict = None
    ) -> Union[threadFuture, asyncFuture]:
        kwargs = kwargs or {}
        context = context or {}
        coro = fn(context, *args, **kwargs)
        assert iscoroutine(coro)
        return asyncio.run_coroutine_threadsafe(
            coro, self.loop
        )

    def shutdown(self, wait=True):
        loop = self.loop
        loop.call_soon_threadsafe(loop.stop)
        # 等待事件循环关闭
        self._close_event.wait()
        self.loop.close()
        self.executor.shutdown(wait)


_COMMON_THREAD_POOL = 0
_COMMON_ASYNC_POOL = 1
_POOL = {
    _COMMON_THREAD_POOL: ThreadPoolExecutor(max_workers=1),
    _COMMON_ASYNC_POOL: AsyncPoolExecutor(max_workers=1),
}


def get_pool(
    worker: Worker
) -> Union[ThreadPoolExecutor, AsyncPoolExecutor]:
    """ 获取工作池。 """
    if worker.independent:
        # 独占线程
        pool = _POOL.get(id(worker))
        if not pool:
            if worker.async_type:
                pool_cls = AsyncPoolExecutor
            else:
                pool_cls = ThreadPoolExecutor
            pool = pool_cls(max_workers=1)
            pool.wait_ready()
    else:
        # 获取异步或线程公共池
        if worker.async_type:
            pool = _POOL[_COMMON_ASYNC_POOL]
        else:
            pool = _POOL[_COMMON_THREAD_POOL]
    return pool


def shutdown(wait=True):
    for name, pool in _POOL.items():
        pool.shutdown(wait)
