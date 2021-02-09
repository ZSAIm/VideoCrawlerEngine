
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

# from app.script.middleware import stack_middleware
# from helper.ctxtools.vars.task import stack
from exception import (
    APIBaseError,
)
from helper.codetable import VALIDATE_ERROR
from traceback import format_exc, print_exc


async def api_exception_handler(
    request: Request,
    exc: APIBaseError
):
    return JSONResponse(
        status_code=200,
        content=dict(
            code=exc.code,
            msg=exc.msg,
            data=exc.data
        ),
    )


async def not_impl_exception_handler(
    request: Request,
    exc: NotImplementedError
):
    return JSONResponse(
        status_code=502,
        content={
            'code': 502,
            'msg': '接口未实现。',
            'data': repr(exc)
        }
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
):
    print_exc()
    return JSONResponse(
        status_code=418,
        content=dict(
            code=VALIDATE_ERROR,
            msg='参数检查不通过。',
            data=[]
        ),
    )


def include_exception_handler(app: FastAPI) -> None:
    """ 异常处理器。"""
    app.exception_handler(APIBaseError)(api_exception_handler)
    app.exception_handler(RequestValidationError)(validation_exception_handler)
    app.exception_handler(NotImplementedError)(not_impl_exception_handler)



