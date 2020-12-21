
from .base import get_conf as __get_conf, ConfMeta
from typing import ClassVar
import importlib
import sys

DEBUG = True


def get_conf(name: str) -> ClassVar[ConfMeta]:
    package = f'{get_conf.__module__}.{name}'
    if not sys.modules.get(package, None):
        importlib.import_module(package)
    conf_cls = __get_conf(name)
    return conf_cls()
