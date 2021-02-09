
from .worker import Worker
from .entrypoint import Entrypoint
from . import executor
from .entrypoint import get_ep
from . import pool


__WORKERS = {}


def get_worker(
    name: str
) -> Worker:
    return __WORKERS[name]


def register_worker(
    name: str,
    max_concurrent: int,
    async_type: bool,
    independent: bool,
    ep: Entrypoint,
    *args,
    **kwargs
) -> None:
    worker = Worker(
        name=name,
        max_concurrent=max_concurrent,
        async_type=async_type,
        independent=independent,
        entrypoint=ep,
        *args,
        **kwargs
    )
    __WORKERS[name] = worker


def iter_worker():
    return iter(__WORKERS.values())


def shutdown(wait=True):
    pool.shutdown(wait)
