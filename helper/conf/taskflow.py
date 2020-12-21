from .base import ConfMeta, List


class TaskFlowConf(
    name='taskflow',
    file='conf/taskflow.ini',
    metaclass=ConfMeta
):
    default_rule: int
    to_format: List(sep='|')
    append: List(sep=',')
