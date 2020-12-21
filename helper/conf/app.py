from .base import ConfMeta


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
    gateway: str

    host: str
    port: int
    protocol: str