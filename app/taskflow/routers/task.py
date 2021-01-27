

from fastapi import APIRouter, Depends
from app.model.param import (
    ListTaskParams,
    NewTasksListParams,
    StopTaskParams,
)
from app.model.response import (
    NewTasksResp,
    ListTasksResp,
    StopTasksResp,
)
from exception import DataExistsError, APIBaseError
from app.model.data import TaskModel, StopTaskModel
from .helper import task as taskhelper
from traceback import format_exc

task_router = APIRouter()


@task_router.get(
    '/list',
    response_model=ListTasksResp
)
async def list_task(
    param: ListTaskParams = Depends(ListTaskParams)
):
    """ 任务列表。"""
    # data = _list_task(param.offset, param.limit)
    data = taskhelper.list(param.offset, param.limit, param.active)
    return ListTasksResp(
        data=data
    )


@task_router.post(
    '/new',
    response_model=NewTasksResp
)
async def create_tasks(
    params: NewTasksListParams,
):
    """ 批量添加任务。"""
    data = []
    for url in params.urls:
        try:
            t = taskhelper.create(url, params.options)
            t.run_async()
            errcode = 0
            errmsg = None
        except APIBaseError as err:
            t = taskhelper.get(err.data)
            errcode = err.code
            errmsg = err.msg
        data.append(TaskModel(
            sign=t.sign,
            title=t.title,
            url=t.url,
            errcode=errcode,
            errmsg=errmsg
        ))
    return NewTasksResp(data=data)


@task_router.post(
    '/stop',
    response_model=StopTasksResp
)
async def stop_tasks(
    params: StopTaskParams
):
    data = []
    for key in params.keys:
        try:
            result = taskhelper.stop(key)
            errcode = 0
            errmsg = None
        except APIBaseError as err:
            errcode = err.code
            errmsg = err.msg

        data.append(StopTaskModel(
            errcode=errcode,
            errmsg=errmsg
        ))
    return StopTasksResp(data=data)
