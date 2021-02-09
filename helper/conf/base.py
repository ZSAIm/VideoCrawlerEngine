
from configparser import ConfigParser
from typing import Any, Union, Dict
from collections import namedtuple
from urllib.parse import urlparse, ParseResult
import re
import os

_REG_FILESIZE = re.compile(r'([\d.]+)([a-zA-Z]+)?')

_NAME_CONF = {}


Item = namedtuple('Item', 'value loader')


class ItemLoader(object):
    tag: str

    def __init__(
        self, *,
        title: str = '',
        desc: str = '',
        tag: str = None,
        disabled: bool = False
    ):
        self.title = title
        self.desc = desc
        self.disabled = disabled
        if tag is not None:
            self.tag = tag

    def load(self, origin: str) -> Any:
        raise NotImplementedError

    def dump(self, value: Any) -> str:
        return '' if value is None else str(value)

    def validation(self) -> Dict:
        raise NotImplementedError


def get_conf(__name: str):
    return _NAME_CONF[__name]


def iter_conf():
    return iter(_NAME_CONF.items())


class ConfSection(object):
    __items__: Dict[str, Item] = {}

    def __init__(self, name: str, items: Dict[str, Item]):
        self.__items__ = items
        self.__section_name__ = name
        self.__history__ = {}

    def __getattr__(self, item):
        result = self.__items__[item]
        return result.value

    __getitem__ = __getattr__

    def __repr__(self):
        items = '\n'.join([f'{k}: {v.__class__.__name__} = {v.value}' for k, v in self.__items__.items()])
        return f"""[{self.__section_name__}]\n{items}"""

    def get(self, k, default=None):
        return self.__items__.get(k, Item(value=default, loader=None)).value

    def __iter__(self):
        for k, v in self.__items__.items():
            yield k, v.value

    items = __iter__

    def keys(self):
        return self.__items__.keys()

    def values(self):
        for k, v in self.__items__.items():
            yield v.value

    def __setitem__(self, key, value):
        """ 配置会话管理。 """
        type_conv = self.__items__[key].loader
        self.__history__[key] = type_conv.dump(value)

    def __setattr__(self, key, value):
        if key.startswith('__') and key.endswith('__'):
            object.__setattr__(self, key, value)
        else:
            type_conv = self.__items__[key].loader
            self.__history__[key] = type_conv.dump(value)

    def get_loader(self, key):
        return self.__items__[key].loader

    def get_field(self, key):
        item = self.__items__[key]
        loader = item.loader
        value = item.value
        if type(value) not in (int, str, list, tuple, dict, float, set, bool) or (
            value in (float('inf'), float('-inf'), float('nan'))
        ):
            value = loader.dump(value)
        return {
            'name': key,
            'title': loader.title,
            'desc': loader.desc,
            'tag': loader.tag,
            'disabled': loader.disabled,
            'value': value,
            'validation': loader.validation(),
            'extra': {}
        }


def conf_loader(parser: ConfigParser, loaders: dict):
    sections = {}
    basetype_convertor = {
        int: Integer(),
        str: String(),
        float: Float(),
        bool: Boolean(),
    }
    for sec_name, sec in parser.items():
        if sec_name == parser.default_section and not len(sec.keys()):
            continue
        items = {}
        for k in sec.keys():
            ty = loaders.get(k, None)
            if ty:
                conv = basetype_convertor.get(ty, None)
                if not conv:
                    conv = ty
                if not isinstance(conv, ItemLoader):
                    raise TypeError(f'item的{type(ty)}类型无法处理。')
                try:
                    value = conv.load(sec.get(k))
                except ValueError:
                    value = None
            else:
                conv = String()
                value = sec.get(k)

            items[k] = Item(value=value, loader=conv)
        sections[sec_name] = ConfSection(sec_name, items)
    return sections


