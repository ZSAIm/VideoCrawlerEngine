from .base import ConfMeta, List, FileSize


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

    convert_strict: bool

    maxsize: FileSize()

    @staticmethod
    def default():
        return ScriptConf()['base']
