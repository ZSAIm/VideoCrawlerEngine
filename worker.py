from concurrent.futures.thread import ThreadPoolExecutor
from config import get_config, SECTION_WORKER
from entrypoint import get_entrypoint
from uitls import cancel_all_tasks
from contexts import glb
import threading
import asyncio
import sys

# 工作者平台
REGISTERED_WORKER = {}

WORKER_ENTRYPOINT = {}


class Workers:
    __type__ = None

    def __init__(self, name, max_workers, entrypoint=None, *args, **kwargs):
        """
        Initialize workers.

        Args:
            self: (todo): write your description
            name: (str): write your description
            max_workers: (int): write your description
            entrypoint: (str): write your description
        """
        self.name = name
        self.max_workers = max_workers
        self.entrypoint = entrypoint

    def submit(self):
        """
        Submit a request.

        Args:
            self: (todo): write your description
        """
        raise NotImplementedError

    def run(self):
        """
        Run the result of the specified arguments.

        Args:
            self: (todo): write your description
        """
        raise NotImplementedError

    def shutdown(self, wait=True):
        """
        Shutdown the connection. shutdown.

        Args:
            self: (todo): write your description
            wait: (bool): write your description
        """
        pass


class NullWorkers(Workers):
    __type__ = 'null'

    def submit(self, *args, **kwargs):
        """
        Submit a job.

        Args:
            self: (todo): write your description
        """
        return self.run(*args, **kwargs)

    def run(self, *args, **kwargs):
        """
        Run the entry point.

        Args:
            self: (todo): write your description
        """
        with glb['worker'].enter(self):
            return get_entrypoint(self.entrypoint, False)(*args, **kwargs)

    def shutdown(self, wait=True):
        """
        Shutdown the connection. shutdown.

        Args:
            self: (todo): write your description
            wait: (bool): write your description
        """
        pass


class AsyncNullWorkers(Workers):
    __type__ = 'null async'

    @property
    def loop(self):
        """
        The async loop.

        Args:
            self: (todo): write your description
        """
        return asyncio.get_running_loop()

    def submit(self, *args, **kwargs):
        """
        Submit a job.

        Args:
            self: (todo): write your description
        """
        return self.run(*args, **kwargs)

    def run(self, *args, **kwargs):
        """
        Run entry point.

        Args:
            self: (todo): write your description
        """
        with glb['worker'].enter(self):
            return get_entrypoint(self.entrypoint, True)(*args, **kwargs)

    def shutdown(self, wait=True):
        """
        Shutdown the connection. shutdown.

        Args:
            self: (todo): write your description
            wait: (bool): write your description
        """
        pass


# class MixedWorkers(Workers):
#     __type__ = 'mixed'
#
#     def __init__(self, name, max_workers, entrypoint=None):
#         super(MixedWorkers, self).__init__(name, max_workers, entrypoint)
#         self.async_workers = AsyncWorkers(name, max_workers, entrypoint)
#         self.thread_workers = ThreadWorkers(name, max_workers, entrypoint)
#
#     def submit(self, *args, **kwargs):
#         return self.run(*args, **kwargs)
#
#     def run(self, *args, **kwargs):
#         """ """
#
#     def shutdown(self, wait=True):
#         pass


def try_async_future(future):
    """ 尝试将线程concurrent.futures.Future封装成异步asyncio.futures.Future。"""
    try:
        loop = asyncio.get_running_loop()
        return asyncio.wrap_future(future, loop=loop)
    except RuntimeError:
        return future


class ThreadWorkers(Workers):
    """ 工作线程"""
    __type__ = 'thread'

    def __init__(self, name, max_workers, entrypoint=None, *, initializer=None, initargs=()):
        """
        Initialize workers.

        Args:
            self: (todo): write your description
            name: (str): write your description
            max_workers: (int): write your description
            entrypoint: (str): write your description
            initializer: (todo): write your description
            initargs: (todo): write your description
        """
        Workers.__init__(self, name, max_workers, entrypoint)
        self.workers = ThreadPoolExecutor(
            max_workers, thread_name_prefix=name,
            initializer=initializer, initargs=initargs)

    def submit(self, *args, **kwargs):
        """ 提交工作任务。"""
        # try:
        #     loop = asyncio.get_running_loop()
        # except RuntimeError:
        #     future = self.workers.submit(self.run, *args, **kwargs)
        #     return asyncio.wrap_future(future)
        # else:
        #     return loop.run_in_executor(self.workers, partial(self.run, *args, **kwargs))
        return try_async_future(
            self.workers.submit(self.run, *args, **kwargs)
        )

    def run(self, *args, **kwargs):
        """
        Run the entry point.

        Args:
            self: (todo): write your description
        """
        with glb['worker'].enter(self):
            return get_entrypoint(self.entrypoint, False)(*args, **kwargs)
        # return request_entrypoint(*args, **kwargs)

    def shutdown(self, wait=True):
        """
        Shutdown all workers.

        Args:
            self: (todo): write your description
            wait: (bool): write your description
        """
        return self.workers.shutdown(wait)


