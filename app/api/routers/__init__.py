
from fastapi import FastAPI
from .task import task_router


def include_routers(app: FastAPI) -> None:
    app.include_router(
        task_router,
        prefix='/task'
    )