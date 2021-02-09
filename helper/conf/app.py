from .base import (
    ConfMeta,
    UrlParse,
    FileRealPath,
    Integer,
    Boolean,
    String,
)
import os


class ApplicationConf(
    name='app',
    file='conf/app.ini',
    metaclass=ConfMeta
):
    # global
    tempdir: String(
        title='临时目录',
        desc='指定临时目录路径，若不指定则使用系统默认临时目录。'
    )
    debug: Boolean(tag='Switches', title='开启调试模式', desc='开启调试模式后就开启了调试模式！！！')

    # app 选项
    module: String(title='应用模块文件', desc='应用模块的文件入口')
    entrypoint: String(title='应用入口', disabled=True)
    gateway: UrlParse(title='应用网关URL')

    host: String(title='应用主机地址')
    port: Integer(title='应用端口')
    protocol: String(title='应用协议')

    # html
    dist: FileRealPath(title='前端HTML路径', desc='前端代码编译生成目录')
