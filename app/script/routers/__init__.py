from fastapi import FastAPI

from .routers import script_router, stack_router
from app.helper.routers.system import system_router


def include_routers(app: FastAPI) -> None:
    app.include_router(script_router, prefix='/api/v1/script')
    app.include_router(stack_router, prefix='/api/v1/stack')
    app.include_router(system_router, prefix='/api/v1/system')