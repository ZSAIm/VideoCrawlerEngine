from .base import ConfMeta, FileRealPath
import os


class LoggerConf(
    name='logger',
    file='conf/logger.ini',
    metaclass=ConfMeta
):
    logdir: FileRealPath()

