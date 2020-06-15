# -*- coding: UTF-8 -*-
"""
==================================
Name:       Base 爬虫基类
Author:     ZSAIM
Created:    2020-03-05
Recently Update:
Version:    0.0
License:    Apache-2.0
==================================
"""

from utils import extract_cookies_str_to_jar
from script import ScriptBaseClass as BaseClass
import requests

TIMEOUT = 10


class ScriptBaseClass(BaseClass):
    """ 爬虫脚本基类。继承基类 BaseClass
    :class variable
        name:               名称
        version:            版本
        supported_domains:  支持的域
    """
    name = 'base'
    version = 0.0
    author = 'ZSAIM'
    created_date = '2020/03/05'
    license = 'Apache-2.0'

    quality_ranking = []
    supported_domains = []

    def __init__(self, config, url, quality, **options):
        """
        :param
            guard:  脚本监控对象
            url:    要处理的URL
            config: 爬虫脚本配置信息
        """
        # 从配置中读入cookies。
        cookies = config.get('cookies', '')
        cookies = extract_cookies_str_to_jar(cookies)
        self.url = url
        self.cookies = cookies
        self.config = config
        if quality is None:
            quality = config.get('default_quality', None)
        self.quality = quality
        # requests 会话。
        self.session = requests.session()
        self.options = options
        self._init()

    def _init(self):
        """ 自定义初始化。"""

    def request(self, method, url, **kwargs):
        """ 处理URL资源。具体参数参考方法 requests.Session.request()。"""
        # cookies参数
        self.cookies.update(kwargs.pop('cookies', {}))
        kwargs['cookies'] = self.cookies
        # timeout参数。
        timeout = kwargs.pop('timeout', TIMEOUT)
        kwargs['timeout'] = timeout
        return self.session.request(method, url, **kwargs)

    def request_get(self, url, **kwargs):
        return self.request('GET', url, **kwargs)

    def request_post(self, url, **kwargs):
        return self.request('POST', url, **kwargs)

    def run(self):
        raise NotImplementedError

    def quick_glance(self):
        """ 快速粗略获取必要的数据。
        至少上传数据:
            title:  处理的标题
        """
        raise NotImplementedError

    def api_get(self, url, request_params, otype='auto'):
        """ api json 请求。 """
        request_query = '&'.join(['%s=%s' % (k, v) for k, v in request_params.items()])
        request_url = url.rstrip('?') + '?' + request_query
        resp = self.request_get(request_url)
        if otype in ('json', 'auto'):
            try:
                return resp.json()
            except Exception:
                pass
        return resp.text

    def __repr__(self):
        return '<CrawlerScript %s-%s>' % (self.name, self.version)


if __name__ == '__main__':
    pass
