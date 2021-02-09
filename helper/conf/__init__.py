
from .base import get_conf as __get_conf, ConfMeta, iter_conf
from typing import ClassVar
import importlib
import sys

DEBUG = True


def get_conf(__name: str, **kwargs) -> ClassVar[ConfMeta]:
    package = f'{get_conf.__module__}.{__name}'
    if not sys.modules.get(package, None):
        importlib.import_module(package)
    conf_cls = __get_conf(__name)
    return conf_cls(**kwargs)
