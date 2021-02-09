
from .entrypoint import Entrypoint
from threading import Semaphore
import asyncio


class Worker:
    def __init__(
        self,
        name: str,
        max_concurrent: int,
        async_type: bool,
        independent: bool,
        entrypoint: Entrypoint,
        *args,
        **kwargs
    ):
        self.name = name
        self.entrypoint = entrypoint
        if max_concurrent in (float('inf'),):
            max_concurrent = None
        self.max_concurrent = max_concurrent
        self.async_type = async_type
        self.independent = independent
        self.semaphore = Semaphore(float('inf') if max_concurrent is None else max_concurrent)
        self.count = 0

    def __enter__(self):
        self.semaphore.acquire()
        self.count += 1
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.count -= 1
        self.semaphore.release()

    async def __aenter__(self):
        if not isinstance(self.semaphore, asyncio.Semaphore):
            # 只能用于同一个协程事件循环
            self.semaphore = asyncio.Semaphore(
                float('inf') if self.max_concurrent is None else self.max_concurrent
            )
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



