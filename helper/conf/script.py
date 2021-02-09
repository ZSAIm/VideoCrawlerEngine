from .base import (
    ConfMeta,
    UrlParse,
    FileRealPath,
    Integer,
    Boolean,
    String,
    FileSize,
    List,
    Float
)


class ScriptConf(
    name='script',
    file='conf/script.ini',
    metaclass=ConfMeta
):
    order: Integer(title='脚本优先级')
    cookies: String(title='预载Cookies')
    proxies: String(title='预载代理Proxies')
    active: Float(title='指定版本', desc='')
    default_rule: Integer(
        tag='Slider',
        min_value=0,
        max_value=100,
        title='默认选择规则',
        desc='指定范围0-100：0表示最低；100表示最高。(具体排序取决于脚本结果)'
    )
    to_format: List(sep='|', title='目标格式', desc='')
    append: List(sep=',', title='追加处理器', desc='')

    convert_strict: Boolean(
        tag='Switches',
        title='严格转码',
        desc='若真则对视频进行严格转码（耗时长），否则使用快速转码'
    )

    maxsize: FileSize(title='')

    @staticmethod
    def default():
        return ScriptConf()['base']
