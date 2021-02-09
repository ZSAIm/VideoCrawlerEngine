

from fastapi import APIRouter, Depends
from app.model.param import SystemStateParams, ConfReloadParams
from app.model.response import SystemStateResp, ConfReloadResp
from helper.worker import get_worker, iter_worker, executor
from app.model.data import WorkerStateModel
from helper.conf import iter_conf

system_router = APIRouter()


@system_router.get(
    '/state',
    response_model=SystemStateResp
)
async def get_state(
    params: SystemStateParams = Depends(SystemStateParams)
):
    worker_states = []
    for worker in iter_worker():
        worker_states.append({
            'name': worker.name,
            'maxConcurrent': worker.max_concurrent,
            'independent': worker.independent,
            'asyncType': worker.async_type,
            'count': worker.count
        })
    state_resp = {
        'worker': [WorkerStateModel(**state) for state in worker_states],
    }
    return SystemStateResp(data=state_resp)


@system_router.post(
    '/reload',
    response_model=ConfReloadResp
)
async def reload_conf(
    params: ConfReloadParams
):
    """ 重载系统配置。"""
    for name, conf_cls in iter_conf():
        conf_cls().reload()

    return ConfReloadResp()