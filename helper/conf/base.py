
from configparser import ConfigParser
from typing import Any

_NAME_CONF = {}


def get_conf(name: str):
    return _NAME_CONF[name]


class ConfSection(object):
    def __init__(self, name: str, items: dict):
        self.__section_name__ = name
        self.__items__ = items

    def __getattr__(self, item):
        return self.__items__[item]

    __getitem__ = __getattr__

    def __repr__(self):
        items = '\n'.join([f'{k} = {v}' for k, v in self.__items__.items()])
        return f"""[{self.__section_name__}]\n{items}"""

    def get(self, k, default=None):
        return self.__items__.get(k, default)

    def __iter__(self):
        return iter(self.__items__.items())

    def keys(self):
        return self.__items__.keys()

    def values(self):
        return self.__items__.values()


class ConfMeta(type):
    def __new__(mcs, mcs_name, mcs_bases, mcs_namespace, **kwargs):
        file = kwargs['file']
        confname = kwargs['name']
        # 加载配置文件
        parser = ConfigParser()
        result = parser.read(file)
        new_namespace = mcs_namespace.copy()

        # 标注类型
        annotations = mcs_namespace.get('__annotations__', {})
        annotations.update(mcs_namespace.get('__items__', {}))
        sections = {}
        for sec_name, sec in parser.items():
            if sec_name == parser.default_section and not len(sec.keys()):
                continue
            items = {}
            for k in sec.keys():
                ty = annotations.get(k, None)
                if ty:
                    basetype_convert = {
                        int: Integer(),
                        str: String(),
                        float: Float(),
                        bool: Boolean(),
                    }
                    conv = basetype_convert.get(ty, None)
                    if not conv:
                        conv = ty
                    if not isinstance(conv, ItemType):
                        raise TypeError(f'item的{type(ty)}类型无法处理。')
                    try:
                        value = conv(sec.get(k))
                    except ValueError:
                        value = None
                else:
                    value = sec.get(k)

                items[k] = value
            sections[sec_name] = ConfSection(sec_name, items)

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

        new_namespace.update({
            '__conf_parser__': parser,
            '__sections__': sections,
            '__getitem__': __getitem__,
            '__getattr__': __getitem__,
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


class ItemType(object):
    def __call__(self, origin: str) -> Any:
        raise NotImplementedError


class String(ItemType):
    def __call__(self, origin: str) -> str:
        return origin


class Integer(ItemType):
    def __call__(self, origin: str) -> int:
        return int(origin)


class Float(ItemType):
    def __call__(self, origin: str) -> float:
        return float(origin)


class Boolean(ItemType):
    def __call__(self, origin: str) -> bool:
        return ConfigParser.BOOLEAN_STATES[origin]


class List(ItemType):
    def __init__(self, sep=','):
        self.sep = sep

    def __call__(self, origin: str) -> list:
        return list(origin.split(self.sep))
