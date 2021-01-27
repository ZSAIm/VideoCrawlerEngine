"""
==================================
Name:       Bilibili 爬虫脚本
Author:     ZSAIM
Created:    2020-03-05
Recently Update:      
Version:    0.1
License:    Apache-2.0
==================================
"""
from app.script import ScriptBaseClass
from request.download import download, stream_download
from request.ffmpeg import ffmpeg
from request import option, optional
from helper.payload import export_func, Concurrent
from helper.ctxtools import ctx
from urllib.parse import urljoin, urlsplit
from request.live import live_daemon
import bs4
import json
import re

reg_playinfo = re.compile(
    r'<script>.*?window\.__playinfo__\s*=(?:[(?:\s/\*).*?(?:\*/)\s])*(.*?)</script>'
)

reg_initial_state = re.compile(
    r'<script>.*?window\.__INITIAL_STATE__\s*=(.*?);(\(function\s*\(\s*\)\s*\{.*?)?</script>'
)

dash_params = {
    'avid': None,
    'cid': None,
    'qn': None,   # quality
    'type': '',
    'otype': 'json',
    'fnver': '0',
    'fnval': '16',
    'session': None
}

durl_params = {
    'avid': None,
    'cid': None,
    'qn': None,   # quality
    'type': '',
    'otype': 'json',
    'fnver': '0',
    'fnval': '0',
    'session': None

}

HEADERS = {
    'User-Agent': ('Mozilla/5.0 (Windows NT 6.1; Win64; x64) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36'),
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
}


