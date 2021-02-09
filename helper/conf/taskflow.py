from .base import (
    ConfMeta,
    UrlParse,
    FileRealPath,
    Integer,
    Boolean,
    String,
    List
)


class TaskFlowConf(
    name='taskflow',
    file='conf/taskflow.ini',
    metaclass=ConfMeta
):
    default_rule: Integer()
    to_format: List(sep='|')
    append: List(sep=',')