class AsyncWorkers(Workers):
    __type__ = 'async'

    def __init__(self, name, max_workers, entrypoint=None, *args, **kwargs):
        """
        Create a new : class.

        Args:
            self: (todo): write your description
            name: (str): write your description
            max_workers: (int): write your description
            entrypoint: (str): write your description
        """
        def setup_async_thread():
            """
            Setup the asyncio event loop.

            Args:
            """
            nonlocal ready_evt
            if sys.platform == 'win32':
                loop = asyncio.ProactorEventLoop()
            else:
                loop = asyncio.get_event_loop()

            asyncio.set_event_loop(loop)
            self.loop = loop
            # 初始化完成事件
            ready_evt.set()
            del ready_evt

            self._sema = asyncio.Semaphore(max_workers)
            try:
                loop.run_forever()
            finally:
                try:
                    cancel_all_tasks(loop)
                    loop.run_until_complete(loop.shutdown_asyncgens())
                finally:
                    loop.close()

        if max_workers is None:
            # 未限制的异步行为
            max_workers = float('inf')

        super().__init__(name, 1, entrypoint)
        self.loop = None
        self.max_workers = max_workers
        self._sema = None
        self.workers = ThreadPoolExecutor(
            max_workers, thread_name_prefix=name)
        ready_evt = threading.Event()
        self.workers.submit(setup_async_thread)
        ready_evt.wait()

    def submit(self, *args, **kwargs):
        """
        Submit a coroutine.

        Args:
            self: (todo): write your description
        """
        # fut = asyncio.run_coroutine_threadsafe(self.run(*args, **kwargs), self.loop)
        # try:
        #     # 如果当前存在协程循环，则返回协程future，否则返回线程future。
        #     loop = asyncio.get_running_loop()
        #     fut = asyncio.wrap_future(fut, loop=loop)
        # except RuntimeError:
        #     pass
        # return fut
        return try_async_future(
            asyncio.run_coroutine_threadsafe(self.run(*args, **kwargs), self.loop)
        )

    async def run(self, *args, **kwargs):
          """
          Run the entry point.

          Args:
              self: (todo): write your description
          """
        with glb['worker'].enter(self):
            async with self._sema:
                return await get_entrypoint(self.entrypoint, True)(*args, **kwargs)
            # return await async_request_entrypoint(*args, **kwargs)

    def shutdown(self, wait=True):
        """
        Shutdown the event loop.

        Args:
            self: (todo): write your description
            wait: (bool): write your description
        """
        self.loop.call_soon_threadsafe(self.loop.stop)
        super().shutdown(wait)


def setup_worker(name, config):
    """
    Setup the worker.

    Args:
        name: (str): write your description
        config: (todo): write your description
    """
    def get_workers_cls(type_name):
        """
        Returns a dictionary of workers.

        Args:
            type_name: (str): write your description
        """
        for subcls in Workers.__subclasses__():
            if subcls.__type__ == type_name:
                return subcls
        raise TypeError('没有找到对应类型的Worker处理器。')

    global REGISTERED_WORKER
    max_concurrent = config['max_concurrent']
    # is_async = config.get('async', False)
    # if is_async:
    #     if max_concurrent is None or max_concurrent < 1:
    #         workers_cls = AsyncNullWorkers
    #     else:
    #         workers_cls = AsyncWorkers
    # else:
    #     if max_concurrent is None or max_concurrent < 1:
    #         workers_cls = NullWorkers
    #     else:
    #         workers_cls = ThreadWorkers
    workers_cls = get_workers_cls(config['type'])

    entrypoint = config.get('entrypoint', 'request')
    # entrypoint = get_entrypoint(config.get('entrypoint', 'request'), is_async)
    REGISTERED_WORKER[name] = workers_cls(name, max_concurrent, entrypoint)


def init_workers():
    """ 初始化工作者们。 """
    global REGISTERED_WORKER

    workers = get_config(SECTION_WORKER)

    for k, v in workers.items():
        setup_worker(k, v)


def get_worker(name):
    """ 返回指定名称的工作者。"""
    global REGISTERED_WORKER
    return REGISTERED_WORKER.get(name)


def shutdown_all():
    """
    Shutdown all open connections to all instances.

    Args:
    """
    global REGISTERED_WORKER
    for k, v in REGISTERED_WORKER.items():
        v.shutdown(False)


def shutdown(name, wait=True):
    """
    Shutdown a named listener.

    Args:
        name: (str): write your description
        wait: (bool): write your description
    """
    get_worker(name).shutdown(wait)


def restart(name):
    """
    Restart the worker.

    Args:
        name: (str): write your description
    """
    get_worker(name).shutdown(True)
    setup_worker(name, get_config(SECTION_WORKER))