class Bilibili(ScriptBaseClass):
    name = 'bilibili'
    version = '0.1'
    author = 'ZSAIM'
    created_date = '2020/03/05'

    supported_domains = ['www.bilibili.com']
    quality_ranking = [116, 80, 74, 64, 32, 16]

    def _init(self):
        self.html_res = None
        self.html_parse = None

    def run(self):
        splitresult = urlsplit(self.url)
        scheme, netloc, path, query, fragment = splitresult
        bvid = path.strip('/').split('/')[-1]
        self.view_detail(bvid)

        html_res = self.request_get(self.url, headers=dict(HEADERS))
        # 汇报处理情况。
        if html_res.status_code != 200:
            ctx.error('%s %s: %s' % (html_res.status_code, html_res.reason, html_res.url))
        else:
            ctx.success('%s %s: %s' % (html_res.status_code, html_res.reason, html_res.url))

        # 上传标题
        html_parse = bs4.BeautifulSoup(html_res.text, features='html.parser')
        ctx.upload(title=html_parse.find('h1').text)

        playinfo = self.parse_playinfo(html_res) or {}
        initial_state = self.parse_initial_state(html_res) or {}

        #
        if not initial_state:
            raise ValueError('initial_state参数无法正确解析。')
        if initial_state.get('videoData'):
            aid = initial_state['videoData']['aid']
            cid = initial_state['videoData']['cid']
        elif initial_state.get('epInfo'):
            aid = initial_state['epInfo']['aid']
            cid = initial_state['epInfo']['cid']
        else:
            raise ValueError('参数aid, cid未找到。')

        # 是否分页
        videos_p = initial_state['videoData']['videos']
        if videos_p > 1:
            # 获取分p列表
            pagelist_res = self.api_pagelist(aid)
            page_cids = [d['cid'] for d in pagelist_res['data']]
        else:
            page_cids = [cid]

        request_params = {
            'avid': aid,
            'cid': cid,
            'qn': self.quality,
            'session': playinfo.get('session', '')
        }

        results = []
        for cid in page_cids:
            request_params['cid'] = cid
            # api: playurl
            result = self.api_playurl(request_params)
            results.append(optional(result))

        ctx.upload(items=results)

    def view_detail(self, bvid):
        """
        https://api.bilibili.com/x/web-interface/view/detail
        Params:
            bvid=
            aid=
            need_operation_card=
            web_rm_repeat=
            jsonp=
            callback=
        """
        url = 'https://api.bilibili.com/x/web-interface/view/detail'
        params = {
            'bvid': bvid,
            'aid': '',
            'need_operation_card': 1,
            'web_rm_repeat': '',
            'jsonp': 'json'

        }
        resp = self.request_get(url=url, params=params, headers=dict(HEADERS))
        resp.json()

    def api_playurl(self, request_params):
        """ api: https://api.bilibili.com/x/player/playurl
        这一接口获得的视频资源属于
        """
        options = []
        headers = dict(HEADERS)
        headers['Referer'] = self.url
        r = dict(dash_params)
        r.update(request_params)
        api_res = self.api_get('https://api.bilibili.com/x/player/playurl?', r)
        data = api_res['data']
        # dash
        dash = data.get('dash')

        if dash:
            # audio 选项
            audio = optional([
                download(uri=audio['base_url'], headers=headers)
                for audio in dash['audio']
            ])
            # v
            time_length = data['timelength'] / 1000
            for v in dash['video']:
                video_dl = download(uri=v['base_url'], headers=headers)
                item_req = ffmpeg.concat_av([video_dl, audio])

                frame_rate = v['frame_rate'].split('/')
                if len(frame_rate) > 1:
                    frame_rate = int(frame_rate[0]) / int(frame_rate[1])
                else:
                    frame_rate = frame_rate[0]
                size = None
                video_desc = {
                    'length': time_length,
                    'size': size,
                    'quality': v['id'],
                    'width': v['width'],
                    'height': v['height'],
                    'frame_rate': frame_rate,
                    'mime_type': v['mime_type'],
                }

                # 发送成功解析到视频的消息，并带上资源信息
                ctx.success('quality: %s\nresolution: %s x %s\nsize: %s\nurl: %s' % (
                    v['id'], v['width'], v['height'], size, v['base_url']
                ))
                options.append(
                    option(item_req, descriptions=video_desc)
                )
        # durl
        r = dict(durl_params)
        r.update(request_params)
        api_res = self.api_get('https://api.bilibili.com/x/player/playurl?', r)
        durl = api_res.get('data', {}).get('durl')
        if durl:
            for v in durl:
                video_dl = download(uri=v['url'], headers=headers)
                item_req = video_dl
                # 不需要合并操作使用none 方法, 或着接提交下载请求
                ctx.success('quality: %s\nresolution: %s x %s\nsize: %s\nurl: %s' % (
                    request_params['qn'], 'unknown', 'unknown', v['size'], v['url']
                ))
                options.append(option(item_req, descriptions=v))

        return options

    def playlist(self, aid):
        """ api: https://api.bilibili.com/x/player/pagelist?aid=%s&jsonp=jsonp
        分p列表
        """
        request_params = {
            'aid': aid,
            'jsonp': 'jsonp'
        }
        api_res = self.api_get('https://api.bilibili.com/x/player/pagelist?', request_params)
        return api_res

    def api_pagelist(self, aid):
        """ api: https://api.bilibili.com/x/player/pagelist?aid=%s&jsonp=jsonp
        分p列表
        """
        request_params = {
            'aid': aid,
            'jsonp': 'jsonp'
        }
        api_res = self.api_get('https://api.bilibili.com/x/player/pagelist?', request_params)
        if api_res['code'] != 0:
            raise ValueError('分p列表返回错误。message: %s' % api_res['message'])
        return api_res

    @staticmethod
    def parse_playinfo(html_res):
        # 解析 window.__playinfo__
        res_playinfo = reg_playinfo.search(html_res.text)
        if res_playinfo is None:
            raise ValueError(res_playinfo)
        playinfo = json.loads(res_playinfo.group(1))
        return playinfo

    @staticmethod
    def parse_initial_state(html_res):
        # 解析 window.__INITIAL_STATE__
        res_initial_state = reg_initial_state.search(html_res.text)
        if reg_initial_state is None:
            raise ValueError(reg_initial_state)
        initial_state = json.loads(res_initial_state.group(1))
        return initial_state


