import json
import os
import re
from asyncio import tasks
from contextlib import contextmanager
from datetime import datetime
from threading import Thread

import jscaller
from requests.cookies import RequestsCookieJar, create_cookie

from config import get_config, SECTION_WORKER

NoneType = type(None)


def current_time():
    """ 返回 '时:分:秒' 格式的当前时间文本。"""
    return datetime.now().strftime('%H:%M:%S.%f')


def split_name_version(script_name):
    """ 返回分割的脚本名称，版本。"""
    name_version = script_name.rsplit('-', 1)
    if len(name_version) == 1:
        name, version = name_version[0], None
    else:
        name, version = name_version
        try:
            version = float(version)
        except ValueError:
            # 若无法转为浮点，那么将判定为其后的-是非版本号
            name = script_name
            version = None
    return name, version


def run_forever(function, *args, name=None, **kwargs):
    """ 进程周期内的运行线程。"""
    Thread(target=function, args=args, kwargs=kwargs, name=name, daemon=True).start()


def cancel_all_tasks(loop):
    """ 关闭循环中剩余的所有任务。 asyncio.runners._cancel_all_tasks"""
    to_cancel = tasks.all_tasks(loop)
    if not to_cancel:
        return

    for task in to_cancel:
        task.cancel()

    loop.run_until_complete(
        tasks.gather(*to_cancel, loop=loop, return_exceptions=True))

    for task in to_cancel:
        if task.cancelled():
            continue
        if task.exception() is not None:
            loop.call_exception_handler({
                'message': 'unhandled exception during asyncio.run() shutdown',
                'exception': task.exception(),
                'request_task': task,
            })


def extract_cookies_str_to_jar(cookies_str, cookiejar=None, overwrite=True, cookies_specified_kw=None):
    """ cookies字符串提取成CookieJar。
    :param
        cookies_str:    cookie字符串文本
        cookiejar:      (可选)指定cookie添加到的cookiejar对象
        overwrite:      (可选)指定是否覆盖已经存在的cookie键
        cookie_kwargs:  (可选)指定Cookie的参数，参见 cookielib.Cookie 对象
                        - domain: 指定所在域
                        - path: 指定所在路径
    """
    # 分割cookies文本并提取到字典对象。
    cookie_dict = {}
    for cookie in cookies_str.split(';'):
        try:
            key, value = cookie.split('=', 1)
        except ValueError:
            continue
        else:
            cookie_dict[key] = value

    if not cookies_specified_kw:
        cookies_specified_kw = {}

    return cookiejar_from_dict(cookie_dict, cookiejar, overwrite, cookies_specified_kw)


def cookiejar_from_dict(cookie_dict, cookiejar=None, overwrite=True, cookies_specified_kw=None):
    """ 以下代码引用自requests库
    具体参数说明参考：requests.cookies.cookiejar_from_dict。
    """
    if not cookies_specified_kw:
        cookies_specified_kw = {}

    if cookiejar is None:
        cookiejar = RequestsCookieJar()

    if cookie_dict is not None:
        names_from_jar = [cookie.name for cookie in cookiejar]
        for name in cookie_dict:
            if overwrite or (name not in names_from_jar):
                # 添加参数 cookies_specified_kw
                cookiejar.set_cookie(create_cookie(name, cookie_dict[name], **cookies_specified_kw))

    return cookiejar


def json_stringify(source,
                   replace=None,
                   keys=(float('nan'), float('inf'), float('-inf')),
                   indent=None):
    """ 处理非标准JSON的格式化问题。由于python内置的json会对nan, inf, -inf进行处理，这会造成非标准的JSON。"""
    def check_dict(o):
        return {go_check(k): go_check(v) for k, v in o.items()}

    def check_list_tuple_set(o):
        return [go_check(v) for v in o]

    def go_check(o):
        if isinstance(o, (list, tuple, set)):
            return check_list_tuple_set(o)
        elif isinstance(o, dict):
            return check_dict(o)
        elif type(o) in (int, float, str, bytes, NoneType):
            if o in keys:
                o = replace
            return o
        else:
            raise ValueError(o)

    try:
        result = json.dumps(source, allow_nan=False, indent=indent)
    except ValueError:
        result = json.dumps(go_check(source), allow_nan=False, indent=indent)
    return result


utility_package = {
    'extract_cookies_str_to_jar': extract_cookies_str_to_jar,
    'current_time': current_time,
}


@contextmanager
def js_session(source, timeout=None, engine=None):
    from requester.request import jsruntime

    worker = get_config(SECTION_WORKER, 'jsruntime')

    timeout = timeout or worker.get('timeout')
    if not engine:
        engine = jscaller.engine.JSEngine(
            name=worker['name'],
            source=worker['source'],
            shell=worker['shell'],
            version=worker['version'],
            encoding='utf-8',
        )

    if os.path.isfile(source):
        session = jscaller.session
    else:
        session = jscaller.Session
    with session(source, timeout, engine) as sess:
        yield sess
        req = jsruntime(sess)
        task = req.start_request()
        result = task.result()
        return result


REG_VALID_PATHNAME = re.compile(r'[\\/:*?"<>|\r\n]+')