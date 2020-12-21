from .base import ConfMeta


class PayloadConf(
    name='payload',
    file='conf/payload.ini',
    metaclass=ConfMeta
):
    max_concurrent: int
    meonly: bool
    __items__ = {
        'async': bool
    }