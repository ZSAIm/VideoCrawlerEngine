import json
from binascii import crc32
from json.encoder import JSONEncoder
from typing import Any, Dict

from .base import get_payload_by_sign
from .base import PayloadMeta, OtherPayload, BasePayload


class PayloadJSONEncoder(JSONEncoder):
    def default(self, o: Any) -> Any:
        if type(type(o)) is PayloadMeta:
            pass
        else:
            o = OtherPayload(id(o))
        return parse_payload(o)


def parse_payload(
    payload: BasePayload
) -> Dict[str, Any]:
    def _encode(o):
        if type(type(o)) is PayloadMeta:
            return parse_payload(o)
        elif isinstance(o, (list, tuple, set)):
            return [_encode(i) for i in o]
        elif isinstance(o, dict):
            return {_encode(k): _encode(v) for k, v in o.items()}
        return o

    return {
        'name': payload.NAME,
        'sign': payload.SIGN,
        'id': f'{crc32(str(id(payload)).encode("utf-8")):x}',
        'data': {
            'args': [_encode(arg) for arg in payload.__args__],
            'kwargs': {k: _encode(v) for k, v in payload.__kwargs__.items()}
        },
    }


def unparse_payload(
    pldict: Dict,
    idpls: Dict = None
):
    def undictify_kwargs(o):
        return {k: undictify_payload(v, idpls) for k, v in o.items()}

    def undictify_args(o):
        return [undictify_payload(arg, idpls) for arg in o]

    if idpls is None:
        idpls = {}
    keys = ['name', 'sign', 'data', 'id']
    dif_keys = set(keys).difference(set(pldict.keys()))
    if dif_keys:
        raise RuntimeError(f'无法解析该字典，缺少 {dif_keys} 键。')
    name, sign, data, _id = [pldict[n] for n in keys]
    payload_cls = get_payload_by_sign(sign)
    if not payload_cls:
        raise RuntimeError('找不到该payload，请检查是否有加载该payload。')
    if payload_cls.NAME != name:
        raise RuntimeError(f'找不到匹配的payload: {name}')
    unspecified_args = data['kwargs'].pop('__unspecified_args__', ())
    unspecified_kwargs = data['kwargs'].pop('__unspecified_kwargs__', {})
    # args = [undictify_payload(arg, idpls) for arg in data['args']]
    # kwargs = {k: undictify_payload(v, idpls) for k, v in data['kwargs'].items()}
    args = undictify_args(data['args'])
    kwargs = undictify_kwargs(data['kwargs'])
    unspecified_args = undictify_args(unspecified_args)
    unspecified_kwargs = undictify_kwargs(unspecified_kwargs)
    args.extend(unspecified_args)
    kwargs.update(unspecified_kwargs)
    if _id in idpls:
        return idpls[_id]
    payload = payload_cls(*args, **kwargs)
    idpls[_id] = payload
    return payload


def undictify_payload(
    o: Any,
    idpls: Dict = None
) -> Any:
    if idpls is None:
        idpls = {}
    if isinstance(o, (list, tuple, set)):
        return [undictify_payload(i, idpls) for i in o]
    elif isinstance(o, dict):
        try:
            return unparse_payload(o, idpls)
        except RuntimeError:
            return {k: undictify_payload(v, idpls) for k, v in o.items()}
    else:
        return o


def dictify_payload(obj):
    """ 通过JSONEncoder简单处理JSON序列化对象问题。 """
    data = json.dumps(
        obj, cls=PayloadJSONEncoder
    )
    return json.loads(data)


