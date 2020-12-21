from fastapi import FastAPI

from app.script.routers.routers import script_router, stack_router


def include_routers(app: FastAPI) -> None:
    app.include_router(
        script_router,
        prefix='/api/v1/script'
    )
    app.include_router(
        stack_router,
        prefix='/api/v1/stack'
    )