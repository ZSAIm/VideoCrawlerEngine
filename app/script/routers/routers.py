

from fastapi import APIRouter, Depends, Request
from app.model.param import (
    GetSupportedParams,
    GetVersionsParams,
    RegisterParams,
    ExecuteScriptParams,
    RemoteApplyParams
)
from app.model.response import (
    GetSupportedResp,
    GetVersionsResp,
    RegisterResp,
    ExecuteScriptResp,
    RemoteApplyResp,
)
from app.model.data import (
    ScriptModel,
    ApplyModel,
)
from app.script.manager import (
    get_script,
    get_versions as script_versions,
    supported_script,
    select_script,
)
from request.script import simple_script
from helper.payload import dictify_payload
from helper.ctxtools.mgr import get_ctx
from helper.ctxtools import ctx
from request.export import stack_function
from exception import DataNotFound
from traceback import format_exc
script_router = APIRouter()
stack_router = APIRouter()


@script_router.get(
    '/get_supported',
    response_model=GetSupportedResp
)
async def get_supported(
    param: GetSupportedParams = Depends(GetSupportedParams),
):
    scripts = supported_script(param.url)
    data = [ScriptModel(
        name=s.name,
        version=s.version,
        author=s.author,
        created_date=s.created_date,
        qn_ranking=s.quality_ranking,
        license=s.license,
    ) for s in scripts]
    return GetSupportedResp(data=data)


@script_router.get(
    '/get_versions',
    response_model=GetVersionsResp
)
async def get_versions(
    param: GetVersionsParams = Depends(GetVersionsParams)
):
    scripts = script_versions(param.name)
    data = [ScriptModel(
        name=s.name,
        version=s.version,
        author=s.author,
        created_date=s.created_date,
        qn_ranking=s.quality_ranking,
        license=s.license,
        supported_domains=s.supported_domains,
    ) for s in [ns[1] for ns in scripts]]
    return GetVersionsResp(data=data)


@script_router.post(
    '/register',
    response_model=RegisterResp
)
async def register(
    param: RegisterParams = Depends(RegisterParams),
):
    raise NotImplementedError()


@script_router.post(
    '/exec',
    response_model=ExecuteScriptResp
)
async def exec_script(
    param: ExecuteScriptParams,
):
    script_name = select_script(supported_script(param.url))
    if not script_name:
        raise DataNotFound(f'找不到处理该链接的脚本。{param.url}')
    script_task = get_script(script_name)

    req = simple_script(
        url=param.url,
        rule=param.rule,
        script_task=script_task,
    )
    result = await req.start_request()
    return ExecuteScriptResp(
        # data=[dictify_payload(dict(req.iter_data()))]
        data=dictify_payload(result)
    )


@stack_router.post(
    '/preview'
)
async def preview():
    pass


@stack_router.post(
    '/destroy',
)
async def destroy_stack(

):
    """ 销毁脚本缓存栈。"""
    raise NotImplementedError()


@stack_router.post(
    '/remote_apply',
    response_model=RemoteApplyResp
)
async def remote_apply(
    param: RemoteApplyParams,
):
    """ 执行脚本栈中函数。"""
    key = get_ctx(ctx.script.key, None)
    func_req = stack_function(param.funcid, param.args, param.kwargs)
    try:
        result = await func_req.start_request()
    except Exception as err:
        return RemoteApplyResp(data=ApplyModel(
            key=key,
            funcid=param.funcid,
            context=dictify_payload(dict(func_req.iterdata())),
            exc=format_exc(),
        ))
    else:
        return RemoteApplyResp(
            data=ApplyModel(**dictify_payload(dict(
                key=key,
                funcid=param.funcid,
                context=dict(func_req.iterdata()),
                ret=result
            )))
        )


@stack_router.post(
    '/hit'
)
async def hit_stack(

):
    raise NotImplementedError()


