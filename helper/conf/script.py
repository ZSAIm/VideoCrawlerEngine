from .base import ConfMeta, List


class ScriptConf(
    name='script',
    file='conf/script.ini',
    metaclass=ConfMeta
):
    order: int
    cookies: str
    proxies: str
    active: float
    default_rule: int
    to_format: List(sep='|')
    append: List(sep=',')

    strict: bool
    convert: List(sep=' ')

    @staticmethod
    def default():
        return ScriptConf()['base']
