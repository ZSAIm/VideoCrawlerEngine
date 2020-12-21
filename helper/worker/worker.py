
from .entrypoint import Entrypoint
from threading import Semaphore
import asyncio


class Worker:
    def __init__(
        self,
        name: str,
        max_concurrent: int,
        async_type: bool,
        meonly: bool,
        entrypoint: Entrypoint,
        *args,
        **kwargs
    ):
        self.name = name
        self.entrypoint = entrypoint
        if max_concurrent is None:
            max_concurrent = float('inf')
        self.max_concurrent = max_concurrent
        self.async_type = async_type
        self.meonly = meonly
        # if async_type:
        #     # 在第一次__aenter__所在的事件循环进行初始化
        #     self.semaphore = None
        # else:
        self.semaphore = Semaphore(max_concurrent)
        self.count = 0

    def __enter__(self):
        self.semaphore.acquire()
        self.count += 1
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.count -= 1
        self.semaphore.release()

    async def __aenter__(self):
        # if self.semaphore is None:
        if not isinstance(self.semaphore, asyncio.Semaphore):
            # 只能用于同一个协程事件循环
            self.semaphore = asyncio.Semaphore(self.max_concurrent)
        await self.semaphore.acquire()
        self.count += 1
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.count -= 1
        self.semaphore.release()

    def __call__(self, *args, **kwargs):
        async def async_run():
            return await self.entrypoint.arun(*args, **kwargs)

        def run():
            return self.entrypoint.run(*args, **kwargs)

        if self.async_type:
            return async_run()
        else:
            return run()



