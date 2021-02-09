
from fastapi import FastAPI
from .conf import conf_router
from .system import system_router


def include_routers(app: FastAPI) -> None:
    app.include_router(conf_router, prefix='/api/conf')
    app.include_router(system_router, prefix='/api/system')
