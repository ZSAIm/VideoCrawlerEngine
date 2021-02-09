# TODO: 使用Sqlite来存储日志

from helper.conf import get_conf

__logger_conf = get_conf('logger')


def get_logger(name):
    __logger_conf[name]


raise NotImplementedError()