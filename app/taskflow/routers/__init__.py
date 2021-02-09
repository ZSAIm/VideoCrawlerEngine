from fastapi import FastAPI

from .task import task_router
from app.helper.routers.system import system_router


def include_routers(app: FastAPI) -> None:
    app.include_router(task_router, prefix='/api/v1/task')
    app.include_router(system_router, prefix='/api/v1/system')