class BilibiliLive(ScriptBaseClass):
    name = 'bilibili-live'
    version = '0.1'
    author = 'ZSAIM'
    created_date = '2020/06/19'

    supported_domains = ['live.bilibili.com']
    quality_ranking = [10000, 400, 250, 150, 100, 80, 0]

    def run(self):
        """__NEPTUNE_IS_MY_WAIFU__"""

        splitresult = urlsplit(self.url)
        scheme, netloc, path, query, fragment = splitresult
        room_id = path.strip('/')
        if not room_id.isnumeric():
            raise TypeError(f'url输入不正确，得到room_id为：{room_id}')

        # 获取直播间信息
        self.live_room(room_id)

        # 直播持久化取流
        ctx.upload(item=live_daemon(
            # lambda: self.get_live(room_id)
            export_func(lambda: self.get_live(room_id))
        ))

    def live_room(self, room_id):
        """ 直播间信息。"""
        api = 'https://api.live.bilibili.com/xlive/web-room/v1/index/getInfoByRoom'
        params = {
            'room_id': room_id,
        }
        headers = dict(HEADERS)
        headers.update({
            'Referer': self.url
        })

        resp = self.request_get(api, params=params, headers=headers)
        resp_json = resp.json()
        data = resp_json['data']
        room_info = data['room_info']
        anchor_info = data['anchor_info']
        ctx.upload(
            title=room_info['title'],
            uid=room_info['uid'],
            live_start_time=room_info['live_start_time'],
            area_name=room_info['area_name'],

            upname=anchor_info['base_info']['uname']
        )

    def get_live(self, room_id):
        """
        api: https://api.live.bilibili.com/xlive/web-room/v2/index/getRoomPlayInfo?
        Params:
            room_id=910819
            &protocol=0%2C1
            &format=0%2C2
            &codec=0
            &qn=10000
            &platform=web
            &ptype=16
        """
        api = 'https://api.live.bilibili.com/xlive/web-room/v2/index/getRoomPlayInfo'
        params = {
            'room_id': room_id,
            'protocol': '0,1,2',
            # 'format': '0,1,2',
            'format': '0,1',
            'codec': '0',
            'qn': '10000',
            'platform': 'web',
            'ptype': '16'
        }
        headers = dict(HEADERS)
        headers.update({
            'Referer': self.url
        })

        resp = self.request_get(api, params=params, headers=headers)
        resp_json = resp.json()
        data = resp_json['data']
        ctx.upload(
            room_id=room_id,
            live_status=data['live_status'],
            live_time=data['live_time'],
        )

        self.live_room(room_id)

        # 直播状态
        if data['live_status'] == 0:
            # 未开播
            raise ValueError('直播未开。')
        elif data['live_status'] == 1:
            # 已开播
            pass
        playurl_info = data['playurl_info']
        playurl = playurl_info['playurl']
        # streams = playurl['stream']

        options = []
        for stream in playurl['stream']:
            for format in stream['format']:
                format_name = format['format_name']
                for codec in format['codec']:
                    current_qn = codec['current_qn']
                    qn_desc = [
                        qn['desc']
                        for qn in playurl['g_qn_desc'] if qn['qn'] == current_qn
                    ][0]
                    desc = {
                        'format': format_name,
                        'quality': qn_desc,
                        'qn': current_qn,
                    }

                    uris = []
                    for url_info in codec['url_info']:
                        urlpath = codec['base_url'] + url_info['extra']
                        url = urljoin(url_info['host'], urlpath)
                        uris.append(url)

                    options.append(option(
                        stream_download(uris.pop(), headers=headers),
                        descriptions=desc
                    ))

        return optional(options)


if __name__ == '__main__':
    # 重载基类
    from app.script import ScriptBaseClass

    # bilibili = Bilibili.test('https://www.bilibili.com/video/av91721893', 100)
    # bilibili = Bilibili.test('https://www.bilibili.com/video/BV167411E7Tn', 100)
    # bilibili = Bilibili.test('https://www.bilibili.com/video/BV1sK411p7vg', 100)
    # bilibili = Bilibili.test('https://www.bilibili.com/video/BV14p4y1D7r7', 100)
    # print(bilibili)

    # live = BilibiliLive.test('https://live.bilibili.com/910819', 100)
    # live = BilibiliLive.test('https://live.bilibili.com/697', 100)
    # live = BilibiliLive.test('https://live.bilibili.com/2523257', 100)
    live = BilibiliLive.test('https://live.bilibili.com/4404024', 100)
    print(live)