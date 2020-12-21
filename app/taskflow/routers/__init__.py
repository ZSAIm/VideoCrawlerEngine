from fastapi import FastAPI

from app.taskflow.routers.routers import task_router


def include_routers(app: FastAPI) -> None:
    app.include_router(
        task_router,
        prefix='/api/v1/task'
    )