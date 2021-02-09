

from fastapi import APIRouter, Depends
from app.model.param import ConfReloadParams
from app.model.response import ConfReloadResp
from helper.conf import iter_conf

conf_router = APIRouter()


@conf_router.post(
    '/reload',
    response_model=ConfReloadResp
)
async def reload_conf(
    params: ConfReloadParams
):
    """ 重载系统配置。"""
    for name, conf in iter_conf():
        conf().reload()

    return ConfReloadResp()