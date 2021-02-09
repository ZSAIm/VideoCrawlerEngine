from helper.worker import register_worker
from helper.worker import get_ep, pool
from app.taskflow.app import app
from helper.conf import get_conf
from helper.client import get_client
from urllib.parse import urlparse
import uvicorn

# TODO: requester 做好动态加载的需要
#       后续将requester作为插件加载
from request.download import download
from request.ffmpeg import ffmpeg
from request.live import live_daemon
from request.utils import cleanup, jsruntime


def main():
    get_client('script')
    for k, v in get_conf('worker').items():
        register_worker(
            name=k,
            max_concurrent=v.get('max_concurrent', None),
            async_type=v['async'],
            independent=v.get('independent', False),
            ep=get_ep(v.get('entrypoint', 'requester'))
        )
    conf = get_conf('app').taskflow
    gateway = conf['gateway']
    host = conf.get('host', None)
    port = conf.get('port', None)
    if not host:
        host = gateway.hostname
        port = gateway.port

    uvicorn.run(app, host=host, port=port)
    # TODO: 先正常暂停持久化任务后再进行关闭线程。
    pool.shutdown()
