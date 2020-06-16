
from _request import (Option, Optional, requester, Request, _is_related_types, RE_VALID_PATHNAME)
from utils import concat_abcde, mktemp
from script import select_script, supported_script, get_script
from config import get_basic
from nbdler import Request as DlRequest, dlopen, HandlerError
from subprocess import list2cmdline
from nbdler.uri import URIs
from debugger import dbg
import asyncio
import shutil
import os
import re

TEMP_PREFIX = re.compile(r'(?:(?:\d+)-)*\d+')


def next_script(url, descriptions=None, **kwargs):
    """ 下一个脚本请求。 """
    return Option(script_request(url, discard_next=True, **kwargs),
                  descriptions)


@requester('jsruntime')
def jsruntime(session, **kwargs):
    session.leave()


@requester('convert', weight=0.5)
async def convert():
    from requester import ffmpeg
    results = []

    merges = dbg.flow.find_by_name('ffmpeg')
    for pathname in [merge.get_data('pathname') for merge in merges]:
        results.append(pathname)

    if not results:
        # 对于没有经过ffmpeg处理的工具，默认将下载的音频资源全经过
        downloads = dbg.flow.find_by_name('download')
        for filename in [dl.get_data('pathname') for dl in downloads]:
            converter = ffmpeg.convert(filename)
            node = dbg.flow.attach_node(converter)
            result = await node.start_request()
            results.append(converter.get_data('pathname'))

    # 修改文件名并移动文件
    storage_dir = dbg.root_info['storage_dir']
    # 当文件多于一个的时候在存储目录添加一级目录
    new_dir = os.path.join(os.path.realpath(storage_dir), dbg.root_info['title'])
    n = dbg.root_info['n']
    if n > 1:
        if not os.path.isdir(new_dir):
            os.mkdir(new_dir)
        storage_dir = new_dir

    for pathname in results:
        path, name = os.path.split(pathname)
        dst_name = name.split('.', 1)[-1]
        if n > 1:
            dst_name = f'{dbg.flow.b:03}.{dst_name}'
        dst_pathname = os.path.join(os.path.realpath(storage_dir), dst_name)
        shutil.move(pathname, dst_pathname)


@requester('cleanup', weight=0.3)
async def cleanup():
    if dbg.root_info['remove_tempdir']:
        tempdir = dbg.root_info['tempdir']
        tempfiles = []
        cur_b = dbg.flow.b
        for name in os.listdir(tempdir):
            rex = TEMP_PREFIX.search(name)
            if not rex:
                continue
            a, b, c, d, *e = rex.group(0).split('-')
            if int(b) == cur_b:
                tempfiles.append(os.path.join(tempdir, name))

        for tempfile in tempfiles:
            try:
                os.unlink(tempfile)
            except:
                pass


@requester('download', bases_cls=(Request, URIs), sketch_data=('size', ), weight=2)
async def download(**kwargs):
    self = dbg.__self__

    temp = mktemp()
    rq = DlRequest(file_path=temp.pathname, max_retries=dbg.config['max_retries'])
    for uri in self.dumps():
        uri.pop('id')
        rq.put(**uri)

    exception = None

    async with dlopen(rq) as dl:
        dbg.upload(
            size=dl.file.size,
            pathname=dl.file.pathname,
        )
        dbg.set_percent(dl.percent_complete)
        dbg.set_timeleft(dl.remaining_time)
        dbg.set_speed(lambda: dl.transfer_rate())

        dl.start(loop=asyncio.get_running_loop())
        while not dl._future:
            await asyncio.sleep(0.01)

        # 添加请求停止器
        dbg.add_stopper(dl.pause)
        async for exception in dl.aexceptions():
            dbg.warning(exception.exc_info)
            if isinstance(exception, HandlerError):
                await dl.apause()
                break
        else:
            exception = None
        await dl.ajoin()

    if exception:
        # 若发生异常，抛出异常
        raise exception from exception.exception

    # 更新文件信息
    dbg.upload(
        pathname=dl.file.pathname,
        size=dl.file.size,
    )


@download.initializer
def _download_init(req):
    URIs.__init__(req)
    kwargs = req.kwargs
    if kwargs:
        req.put(**kwargs)


@requester('ffmpeg')
async def ffmpeg(inputs, callable_cmd, **kwargs):
    from requester.ffmpeg import FFmpegEngine

    def input2pathname(input):
        if isinstance(input, str):
            return input
        elif _is_related_types(input):
            return input.get_data('pathname')
        assert input

    def percent():
        nonlocal time_length, _ffmpeg
        return _ffmpeg.length() * 100 / (time_length or float('info'))

    time_length = dbg.root_info.get_data('length', None)

    temp = mktemp(dbg.root_info['to_format'])

    inputs = inputs
    if not isinstance(inputs, (list, tuple, set)):
        inputs = [inputs]

    cmd = callable_cmd(
        inputs=[input2pathname(input) for input in inputs],
        output=temp.pathname,
        **kwargs
    )

    source = os.path.join(dbg.config['source'], dbg.config['name'])

    if isinstance(cmd, (list, tuple)):
        cmd = [source] + list(cmd)
        cmd = list2cmdline(cmd)
    else:
        cmd = f'{source} ' + cmd

    if dbg.config['overwrite']:
        cmd += ' -y'

    process = await asyncio.create_subprocess_shell(
        cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _ffmpeg = FFmpegEngine(process)
    dbg.set_speed(_ffmpeg.speed)
    dbg.set_percent(percent)

    dbg.upload(
        cmd=cmd,
        pathname=temp.pathname
    )

    await _ffmpeg.run(timeout=dbg.config.get('timeout', None))


@requester('script', root=True)
def script_request(url, rule=None, script=None, *, discard_next=False, **kwargs):
    if script is None:
        name = select_script(supported_script(url))
        script = get_script(name)
        script = script

    script_config = script.config

    if rule is None:
        rule = script_config.get('selection_rule')
    qn = script.quality_ranking
    quality = qn[max(0, round((100 - rule) * len(qn) / 100) - 1)]

    # 请求来源脚本请求
    dbg.upload(
        url=url,
        name=script.name,
        script=script,
        rule=rule,
        quality=quality
    )

    # 创建并运行脚本
    script(url, quality, discard_next=discard_next).run()

    # 合法文件路径
    origin_title = dbg.get_data('title')
    title = RE_VALID_PATHNAME.sub('_', origin_title)

    # 创建临时目录
    tempdir = os.path.join(dbg.config['tempdir'],
                           script.name,
                           title)
    tempdir = os.path.realpath(tempdir)

    storage_dir = os.path.join(get_basic('storage_dir'), script_config['storage_dir'], script.name)

    items = dbg.get_data('items', [])
    dbg.upload(
        title=title,
        tempdir=tempdir,
        storage_dir=storage_dir,
        remove_tempdir=script_config.get('remove_tempdir', True),
        to_format=script_config.get('to_format', ['.mp4'])[0],
        n=len(items),
    )

    return items


