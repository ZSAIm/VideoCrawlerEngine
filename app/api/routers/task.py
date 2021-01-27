

from fastapi import APIRouter, Depends
# from model.task import TasksCreateModel, TaskBaseModel, StopTaskModel
from app.model.param import (
    StopTaskParams,

)
from typing import List

task_router = APIRouter()


@task_router.post('/new')
async def add_tasks(
    new_tasks: List[CreateTaskParams] = Depends(CreateTaskParams),
):
    pass


@task_router.get('/stop')
async def stop_tasks(
    task: StopTaskParams
):
    pass


@task_router.get('/start')
async def start_tasks(
    task: StopTaskParams
):
    pass


@task_router.get('/pause')
async def pause_tasks(
    task: StopTaskParams
):
    pass


@task_router.get('/delete')
async def delete_tasks(

):
    pass


@task_router.get('/query')
async def lst_task(

):
    pass




