
from fastapi import FastAPI
from .routers import include_routers
from .version import version, title, description
from app.helper.middleware import (
    include_exception_handler,
    include_middleware,
)
from app.helper.middleware.context import ContextStackMiddleware

app = FastAPI(
    title=title,
    version=version,
    description=description,
)

include_routers(app)
include_exception_handler(app)
include_middleware(app, ContextStackMiddleware())
