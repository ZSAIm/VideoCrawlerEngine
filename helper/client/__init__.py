
from .base import get_client as _get_client
import importlib
import sys


def get_client(name):
    """ 获取服务的SDK客户端。"""
    module_name = f'helper.client.{name}'
    if not sys.modules.get(module_name):
        importlib.import_module(module_name)

    return _get_client(name)()
