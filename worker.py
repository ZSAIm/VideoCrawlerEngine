
from traceback import print_exc
from concurrent.futures.thread import ThreadPoolExecutor
import asyncio
import sys
from utils import cancel_all_tasks
from functools import partial
from debugger import dbg

# 工作者平台
REGISTERED_WORKER = {}


class Worker:
    def __init__(self, name):
        self.name = name

    def submit(self):
        raise NotImplementedError

    def run(self):
        raise NotImplementedError

    def shutdown(self, wait=True):
        raise NotImplementedError


class NullWorker(Worker):
    def __init__(self, name, *args, **kwargs):
        super().__init__(name)

    def submit(self, *args, **kwargs):
        return self.run(*args, **kwargs)

    async def run(self, *args, **kwargs):
        return await async_entrypoint(*args, **kwargs)

    def shutdown(self, wait=True):
        pass


class Workers(Worker):
    """ 工作线程"""
    def __init__(self, name, max_workers, *, initializer=None, initargs=()):
        Worker.__init__(self, name)
        self.workers = ThreadPoolExecutor(max_workers, thread_name_prefix=name,
                                          initializer=initializer, initargs=initargs)

    def submit(self, *args, **kwargs):
        """ 提交工作任务。"""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return self.workers.submit(self.run, *args, **kwargs)
        else:
            return loop.run_in_executor(self.workers, partial(self.run, *args, **kwargs))

    def run(self, *args, **kwargs):
        return request_entrypoint(*args, **kwargs)

    def shutdown(self, wait=True):
        return self.workers.shutdown(wait)


class AsyncWorkers(Workers):
    def __init__(self, name, max_workers, *args, **kwargs):
        def setup_async_thread():
            if sys.platform == 'win32':
                loop = asyncio.ProactorEventLoop()
            else:
                loop = asyncio.get_event_loop()

            asyncio.set_event_loop(loop)
            self.loop = loop

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

        super().__init__(name, 1)
        self.loop = None
        self.max_workers = max_workers
        self._sema = None
        self.workers.submit(setup_async_thread)

    def submit(self, *args, **kwargs):
        fut = asyncio.run_coroutine_threadsafe(self.run(*args, **kwargs), self.loop)
        try:
            loop = asyncio.get_running_loop()
            fut = asyncio.wrap_future(fut)
        except RuntimeError:
            pass
        return fut

    async def run(self, *args, **kwargs):
        async with self._sema:
            return await async_entrypoint(*args, **kwargs)

    def shutdown(self, wait=True):
        self.loop.call_soon_threadsafe(self.loop.stop)
        super().shutdown(wait)


async def async_entrypoint(task, context):
    with dbg.run(task, context) as debug:
        try:
            debug.start()
            result = await task.end_request()
            debug.task_done()
        except BaseException as err:
            print_exc()
            task.error_handler(err)
            raise
        finally:
            debug.close()

    return result


def request_entrypoint(task, context):
    """ 请求任务处理入口点。 """
    with dbg.run(task, context) as debug:
        try:
            debug.start()
            result = task.end_request()
            debug.task_done()
            debug.close()
        except BaseException as err:
            print_exc()
            task.error_handler(err)
            raise
        finally:
            debug.close()

    return result


def setup_worker(name, config):
    global REGISTERED_WORKER
    max_concurrent = config['max_concurrent']
    is_async = config.get('async', False)
    if is_async:
        workers_cls = AsyncWorkers
    else:
        if max_concurrent is None or max_concurrent < 1:
            workers_cls = NullWorker
        else:
            workers_cls = Workers

    REGISTERED_WORKER[name] = workers_cls(name, max_concurrent)


def init_workers():
    """ 初始化工作者们。 """
    global REGISTERED_WORKER

    from config import get_config, SECTION_WORKER

    workers = get_config(SECTION_WORKER)

    for k, v in workers.items():
        setup_worker(k, v)


def get_worker(name):
    """ 返回指定名称的工作者。"""
    global REGISTERED_WORKER
    return REGISTERED_WORKER.get(name)


def shutdown():
    global REGISTERED_WORKER
    for k, v in REGISTERED_WORKER.items():
        v.shutdown(False)

