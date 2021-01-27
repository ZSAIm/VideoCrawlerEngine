from .base import ConfMeta
from urllib.parse import urlparse


class ApplicationConf(
    name='app',
    file='conf/app.ini',
    metaclass=ConfMeta
):
    # global
    tempdir: str
    debug: bool

    # app 选项
    module: str
    entrypoint: str
    gateway: urlparse

    host: str
    port: int
    protocol: str