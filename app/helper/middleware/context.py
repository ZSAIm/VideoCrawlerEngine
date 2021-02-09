
from starlette.requests import Request
from helper.ctxtools.mgr import run_context_from_dict
import json


class ContextStackMiddleware:
    async def __call__(self, request: Request, call_next):
        context = request.cookies.get('context', '{}')
        with run_context_from_dict(json.loads(context)):
            response = await call_next(request)
        return response

