
from fastapi.routing import APIRoute
import requests
from requests import Session
from urllib.parse import urljoin
from helper.conf import get_conf
from typing import Sequence, Optional, Type, Any, List
from helper.codetable import SUCCESS
from importlib import import_module
from collections import deque
import sys

_NAME_CLIENTS = {}


def get_client(name):
    return _NAME_CLIENTS.get(name)


def method_not_allowed(*args, **kwargs):
    """ 方法不允许。"""
    raise NotImplementedError('不允许的方法。')


class ClientResponseError(Exception):
    pass


class APIRequestMethod:
    METHODS = {'post', 'get'}

    def __init__(
        self,
        session: Session,
        gateway: str,
        path: str,
        methods: Sequence[str] = (),
        response_model: Optional[Type[Any]] = None,
        description: str = None,
        agents: List = None,
        doc: str = None,
    ):
        self.session = session
        self.gateway = gateway
        self.api = path
        self.methods = {m.lower() for m in methods}
        self.description = description
        self.response_model = response_model
        self.agents = agents

        self.request_methods = {
            m: lambda kwargs: self._request_agent(m, kwargs)
            if m in methods else method_not_allowed
            for m in self.METHODS
        }

    def _unpack_model_response(self, resp: requests.Response):
        res_json = resp.json()
        if res_json['code'] != SUCCESS:
            raise ClientResponseError(res_json['msg'])
        return res_json['data']

    def _post(
        self,
        params: Optional[dict] = None,
        headers: Optional[dict] = None,
        cookies: Optional[dict] = None,
    ):
        resp = self.session.post(
            url=urljoin(self.gateway, self.api),
            json=params,
            headers=headers,
            cookies=cookies,
        )
        if self.response_model:
            return self._unpack_model_response(resp)
        return resp.json()

    def _get(
        self,
        params: Optional[dict] = None,
        headers: Optional[dict] = None,
        cookies: Optional[dict] = None,
    ):
        resp = self.session.get(
            url=urljoin(self.gateway, self.api),
            params=params,
            headers=headers,
            cookies=cookies,
        )
        if self.response_model:
            return self._unpack_model_response(resp)
        return resp.json()

    def _request_agent(self, method, params):
        def next_agent(p, *args):
            try:
                agent = agents.popleft()
            except IndexError:
                result = self.__getattribute__(f'_{method}')(p, *args)
                return result
            else:
                h = agent(self, p, *args)

                p, *args = next(h)
                result = yield from next_agent(p, *args)
                try:
                    h.send(result)
                except StopIteration as r:
                    result = r.value
                else:
                    raise RuntimeError
                return result

        agents = deque(self.agents)
        try:
            next(next_agent(params, None, None))
        except StopIteration as r:
            return r.value
        raise RuntimeError

    def __getattr__(self, item):
        return self.request_methods[item]

    def __call__(self, **kwargs):
        if len(self.methods) != 1:
            raise RuntimeError(f'该接口多于一种请求方法，请指定调用: {self.methods}')
        for m in self.methods:
            return self._request_agent(m, kwargs)


class APIClientMeta(type):
    def __new__(mcs, mcs_name, mcs_bases, mcs_namespace, **kwargs):
        client_name = kwargs['name']

        server_name = client_name
        module_path = f'app.{server_name}.app'
        before_keys = set(sys.modules.keys())
        # module = __import__(module_path).app
        module = import_module(module_path)
        diff_keys = set(sys.modules.keys()).difference(before_keys)
        session = requests.Session()

        # 调试模式
        session.proxies = {
            'http': '127.0.0.1:8888',
            'https': '127.0.0.1:8888',
        }
        new_namespace = mcs_namespace.copy()

        outer = mcs_namespace.get('__outer__', None)
        inner = mcs_namespace.get('__inner__', None)
        default = mcs_namespace.get('__default__', None)

        for route in module.app.routes:
            # 跳过非自定义API路由
            if not isinstance(route, APIRoute):
                continue

            agents = [h for h in [
                outer,
                mcs_namespace.get(route.name, default),
                inner,
            ] if h]
            new_namespace[route.name] = APIRequestMethod(
                session=session,
                gateway=get_conf('app')[server_name]['gateway'].geturl(),
                path=route.path,
                methods=route.methods,
                doc=route.endpoint.__doc__,
                description=route.description,
                response_model=route.response_model,
                agents=agents
            )

        for k in diff_keys:
            del sys.modules[k]

        cls = super().__new__(
            mcs,
            mcs_name,
            mcs_bases,
            new_namespace,
        )
        _NAME_CLIENTS[client_name] = cls
        return cls

