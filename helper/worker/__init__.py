
from .worker import Worker
from .entrypoint import Entrypoint
from . import executor
from .entrypoint import get_ep


__WORKERS = {}


def get_worker(
    name: str
) -> Worker:
    return __WORKERS[name]


def register_worker(
    name: str,
    max_concurrent: int,
    async_type: bool,
    meonly: bool,
    ep: Entrypoint,
    *args,
    **kwargs
) -> None:
    worker = Worker(
        name=name,
        max_concurrent=max_concurrent,
        async_type=async_type,
        meonly=meonly,
        entrypoint=ep,
        *args,
        **kwargs
    )
    __WORKERS[name] = worker

