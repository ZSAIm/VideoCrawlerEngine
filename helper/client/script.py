
from helper.client.base import APIClientMeta
from helper.payload import undictify_payload
from exception import RemoteApplyException
from helper.ctxtools import ctx
import json


class ScriptClient(
    name='script',
    metaclass=APIClientMeta
):
    def __outer__(
        self,
        params: dict,
        headers: dict,
        cookies: dict,
    ):
        def test_json(o):
            if isinstance(o, (str, int, float, type(None))):
                return True
            elif isinstance(o, (dict, list, tuple, set)):
                try:
                    json.dumps(o)
                except (json.JSONDecodeError, TypeError):
                    return False
                else:
                    return True
            return False
        cookies = cookies or {}
        # ctx.__scope__.get()
        json_contexts = {
            k: v
            for k, v in ctx.__scope__.get().items()
            if test_json(v)
        }
        cookies.update(
            context=json.dumps(json_contexts)
        )
        result = yield params, headers, cookies
        return undictify_payload(result)

    def remote_apply(
        self,
        params: dict,
        headers: dict = None,
        cookies: dict = None,
    ):
        result = yield params, headers, cookies
        if result['exc']:
            raise RemoteApplyException(
                result['key'],
                result['funcid'],
                result['context'],
                result['ret'],
                result['exc'],
            )
        return result
