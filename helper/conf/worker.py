from .base import (
    ConfMeta,
    UrlParse,
    FileRealPath,
    Integer,
    Boolean,
    String,
)


class WorkerConf(
    name='worker',
    file='conf/worker.ini',
    metaclass=ConfMeta
):
    max_concurrent: Integer(
        tag='TextField',
        title='最大并发量',
        desc='限制载荷的最大并发量。inf表示不做限制。'
    )
    independent: Boolean(
        title='独占线程',
        desc='若开启则该负载将使用独立的线程进行处理，不与其他载荷共享处理线程。'
    )
    entrypoint: String(
        title='处理器入口点',
        disabled=True
    )
    __items__ = {
        'async': Boolean(
            tag='Switches',
            title='异步类型',
            desc='描述该载荷处理器属于异步处理还是同步处理。',
            disabled=True,
        )
    }