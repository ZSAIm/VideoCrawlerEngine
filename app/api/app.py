
from fastapi import FastAPI
from .routers import include_routers
from app.helper.middleware import include_exception_handler

app = FastAPI()

include_routers(app)
include_exception_handler(app)
