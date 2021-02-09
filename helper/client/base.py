
from fastapi.routing import APIRoute
import requests
from requests import Session
from urllib.parse import urljoin

from exception import ClientResponseError
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


def register_client(name, factory):
    _NAME_CLIENTS[name] = factory


class APIRequestMethod:
    METHODS = {'post', 'get'}

    def __init__(
        self,
        parent: Any,
        session: Session,
        gateway: str,
        path: str,
        methods: Sequence[str] = (),
        response_model: Optional[Type[Any]] = None,
        description: str = None,
        hooks: List = None,
        doc: str = None,
    ):
        self.parent = parent
        self.session = session
        self.gateway = gateway
        self.api = path
        self.methods = {m.lower() for m in methods}
        self.description = description
        self.response_model = response_model
        self.hooks = hooks

        self.request_methods = {
            m: lambda kwargs: self._request_agent(m, kwargs)
            if m in methods else method_not_allowed
            for m in self.METHODS
        }

    def _responder(self, resp: requests.Response):
        res_json = resp.json()
        if res_json['code'] != SUCCESS:
            raise ClientResponseError(res_json['code'], res_json['msg'])
        if self.parent._raw:
            return res_json
        return res_json['data']

    def _post(
        self,
        params: Optional[dict] = None,
        headers: Optional[dict] = None,
        cookies: Optional[dict] = None,
    ):
        if self.parent._headers:
            headers = self.parent._headers
        if self.parent._cookies:
            cookies = self.parent._cookies

        resp = self.session.post(
            url=urljoin(self.gateway, self.api),
            json=params,
            headers=headers,
            cookies=cookies,
            timeout=self.parent._timeout,
            proxies=self.parent._proxies,
            verify=self.parent._verify
        )
        if self.response_model:
            return self._responder(resp)
        return resp.json()

    def _get(
        self,
        params: Optional[dict] = None,
        headers: Optional[dict] = None,
        cookies: Optional[dict] = None,
    ):
        if self.parent._headers:
            headers = self.parent._headers
        if self.parent._cookies:
            cookies = self.parent._cookies

        resp = self.session.get(
            url=urljoin(self.gateway, self.api),
            params=params,
            headers=headers,
            cookies=cookies,
            timeout=self.parent._timeout,
            proxies=self.parent._proxies,
            verify=self.parent._verify
        )
        if self.response_model:
            return self._responder(resp)
        return resp.json()

    def _request_agent(self, method, params):
        def next_hook(p, *args):
            exc = None
            try:
                hook = hooks.popleft()
            except IndexError:
                try:
                    result = self.__getattribute__(f'_{method}')(p, *args)
                    return result, exc
                except Exception as err:
                    exc = ClientResponseError(-1, str(err), exc)
                    return None, exc
            else:
                h = hook(self, p, *args)

                p, *args = next(h)
                result, exc = yield from next_hook(p, *args)
                if exc:
                    try:
                        h.throw(exc)
                    except StopIteration as e:
                        # 异常被捕获处理
                        result = e.value
                        exc = None
                    except:
                        # 异常未经处理交由下一个迭代器处理
                        pass
                else:
                    try:
                        h.send(result)
                    except StopIteration as r:
                        result = r.value
                    else:
                        # 只允许使用一次的yield
                        raise RuntimeError
                return result, exc

        hooks = deque(self.hooks)
        if self.parent._hook:
            hooks.appendleft(self.parent._hook)
        try:
            next(next_hook(params, None, None))
        except StopIteration as r:
            res, exc = r.value
            if exc:
                # 最外层迭代器将抛出异常
                raise exc
            return res
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
        def api_factory(r, h):
            def _request(self):
                return APIRequestMethod(
                    parent=self,
                    session=session,
                    gateway=get_conf('app')[server_name]['gateway'].geturl(),
                    path=r.path,
                    methods=r.methods,
                    doc=r.endpoint.__doc__,
                    description=r.description,
                    response_model=r.response_model,
                    hooks=h
                )
            return _request

        client_name = kwargs['name']
        if APIBaseClient not in mcs_bases:
            mcs_bases += (APIBaseClient,)
        server_name = client_name
        module_path = f'app.{server_name}.app'
        before_keys = set(sys.modules.keys())
        # module = __import__(module_path).app
        module = import_module(module_path)
        diff_keys = set(sys.modules.keys()).difference(before_keys)
        session = requests.Session()

        # 调试模式
        # session.proxies = {
        #     'http': '127.0.0.1:8888',
        #     'https': '127.0.0.1:8888',
        # }
        new_namespace = mcs_namespace.copy()

        outer = mcs_namespace.get('__outer__', None)
        inner = mcs_namespace.get('__inner__', None)
        default = mcs_namespace.get('__default__', None)

        for route in module.app.routes:
            # 跳过非自定义API路由
            if not isinstance(route, APIRoute):
                continue

            hooks = [h for h in [
                outer,
                mcs_namespace.get(route.name, default),
                inner,
            ] if h]

            new_namespace[route.name] = property(api_factory(route, hooks))
            # new_namespace[route.name] = property(lambda self: APIRequestMethod(
            #     parent=self,
            #     session=session,
            #     gateway=get_conf('app')[server_name]['gateway'].geturl(),
            #     path=route.path,
            #     methods=route.methods,
            #     doc=route.endpoint.__doc__,
            #     description=route.description,
            #     response_model=route.response_model,
            #     hooks=hooks
            # ))

        for k in diff_keys:
            del sys.modules[k]

        cls = super().__new__(
            mcs,
            mcs_name,
            mcs_bases,
            new_namespace,
        )
        register_client(client_name, cls)
        return cls


class APIBaseClient:
    def __init__(
        self,
        headers=None,
        cookies=None,
        timeout=None,
        proxies=None,
        verify=None,
        raw=False,
        hook=None,
    ):
        self._timeout = timeout
        self._headers = headers
        self._cookies = cookies
        self._proxies = proxies
        self._verify = verify
        self._raw = raw
        self._hook = hook
