import json
import re
from datetime import datetime
from binascii import crc32
from requests.cookies import RequestsCookieJar, create_cookie
import os
from hashlib import sha256
NoneType = type(None)


def current_time():
    """ 返回 '时:分:秒' 格式的当前时间文本。"""
    return datetime.now().strftime('%H:%M:%S.%f')


def extract_cookies_str_to_jar(
    cookies_str,
    cookiejar=None,
    overwrite=True,
    cookies_specified_kw=None
):
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


def cookiejar_from_dict(
    cookie_dict,
    cookiejar=None,
    overwrite=True,
    cookies_specified_kw=None
):
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


def jsonify(
    source,
    replace=None,
    keys=(float('nan'), float('inf'), float('-inf')),
    indent=None
):
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

REG_SAFETY_FILENAME = re.compile(r'[\\/:*?"<>|\r\n& ]+')


def safety_filename(origin):
    """ 文件路径合理化。"""
    return REG_SAFETY_FILENAME.sub('_', origin)


def cat_a5g(a5g, cat_str='-'):
    return cat_str.join([
        str(i) if not isinstance(i, tuple) else cat_a5g(i)
        for i in a5g if i != ()
    ])


def gen_sign(content: str, encoding='utf-8'):
    return f'{crc32(content.encode(encoding)):x}'


def readable_file_size(byte_size, precise=3):
    unitdict = {
        'GB': 1024 * 1024 * 1024,
        'MB': 1024 * 1024,
        'KB': 1024,
        'B': 1,
    }
    for k, v in unitdict.items():
        if byte_size > v:
            return f'{round(byte_size / v, precise)} {k}'
    return f'{round(byte_size / v, precise)} B'


def gen_token() -> str:
    return sha256(os.urandom(32)).hexdigest()