from typing import List, Union, Callable, Dict
from helper.payload.request import requester
from .helper.ffmpeg import FfmpegStreamHandler
from helper.ctxtools import ctx
from subprocess import list2cmdline
from utils.model import DefaultField
from pydantic import BaseModel
from datetime import datetime
from functools import wraps
from helper.payload import (
    Requester,
    Optional,
    Option,
)
from utils.common import jsonify
import asyncio
import os


class FfmpegDataModel(BaseModel):
    cmd: str = DefaultField(title='ffmpeg执行命令')
    dstpath: str = DefaultField(title='输出文件路径')
    input: Callable[..., Dict] = DefaultField(title='输入流信息')
    output: Callable[..., Dict] = DefaultField(title='输出流信息')


@requester('ffmpeg', infomodel=FfmpegDataModel)
async def ffmpeg(
    inputs: Union[List[str], str],
    cmd_operator: str,
    cal_len,
    **kwargs
):
    """ ffmpeg 数据流处理引擎。"""

    def get_input_filepath(inp) -> str:
        if isinstance(inp, str):
            return inp
        elif isinstance(inp, (Requester, Optional, Option)):
            return inp.getdata('dstpath')
        assert inp

    def percent():
        nonlocal time_length, f
        return f.complete_length() * 100 / (time_length or float('inf'))

    time_length = ctx.glb.script['length'] or float('inf')
    temp = ctx.tempdir.mktemp(ctx.glb.config['to_format'][0])

    inputs = inputs
    if not isinstance(inputs, (list, tuple, set)):
        inputs = [inputs]

    # 通过命令操作符名称获取被修饰的函数进行生成ffmpeg命令
    cmd = await getattr(ffmpeg, cmd_operator).__wrapped__(
        inputs=[get_input_filepath(input) for input in inputs],
        output=temp.filepath,
        **kwargs
    )
    if cal_len and time_length in (float('inf'), None):
        # 总长度计算
        time_length = await cal_total_length(inputs)
        ctx.upload(length=time_length)
    source = os.path.join(ctx.config['source'], ctx.config['name'])

    if isinstance(cmd, (list, tuple)):
        cmd = [source] + list(cmd)
        cmd = list2cmdline(cmd)
    else:
        cmd = f'{source} ' + cmd

    if ctx.config['overwrite']:
        cmd += ' -y'
    print(cmd)

    process = await asyncio.create_subprocess_shell(
        cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    f = FfmpegStreamHandler(process)
    ctx.set_speed(f.speed)
    ctx.set_percent(percent)

    ctx.upload(
        cmd=cmd,
        dstpath=temp.filepath,
        input=f.get_inputs,
        output=f.get_outputs,
    )
    ctx.add_stopper(f.stop_threadsafe)
    await f.run(timeout=ctx.config.get('timeout', None), close_stdin=False)


def ffmpeg_operator(func=None, *, cal_len=True):
    if func is None:
        def wrapper(func):
            return ffmpeg_operator(
                func,
                cal_len=cal_len
            )
    else:
        @wraps(func)
        def wrapper(inputs, **kwargs):
            return ffmpeg(
                inputs,
                cmd_operator=func.__name__,
                cal_len=cal_len,
                **kwargs
            )

        setattr(ffmpeg, func.__name__, wrapper)
    return wrapper


@ffmpeg_operator
async def cmdline(inputs: List, output: str, cmd: str, input_getter=None):
    if input_getter is None:
        return cmd.format(*inputs, output=output)
    else:
        return cmd.format(inputs=input_getter(inputs), output=output)


@ffmpeg_operator
async def concat_av(inputs: List, output: str):
    video, audio = inputs
    cmd = ['-i', f'{video}',
           '-i', f'{audio}',
           '-vcodec', 'copy', '-acodec', 'copy',
           f'{output}']
    return cmd


@ffmpeg_operator
async def concat_demuxer(inputs: List, output: str):
    tempfile = ctx.tempdir.mktemp('.txt')
    concat_input = '\n'.join([f'file \'{input}\'' for input in inputs])

    with tempfile.open('w') as f:
        f.write(concat_input)

    cmd = ['-f', 'concat', '-safe', '0',
           '-i', f'{tempfile.filepath}', '-c', 'copy', f'{output}']
    return cmd


@ffmpeg_operator
async def concat_protocol(inputs: List, output: str):
    concat_input = '|'.join(inputs)
    cmd = ['-i', f'concat:\'{concat_input}\'', '-c', 'copy', f'{output}']
    return cmd


@ffmpeg_operator(cal_len=False)
async def information(inputs: List, **options):
    cmd = []
    for inp in inputs:
        cmd.extend(['-i', inp])

    return cmd


@ffmpeg_operator
async def concat_m3u8(inputs, output, **options):
    cmd = await concat_demuxer(inputs, output).end_request()
    return cmd


@ffmpeg_operator(cal_len=False)
async def m3u8download(
    inputs: List,
    output: str,
    user_agent: str = ('Mozilla/5.0 (Windows NT 6.1; Win64; x64) '
                       'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36'),
    headers: dict = None,
    **options
):
    """ m3u8文件下载。"""
    headers = headers or {}
    cmd = ['-user_agent', f'"{user_agent}"']
    # 设置参数
    headers_params = []
    for k, v in headers.items():
        if v is True:
            v = ''

        headers_params.extend([f'-{k}', v])
    if headers_params:
        cmd.append('-headers')
        cmd.extend(headers_params)

    # 设置输入链接
    for inp in inputs:
        cmd.extend(['-i', f'"{inp}"'])

    # 设置输出路径
    cmd += ['-c', 'copy', output]
    cmd = ' '.join(cmd)
    return cmd


async def cal_total_length(inputs, **options):
    """ 视频长度批量计算。"""
    info = information(inputs)
    await info.end_request()
    all_inputs = info.getdata('input', {})
    length = 0
    for input in all_inputs:
        for stream in input.get('streams', []):
            for s in stream['streams']:
                if s['type'] == 'video':
                    has_video = True
                    break
            else:
                has_video = False

            # 仅在stream有video的时候时间才进行累加计算。
            if has_video:
                duration = datetime.strptime(stream['duration'], '%H:%M:%S.%f')
                length += (
                    duration.hour * 3600 +
                    duration.minute * 60 +
                    duration.second +
                    duration.microsecond * 1e-6
                )
    return length


@ffmpeg_operator
async def convert(inputs, output, h265=False):
    input, *_ = inputs
    cmd = ['-i', input, '-y', '-qscale', '0', '-vcodec', 'libx264', output]
    return cmd


@ffmpeg_operator
async def fast_convert(inputs, output):
    """ flv to mp4 ultrafast but not safe."""
    inp, *_ = inputs
    cmd = ['-i', inp, '-vcodec', 'copy', '-acodec', 'copy', output]
    return cmd
