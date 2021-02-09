from .app import app
import uvicorn
from helper.conf import get_conf
from helper.worker import register_worker, get_ep, pool


def main():
    conf = get_conf('app')
    gateway = conf.api.gateway
    default_conf = get_conf('worker')['default']
    register_worker(
        'default',
        default_conf['max_concurrent'],
        default_conf['async'],
        default_conf.get('independent', False),
        get_ep(default_conf['entrypoint'])
    )
    uvicorn.run(app, host=gateway.hostname, port=gateway.port)
    pool.shutdown()
