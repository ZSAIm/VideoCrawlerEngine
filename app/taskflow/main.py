from helper.worker import register_worker
from helper.worker import get_ep
from app.taskflow.app import app
from helper.conf import get_conf
from helper.client import get_client
from urllib.parse import urlparse
import uvicorn
from request.download import download
from request.ffmpeg import ffmpeg
from request.live import live_daemon
from request.utils import cleanup, jsruntime


def main():
    get_client('script')
    for k, v in get_conf('payload').items():
        register_worker(
            name=k,
            max_concurrent=v.get('max_concurrent', None),
            async_type=v['async'],
            meonly=v.get('meonly', False),
            ep=get_ep(v.get('entrypoint', 'requester'))
        )
    conf = get_conf('app').taskflow
    gateway = conf['gateway']
    host = conf.get('host', None)
    port = conf.get('port', None)
    if not host:
    #     gateway = urlparse(conf['gateway'])
    #     host = gateway.hostname
    #     port = gateway.port
        host = gateway.hostname
        port = gateway.port

    uvicorn.run(app, host=host, port=port)

