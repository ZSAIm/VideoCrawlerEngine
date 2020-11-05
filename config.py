import json
import os
from contexts import glb
from tempfile import TemporaryDirectory


SECTION_WORKER = 'worker'
SECTION_BASIC = 'basic'
SECTION_SCRIPT = 'script'

# 已注册的脚本
REGISTERED_SCRIPT = {
    # 'base.py': '',
    'bilibili.py': '',
    # 'fake.py': '',
}

# 用户配置
BASIC_CONFIG = {
    'trust_unverified': False,
    'storage_dir': 'mp4',
    'tempdir': '',
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
        'active': None,
        'default_rule': 1,
        'to_format': ['.mp4'],
        'starter': ['start'],
        'append': ['convert', 'cleanup'],
        # 'savedir': 'bilibili',
        'remove_tempdir': True,
    },
    'fake': {
        'order': 9999,
        'cookies': '',
        'proxies': None,
        'active': None,
        'default_rule': 1,
        'target_format': ['.mp4'],
        'append': ['convert', 'cleanup'],
        'rm_tempdir': True,
    },
    # global 全局配置
    None: {
        'tempdir': '',
        'to_format': '.mp4',
        'savedir': '',
    }
}


WORKER_CONFIG = {
    'task': {
        'max_concurrent': 3,
        'tempdir': '',
        'type': 'async',
    },
    'script': {
        'max_concurrent': 3,
        'type': 'thread',
    },
    'download': {
        'engine': 'Nbdler',
        'max_concurrent': 5,
        'max_speed': None,
        'timeout': None,
        'max_retries': 10,
        'type': 'async',
    },
    'ffmpeg': {
        'engine': 'ffmpeg',
        'max_concurrent': 5,
        'source': r'',
        'name': 'ffmpeg',
        'overwrite': True,
        'type': 'async',
    },
    'convert': {
        'engine': 'ffmpeg',
        'max_concurrent': None,
        'type': 'async',
    },
    'jsruntime': {
        'engine': 'NodeJS',
        'max_concurrent': 2,
        'name': 'node',
        'source': '',
        'version': None,
        'shell': False,
        'type': 'thread',
    },

    'cleanup': {
        'engine': None,
        'max_concurrent': None,
        'type': 'async',
    },
    'stop': {
        'max_concurrent': 10,
        'entrypoint': 'submit',
        'type': 'thread',
    },
}

CONFIG_JSON = {
    SECTION_BASIC: BASIC_CONFIG,
    SECTION_WORKER: WORKER_CONFIG,
    SECTION_SCRIPT: SCRIPT_CONFIG,

}


def get_config(section, field=None):
    """
    Get the configuration value of the given section.

    Args:
        section: (dict): write your description
        field: (str): write your description
    """
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
        'active': None,
        'default_rule': 1,
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
        writeback()

    with open('config.json', 'r', encoding='utf-8') as fp:
        CONFIG_JSON = json.load(fp)

    config = dict(SCRIPT_CONFIG[None])
    if not config['tempdir']:
        config['tempdir'] = TemporaryDirectory().name
    glb['config'].enter(config)


def writeback():
    """ 配置回写。"""
    global CONFIG_JSON
    with open('config.json', 'w', encoding='utf-8') as fp:
        json.dump(CONFIG_JSON, fp, indent=4, ensure_ascii=False)


def script_config(script_name=None):
    """
    Get a script configuration.

    Args:
        script_name: (str): write your description
    """
    return get_config(SECTION_SCRIPT, script_name)


def basic_config(key):
    """
    Get a config key.

    Args:
        key: (str): write your description
    """
    return get_config(SECTION_BASIC, key)
