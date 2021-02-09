
from argparse import ArgumentParser
from helper.conf import get_conf
import importlib


def run_app(name, *args, **kwargs):
    conf = get_conf('app')
    app = conf[name]
    module = importlib.import_module(app.module)
    return getattr(module, app.entrypoint)(*args, **kwargs)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('app')

    args = parser.parse_args()

    run_app(args.app)
