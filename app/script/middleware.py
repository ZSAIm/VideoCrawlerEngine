
from fastapi import FastAPI
from starlette.requests import Request
from helper.ctxtools.vars.script import script
from helper.ctxtools.mgr import (
    run_context_from_dict,
    run_context_from_scope,
)
from app.helper.middleware import include_exception_handler
from contextlib import ExitStack
import json


async def stack_middleware(
    request: Request,
    call_next,
):
    # task_key = request.cookies.get('SIGN', None)
    context = request.cookies.get('context', '{}')
    with run_context_from_dict(json.loads(context)):
        response = await call_next(request)
    return response


def include_middlewares(app: FastAPI, middleware_type='http') -> None:
    include_exception_handler(app)
    app.middleware(middleware_type)(stack_middleware)


# def include_stack_middleware(app: FastAPI, middleware_type='http') -> None:
#     app.middleware(middleware_type)(stack_middleware)