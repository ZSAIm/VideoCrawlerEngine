

from fastapi import APIRouter, Depends
from helper.conf import get_conf
from app.model.param import ConfModifyParams, QueryConfigureParams
from app.model.data import AppConfModel, ModifyRespModel, AppRespModel
from app.model.response import ConfQueryResp, ConfModifyResp, AppResponse
from app.helper.routers.conf import reload_conf as _reload_conf
from app.helper.routers.utils import client_hook
from app.model.param import ConfReloadParams as _ConfReloadParams
from helper.worker import get_worker, executor
from helper.client import get_client
from functools import partial
from pydantic import Field, BaseModel
import asyncio

conf_router = APIRouter()


@conf_router.get(
    '/query',
    response_model=ConfQueryResp
)
async def query_conf(
    params: QueryConfigureParams = Depends(QueryConfigureParams)
):
    conf_field = []
    for name in ['app', 'script', 'taskflow', 'worker']:
        conf = get_conf(name)
        conf_field.append({
            'title': name,
            'name': name,
            'groups': [{
                'title': k0,
                'name': k0,
                'items': [
                    section.get_field(k1)
                    for k1 in section.keys()
                ]
            } for k0, section in conf.items()]
        })

    return ConfQueryResp(data=[
        AppConfModel(**conf)
        for conf in conf_field
    ])


@conf_router.post(
    '/modify',
    response_model=ConfModifyResp
)
async def modify_conf(
    params: ConfModifyParams
):
    resp_lst = []
    # 写回配置
    for item in params.items:
        app, group, field = item.link
        conf = get_conf(app)
        conf[group][field] = item.newVal
        try:
            conf.commit()
            resp_lst.append(ModifyRespModel(
                id=item.link,
                errcode=0,
                errmsg=''
            ))
        except Exception as err:
            from traceback import print_exc, format_exc
            print_exc()
            resp_lst.append(ModifyRespModel(
                id=item.link,
                errcode=1,
                errmsg=format_exc()
            ))

    return ConfModifyResp(data=resp_lst)


class ConfReloadParams(_ConfReloadParams):
    timeout: float = Field(title='响应超时时间', default=5)


@conf_router.post(
    '/reload',
    response_model=AppResponse
)
async def reload_conf(
    params: ConfReloadParams = Depends(ConfReloadParams)
):
    async def reload(app_name):
        worker = get_worker('default')
        cli = get_client(
            app_name,
            timeout=params.timeout,
            hook=partial(client_hook, name=app_name),
            raw=True
        )
        return await executor.submit(
            worker,
            (cli.reload_conf,)
        )
    results = await asyncio.gather(
        *[reload(name) for name in ['script', 'taskflow']]
    )
    resp = AppRespModel(
        name='api',
        latency=0,
        **dict(await _reload_conf(params))
    )
    results = [resp] + results
    return AppResponse(data=results)
