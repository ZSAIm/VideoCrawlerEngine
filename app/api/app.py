
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from .routers import include_routers
from app.helper.middleware import include_exception_handler
from helper.conf import get_conf
from .helper import read_html_file
from app.helper.middleware.proxy import ReverseProxyMiddleware
from ..helper.middleware import include_middleware
from urllib.parse import urljoin
import os

app = FastAPI()
conf = get_conf('app')

htmldist = {
    'static': os.path.join(conf.html['dist'], 'static'),
    'index': os.path.join(conf.html['dist'], 'index.html')
}

app.mount(
    '/static',
    StaticFiles(directory=htmldist['static']),
    name='dist'
)

include_routers(app)
include_exception_handler(app)


proxy_pass_configures = [
    {
        'source': '/api/task/',
        'pass': urljoin(
            conf.taskflow['gateway'].geturl(),
            '/api/v1/task/'
        ),
    }, {
        'source': '/api/script/',
        'pass': urljoin(
            conf.script['gateway'].geturl(),
            '/api/v1/script/'
        ),
    }
]
include_middleware(app, ReverseProxyMiddleware(proxy_pass_configures))


@app.get('/')
async def index():
    return HTMLResponse(read_html_file(htmldist['index']))
