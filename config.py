import json
import os

SECTION_WORKER = 'worker'
SECTION_BASIC = 'basic'
SECTION_SCRIPT = 'script'

# 已注册的脚本
REGISTERED_SCRIPT = {
    # 'base.py': '',
    'bilibili.py': ''
}

# 用户配置
BASIC_CONFIG = {
    # 'preload': True,
    'safe_script': False,
    'storage_dir': '',
    'tempdir': 'temp',
    'auto_select': True,
    'to_format': '.mp4',
    'registered': REGISTERED_SCRIPT,
}


SCRIPT_CONFIG = {
    'base': {
        # 脚本优先级, 数值越小，优先级越高
        # 当多个脚本能够解析同一个域的时候，使用优先级高的脚本进行处理。
        'order': 100,
        'cookies': '',
        'proxies': None,
        'active_version': None,
        'selection_rule': 100,
        'to_format': ['.mp4'],
        'starter': ['start'],
        'append': ['convert', 'cleanup'],
        'storage_dir': 'bilibili',
        'remove_tempdir': True,
    }
}


WORKER_CONFIG = {
    'task': {
        'engine': None,
        'max_concurrent': 3,
        'timeout': None,
        'async': True,
    },
    'script': {
        'engine': None,
        'max_concurrent': 3,
        'timeout': None,
        'tempdir': 'temp',

    },
    'download': {
        'engine': 'Nbdler',
        'max_concurrent': 5,
        'max_speed': None,
        'timeout': None,
        'async': True,
    },
    'ffmpeg': {
        'engine': 'ffmpeg',
        'max_concurrent': 2,
        'timeout': None,
        'source': r'',
        'name': 'ffmpeg',
        'overwrite': True,
        'async': True,
    },
    'convert': {
        'engine': 'ffmpeg',
        'max_concurrent': None,
        'timeout': None,
        'async': True,
    },

    'jsruntime': {
        'engine': 'NodeJS',
        'max_concurrent': 2,
        'timeout': None,
        'name': 'node',
        'source': '',
        'version': None,
        'shell': False,
    },

    'cleanup': {
        'engine': None,
        'max_concurrent': None,
    },
    'error': {
        'engine': None,
        'max_concurrent': None,
    }

}

CONFIG_JSON = {
    SECTION_BASIC: BASIC_CONFIG,
    SECTION_WORKER: WORKER_CONFIG,
    SECTION_SCRIPT: SCRIPT_CONFIG,

}


def get_config(section, field=None):
    global CONFIG_JSON
    section = CONFIG_JSON.get(section)
    if field:
        return section.get(field, None)
    return section


def new_script_config():
    """ 创建空的脚本配置。"""
    return {
        'order': 100,
        'cookies': '',
        'proxies': None,
        'active_version': None,
        'selection_rule': 100,
        'to_mimetype': ['.mp4'],
        'starter': ['start'],
        'append': ['convert', 'cleanup'],
        'storage_dir': '',
        'remove_tempdir': True,
        'error_handler': ['error']
    }


def load_config():
    """ 加载配置文件。"""
    global CONFIG_JSON
    # 系统配置
    if not os.path.isfile('config.json'):
        write_config()

    with open('config.json', 'r', encoding='utf-8') as fp:
        CONFIG_JSON = json.load(fp)


def write_config():
    """ 配置回写。"""
    global CONFIG_JSON
    with open('config.json', 'w', encoding='utf-8') as fp:
        json.dump(CONFIG_JSON, fp, indent=4, ensure_ascii=False)


def get_script_config(script_name=None):
    return get_config(SECTION_SCRIPT, script_name)


def get_basic(key):
    return get_config(SECTION_BASIC, key)
