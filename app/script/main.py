from .manager import init_scripts
from helper.conf import get_conf
from helper.worker import register_worker
from helper.worker.entrypoint import get_ep
from .app import app
from urllib.parse import urlparse
import uvicorn

_GLOBAL_WORKER = 'script'


def init_worker():
    config = get_conf('payload')
    # script_config = plcfg.get_config('script')
    # register_worker(
    #     _GLOBAL_WORKER,
    #     script_config['max_concurrent'],
    #     script_config.get('async', False),
    #     script_config.get('meonly', False),
    #     get_ep(script_config.get('entrypoint', 'requester')),
    # )
    pls = {'script', 'function'}
    for pl in pls:
        register_worker(
            name=pl,
            max_concurrent=config[pl].get('max_concurrent', None),
            async_type=config[pl]['async'],
            meonly=config[pl].get('meonly', False),
            ep=get_ep(config[pl].get('entrypoint', 'requester'))
        )
    # for k, v in get_conf('payload').items():
    #     register_worker(
    #         name=k,
    #         max_concurrent=v.get('max_concurrent', None),
    #         async_type=v['async'],
    #         meonly=False,
    #         ep=get_ep(v.get('entrypoint', 'requester'))
    #     )
    #
    # register_worker(
    #     _GLOBAL_WORKER,
    #     config.script['max_concurrent'],
    #     config.script.get('async', False),
    #     config.script.get('meonly', False),
    #     get_ep(config.script.get('entrypoint', 'requester')),
    # )
    # register_worker(
    #     _GLOBAL_WORKER,
    #     config.script['max_concurrent'],
    #     config.script.get('async', False),
    #     config.script.get('meonly', False),
    #     get_ep(config.script.get('entrypoint', 'requester')),
    # )


def main():
    init_scripts()
    init_worker()

    conf = get_conf('app').script
    host = conf.get('host', None)
    port = conf.get('port', None)
    if not host:
        gateway = urlparse(conf['gateway'])
        host = gateway.hostname
        port = gateway.port

    uvicorn.run(app, host=host, port=port)

