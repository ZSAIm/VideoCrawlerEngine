

from fastapi import FastAPI, Request
from .exception import APIException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles

app = FastAPI()
templates = Jinja2Templates(directory='templates')
app.mount('/static', StaticFiles(directory='static'), name='static')


@app.exception_handler(APIException)
async def api_exception_handler(
    request: Request,
    exception: APIException
):
    return JSONResponse(
        status_code=200,
        content=dict(
            code=exception.code,
            msg=exception.msg,
            data=exception.data,
        )
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exception: RequestValidationError
):
    return JSONResponse(
        status_code=418,
        content=dict(
            code=-1,
            msg='参数检查不通过。',
            data=[]
        ),
    )


