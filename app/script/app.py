
from fastapi import FastAPI
from .routers import include_routers
from .version import version, title, description
from .middleware import include_middlewares

app = FastAPI(
    title=title,
    version=version,
    description=description,
)

include_routers(app)
include_middlewares(app)