from requester.base import (requester, Request, _is_related_types, CallableData)
from uitls import REG_VALID_PATHNAME
from script import select_script, supported_script, get_script
from nbdler import Request as DlRequest, dlopen, HandlerError
from subprocess import list2cmdline
from nbdler.uri import URIs
import debugger as dbg
import time
import asyncio
import shutil
import os


@requester('jsruntime')
def jsruntime(session, **kwargs):
    """
    Implements.

    Args:
        session: (todo): write your description
    """
    session.leave()


@requester('convert', weight=0.5)
async def convert():
      """
      Convert all audio files in the db.

      Args:
      """
    from requester import ffmpeg

    merges = dbg.glb.task.find_by_name('ffmpeg')

    results = [merge.get_data('filepath') for merge in merges]
    if not results:
        # 对于没有经过ffmpeg处理的工具，转换所有的音视频文件
        downloads = dbg.glb.task.find_by_name('download')
        for filename in [dl.get_data('filepath') for dl in downloads]:
            converter = ffmpeg.convert(filename)
            await converter.start_request()
            results.append(converter.get_data('filepath'))

    # 修改文件名并移动文件
    savedir = os.path.realpath(dbg.glb.config['savedir'])
    # 当文件多于一个的时候在存储目录添加一级目录
    n = dbg.glb.script['n']
    if n > 1:
        savedir = os.path.join(os.path.realpath(savedir), dbg.glb.script['title'])
        if not os.path.isdir(savedir):
            os.makedirs(savedir)

    for filepath in results:
        name = os.path.basename(filepath)
        name = name.split('.', 1)[-1]
        if n > 1:
            name = f'{dbg.b :03}.{name}'
        dst_pathname = os.path.join(savedir, name)
        shutil.move(filepath, dst_pathname)


@requester('cleanup', weight=0.3)
async def cleanup():
    """ 清楚临时文件。 """
    dbg.tempdir.rmfiles(True)


class DownloadRequester(Request, URIs):
    NAME = 'download'

    def __init__(self, uri=None, headers=None, **kwargs):
        """
        Make a put request.

        Args:
            self: (todo): write your description
            uri: (str): write your description
            headers: (list): write your description
        """
        Request.__init__(self)
        URIs.__init__(self)
        if uri:
            self.put(uri, headers, **kwargs)

    async def end_request(self):
          """
          Perform a request.

          Args:
              self: (todo): write your description
          """
        temp = dbg.tempdir.mktemp()
        req = DlRequest(file_path=temp.filepath)
        for uri in self.dumps():
            uri.pop('id')
            req.put(**uri)

        async with dlopen(req) as dl:
            dbg.upload(
                size=dl.file.size,
                filepath=dl.file.pathname,
            )
            dbg.set_percent(dl.percent_complete)
            dbg.set_timeleft(dl.remaining_time)
            dbg.set_speed(lambda: dl.transfer_rate())

            dl.start(loop=asyncio.get_running_loop())
            # FIX: Nbdler 下载器在协程下出现的问题
            while not dl._future:
                await asyncio.sleep(0.01)

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
            filepath=dl.file.pathname,
            size=dl.file.size,
        )


download = DownloadRequester


@requester('ffmpeg')
async def ffmpeg(inputs, callable_cmd, cal_len, **kwargs):
    """ FFMPEG 驱动引擎。"""
    from requester.ffmpeg import FFmpegStreamHandler, cal_total_length

    def input2pathname(input):
        """
        Convert input to a pathname.

        Args:
            input: (todo): write your description
        """
        if isinstance(input, str):
            return input
        elif _is_related_types(input):
            return input.get_data('filepath')
        assert input

    def percent():
        """
        Returns the percentage of the given length.

        Args:
        """
        nonlocal time_length, f
        return f.complete_length() * 100 / (time_length or float('inf'))

    time_length = dbg.glb.script.get('length', float('inf'))
    temp = dbg.tempdir.mktemp(dbg.glb.config['to_format'])

    inputs = inputs
    if not isinstance(inputs, (list, tuple, set)):
        inputs = [inputs]

    cmd = await callable_cmd(
        inputs=[input2pathname(input) for input in inputs],
        output=temp.filepath,
        **kwargs
    )
    if cal_len and time_length in (float('inf'), None):
        # 总长度计算
        time_length = await cal_total_length(inputs)
        dbg.upload(length=time_length)
    source = os.path.join(dbg.config['source'], dbg.config['name'])

    if isinstance(cmd, (list, tuple)):
        cmd = [source] + list(cmd)
        cmd = list2cmdline(cmd)
    else:
        cmd = f'{source} ' + cmd

    if dbg.config['overwrite']:
        cmd += ' -y'
    print(cmd)

    process = await asyncio.create_subprocess_shell(
        cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    f = FFmpegStreamHandler(process)
    dbg.set_speed(f.speed)
    dbg.set_percent(percent)

    dbg.upload(
        cmd=cmd,
        filepath=temp.filepath,
        input=CallableData(f.get_inputs),
        output=CallableData(f.get_outputs),
    )

    await f.run(timeout=dbg.config.get('timeout', None))


@requester('script', root=True)
def fake_script(request_items, rule, **options):
    """ (调试模式) 调试模式下的虚假脚本请求Root。"""
    from script import ScriptTask, new_script_config
    from script.base import ScriptBaseClass

    url = 'http://fake.script'
    script = ScriptTask(ScriptBaseClass, new_script_config())('')
    dbg.upload(
        url=url,
        name=script.name,
        script=script,
        rule=rule,
        quality=100,
        title=f'debug_{time.time() * 1000}',
        tempdir=dbg.glb.config['tempdir'],
        n=1,
        config=script.config,
    )
    dbg.upload(**options)
    dbg.upload(items=[request_items])
    return dbg.get_data('items')


@requester('script', root=True)
def script_request(url, rule=None, script=None, *, dismiss=False, **kwargs):
    """
    Create a script.

    Args:
        url: (str): write your description
        rule: (todo): write your description
        script: (str): write your description
        dismiss: (todo): write your description
    """
    if script is None:
        name = select_script(supported_script(url))
        script = get_script(name)
        script = script

    if rule is None:
        rule = script.config.get('default_rule')
    qn = script.quality_ranking
    quality = qn[max(0, round((100 - rule) * len(qn) / 100) - 1)]

    # 请求来源脚本请求
    dbg.upload(
        url=url,
        name=script.name,
        script=script,
        rule=rule,
        quality=quality,
        config=script.config,
    )

    # 创建并运行脚本
    script(url, quality, dismiss=dismiss, **kwargs).run()

    # 合法文件路径
    title = REG_VALID_PATHNAME.sub('_', dbg.get_data('title'))

    # 创建临时目录
    tempdir = os.path.realpath(os.path.join(
        dbg.glb.config['tempdir'],
        script.name,
        title
    ))

    items = dbg.get_data('items', [])
    dbg.upload(
        title=title,
        tempdir=tempdir,
        n=len(items),
    )

    return items
