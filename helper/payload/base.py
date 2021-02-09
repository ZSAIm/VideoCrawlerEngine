from abc import ABCMeta
from typing import (
    Tuple,
    Any,
    Dict
)
import inspect
from binascii import crc32
import re

_SIGN_PAYLOAD = {}
_NAME_PAYLOAD = {}


class PayloadMeta(ABCMeta):
    def __new__(mcs, mcs_name, mcs_bases, mcs_namespace):
        new_namespace = {
            '__constructor__': None,
            '__decorated__': None,
        }
        new_namespace.update(mcs_namespace)

        new_namespace.update({
            'SIGN': property(fget=lambda *_: sign),
        })

        cls = super().__new__(
            mcs,
            mcs_name,
            mcs_bases,
            new_namespace,
        )
        try:
            sign = inspect.getsource(cls)
            constructor = cls
        except OSError:
            # 使用修饰器创建的payload类
            sign = inspect.getsource(cls.__decorated__)
            constructor = cls.__constructor__

        sign = f"{crc32(sign.encode('utf-8')):x}"
        _SIGN_PAYLOAD[sign] = constructor
        _NAME_PAYLOAD[cls.NAME] = constructor
        return cls


class BasePayload(object, metaclass=PayloadMeta):
    NAME: str = 'base'
    SIGN: str

    __args__: Tuple
    __kwargs__: Dict

    def __new__(cls, *args, **kwargs) -> Any:
        inst = object.__new__(cls)
        inst.__args__ = args
        inst.__kwargs__ = kwargs
        return inst


class IgnoreObjectPayload(
    BasePayload,
    # metaclass=PayloadMeta
):
    NAME = 'object'

    def __init__(self, obj):
        self.repr = repr(obj)


class OtherPayload(
    BasePayload,
    # metaclass=PayloadMeta
):
    NAME = 'other'

    def __init__(self, o):
        pass


def get_payload_by_sign(sign):
    return _SIGN_PAYLOAD.get(sign)


def get_payload_by_name(name):
    return _NAME_PAYLOAD.get(name)