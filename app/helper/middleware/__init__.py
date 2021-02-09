from fastapi import FastAPI
from .exchandler import include_exception_handler


def include_middleware(app: FastAPI, middleware, middleware_type='http'):
    app.middleware(middleware_type)(middleware)