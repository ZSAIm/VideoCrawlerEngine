
from urllib.parse import urljoin, urlunsplit, urlsplit
from starlette.requests import Request
from fastapi.responses import Response
from typing import Sequence
import aiohttp
import re


class ReverseProxyMiddleware:
    session: aiohttp.ClientSession = None

    def __init__(self, proxy_configures: Sequence):
        sources = sorted(
            [config['source'] for config in proxy_configures],
            key=lambda x: len(x),
            reverse=True
        )
        pattern = f"^({'|'.join(sources)})\\b(.*)"
        self.match_pattern = re.compile(pattern)
        self.source_proxy = {
            config['source']: urlsplit(config['pass'])
            for config in proxy_configures
        }

    async def __call__(self, request: Request, call_next):
        scheme, netloc, path, query, fragment = urlsplit(str(request.url))
        res = self.match_pattern.match(path)
        if res:
            match_source, rest_path = res.groups()
            scheme, netloc, path, *_ = self.source_proxy[match_source]
            url = urlunsplit((scheme, netloc, urljoin(path, rest_path), query, fragment))
            response = await self.responder(request, url)
        else:
            response = await call_next(request)

        return response

    async def responder(self, request: Request, new_url: str):
        if self.session is None:
            self.session = aiohttp.ClientSession()
        resp = await self.session.request(
            request.method,
            url=new_url,
            headers=request.headers,
            cookies=request.cookies,
            data=await request.body(),
            # proxy='http://127.0.0.1:8888'
        )
        headers = resp.headers.copy()
        dismiss_keys = [
            'date', 'server',
        ]
        for key in dismiss_keys:
            headers.pop(key, None)
        return Response(
            content=await resp.content.read(),
            status_code=resp.status,
            # multidict supported
            headers=headers,
            media_type=resp.content_type,
        )
