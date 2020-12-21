

from fastapi import APIRouter
from app.model.param import (
    NewTaskParams,
    ListTaskParams,
)
from app.model.response import (
    NewTaskResp,
    ListTaskResp,
)
from app.model.data import TaskModel
from app.taskflow.task import (
    create_task as _create_task,
    list_task as _list_task
)

task_router = APIRouter()


@task_router.get(
    '/detail',
)
async def detail_task():
    raise NotImplementedError


@task_router.get(
    '/list',
    response_model=ListTaskResp
)
async def list_task(
    param: ListTaskParams
):
    """ 任务列表。"""
    data = _list_task(param.offset, param.limit)
    return ListTaskResp(
        data=data
    )


@task_router.post(
    '/new',
    response_model=NewTaskResp
)
async def create_task(
    params: NewTaskParams,
):
    """ 新建任务。"""
    task = _create_task(
        url=params.url,
        options=params.options
    )
    task.run_async()
    data = [TaskModel(
        sign=task.sign,
        title=task.sign,
        url=params.url
    )]

    return NewTaskResp(data=data)