class ConfMeta(type):
    def __new__(mcs, mcs_name, mcs_bases, mcs_namespace, **kwargs):
        file = kwargs['file']
        confname = kwargs['name']
        # 加载配置文件
        parser = ConfigParser()
        result = parser.read(file, encoding='utf-8')
        new_namespace = mcs_namespace.copy()

        # 标注类型
        annotations = mcs_namespace.get('__annotations__', {})
        annotations.update(mcs_namespace.get('__items__', {}))
        sections = conf_loader(parser, annotations)

        def __getitem__(self, item):
            return sections[item]

        def items(self):
            return sections.items()

        def keys(self):
            return sections.keys()

        def values(self):
            return sections.values()

        def get(self, k, default=None):
            return sections.get(k, default)

        def reload(self):
            conf_loader(parser, annotations)

        def commit(self):
            """ 配置回写。"""
            nonlocal sections
            cnt = 0
            for k0, v0 in items(self):
                for k1, v1 in v0.__history__.items():
                    parser[k0][k1] = v1
                    cnt += 1
                # 清空历史修改记录
                v0.__history__.clear()

            if cnt > 0:

                with open(file, 'w', encoding='utf-8') as f:
                    parser.write(f)

                # 重新加载配置文件
                sections = conf_loader(parser, annotations)

        new_namespace.update({
            '__conf_parser__': parser,
            '__sections__': sections,
            '__getitem__': __getitem__,
            '__getattr__': __getitem__,
            'commit': commit,
            'reload': reload,
            'items': items,
            'keys': keys,
            'values': values,
            'get': get,
        })
        new_namespace.update(sections)
        cls = super().__new__(
            mcs,
            mcs_name,
            mcs_bases,
            new_namespace
        )
        _NAME_CONF[confname] = cls
        return cls

    __getitem__ = object.__getattribute__


class String(ItemLoader):
    tag: str = 'TextField'

    def load(self, origin: str) -> str:
        return origin

    def validation(self) -> Dict:
        return {
            'type': 'string',
        }


class Integer(ItemLoader):
    tag: str = 'TextField'

    def __init__(
        self,
        min_value: int = None,
        max_value: int = None,
        **kwargs
    ):
        self.min = min_value
        self.max = max_value
        super().__init__(**kwargs)

    def load(self, origin: str) -> Union[int, float]:
        if origin == 'inf':
            return float('inf')
        return int(origin)

    def validation(self) -> Dict:
        return {
            'min': self.min,
            'max': self.max,
            'type': 'number',
        }


class Float(ItemLoader):
    tag: str = 'TextField'

    def load(self, origin: str) -> float:
        return float(origin)

    def validation(self) -> Dict:
        return {
            'type': 'number',
        }


class Boolean(ItemLoader):
    tag: str = 'Switches'

    def load(self, origin: str) -> bool:
        return ConfigParser.BOOLEAN_STATES[origin]

    def dump(self, value: bool) -> str:
        return 'yes' if value else 'no'

    def validation(self) -> Dict:
        return {
            'type': 'number',
        }


class List(ItemLoader):
    tag: str = 'Combobox'

    def __init__(self, sep: str = ',', **kwargs):
        super().__init__(**kwargs)
        self.sep = sep

    def load(self, origin: str) -> list:
        return origin.split(self.sep)

    def dump(self, value: list) -> str:
        return self.sep.join(value)

    def validation(self) -> Dict:
        return {
            'type': 'array',
        }


class FileSize(ItemLoader):
    """ 文件大小格式化。"""
    tag: str = 'TextField'

    def load(self, origin: str) -> float:
        size, fm = _REG_FILESIZE.search(origin.strip()).groups()
        size = float(size)

        scale = {
            'g': 1024 * 1024 * 1024,
            'gb': 1024 * 1024 * 1024,
            'm': 1024 * 1024,
            'mb': 1024 * 1024,
            'k': 1024,
            'kb': 1024,
            'b': 1,
            '': 1
        }[(fm or '').lower()]
        return size * scale

    def dump(self, value: Union[int, float]) -> str:
        scale = {
            1024 * 1024 * 1024: 'g',
            1024 * 1024: 'm',
            1024: 'k',
            1: 'b'
        }
        for k, v in scale.items():
            if value >= k:
                if value % k == 0:
                    return f'{int(value / k)}{v}'
        return str(value)

    def validation(self) -> Dict:
        return {
            'type': 'number',
        }


class UrlParse(ItemLoader):
    tag: str = 'TextField'

    def load(self, origin: str) -> ParseResult:
        return urlparse(origin)

    def dump(self, value: Union[ParseResult, str]) -> str:
        if isinstance(value, ParseResult):
            return value.geturl()
        elif isinstance(value, str):
            return value
        elif value is None:
            return ''
        raise TypeError(f'不支持的类型{type(value)}。')

    def validation(self) -> Dict:
        return {
            'type': 'string',
        }


class FileRealPath(ItemLoader):
    tag: str = 'TextField'

    def load(self, origin: str) -> str:
        return os.path.realpath(origin)

    def validation(self) -> Dict:
        return {
            'type': 'string',
        }

