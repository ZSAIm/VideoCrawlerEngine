
from fastapi import APIRouter, Depends
from app.model.data import AppRespModel
from app.model.response import AppResponse
from app.model.param import SystemStateParams as _SystemStateParams
from app.helper.routers.system import get_state as _simple_state
from app.helper.routers.utils import client_hook
from helper.worker import executor, get_worker
from functools import partial
from helper.client import get_client
from pydantic import Field
from helper.conf import get_conf
import asyncio

system_router = APIRouter()


class SystemStateParams(_SystemStateParams):
    timeout: float = Field(title='响应超时时间', default=5)


@system_router.get(
    '/state',
    response_model=AppResponse
)
async def get_state(
    params: SystemStateParams = Depends(SystemStateParams)
):
    async def state(app_name):
        worker = get_worker('default')
        cli = get_client(
            app_name,
            timeout=params.timeout,
            hook=partial(client_hook, name=app_name),
            raw=True
        )
        result = await executor.submit(
            worker,
            (cli.get_state,)
        )
        return result

    results = await asyncio.gather(
        *[state(name) for name in ['script', 'taskflow']]
    )
    api_state = AppRespModel(
        name='api',
        latency=0,
        gateway=get_conf('app')['api'].gateway.geturl(),
        **dict(await _simple_state(params))
    )
    results = [api_state] + results
    return AppResponse(data=results)