from .manager import init_scripts
from helper.conf import get_conf
from helper.worker import register_worker, pool
from helper.worker.entrypoint import get_ep
from .app import app
import uvicorn


def init_worker():
    config = get_conf('worker')
    pls = {'script', 'function'}
    for pl in pls:
        register_worker(
            name=pl,
            max_concurrent=config[pl].get('max_concurrent', None),
            async_type=config[pl]['async'],
            independent=config[pl].get('independent', False),
            ep=get_ep(config[pl].get('entrypoint', 'requester'))
        )


def main():
    init_scripts()
    init_worker()

    conf = get_conf('app').script
    gateway = conf['gateway']
    host = conf.get('host', None)
    port = conf.get('port', None)
    if not host:
        host = gateway.hostname
        port = gateway.port
    uvicorn.run(app, host=host, port=port)

    pool.shutdown()