from functools import wraps
from debugger import dbg
from utils import PipeStreamHandler
from datetime import datetime
from requester.request import ffmpeg
import time
import re
import os


class FFmpegEngine(PipeStreamHandler):
    RE_STEP = re.compile(r'\b(\w+)=\s*([-\+\w\.:/]+)\s*')
    RE_DONE = re.compile(r'\b([\w\s]+):\s*([-\+\w\.:/%]+)\s*')
    RE_SIZE = re.compile(r'(\d+)([a-zA-Z]+)')
    RE_START = re.compile(r'\s*Press\s*\[q\]\sto\s*stop,\s*\[\?\]\s*for\s*help\s*')
    RE_META = re.compile(r'Metadata\s*:((\s*(\b\w+)\s*:\s*([^\n])+\n)+)')
    RE_INOUT = re.compile(r"""(?:Input|Output)\s*#(\d+)\s*,\s*(\w+)\s*,\s*(?:from|to)\s*['"](.*?)['"]:""")

    def __init__(self, process):
        super().__init__(process)
        self._started = False
        self._fulltext = ''
        self._info = {}
        self._step = {}

    def speed(self):
        return self._step.get('speed', 'unknown')

    def size(self):
        return self._step.get('size', 0)

    def length(self):
        return self._step.get('time', 0)

    def bitrate(self):
        return self._step.get('bitrate', 'unknown')

    def fps(self):
        return self._step.get('fps', 'unknown')

    async def _stream_handler(self, stream_id, line):
        if isinstance(line, bytes):
            line = line.decode('utf-8')
        if not self._started:
            # start flag
            res = self.RE_START.search(line)
            self._started = bool(res)
        else:
            # step progress
            keyword = {k: v for k, v in self.RE_STEP.findall(line)}

            if all([i in keyword for i in ('bitrate', 'time', 'frame', 'fps')]):
                # Lsize = size
                keyword['size'] = keyword.get('size', keyword.get('Lsize'))

                tm = datetime.strptime(keyword['time'], '%H:%M:%S.%f')
                time_length = tm.hour * 3600 + tm.minute * 60 + tm.second + tm.microsecond / 1e6
                # 格式化尺寸大小
                res_size = self.RE_SIZE.search(keyword['size'])
                size = int(res_size[1]) * {
                    'B': 1,
                    'KB': 1024,
                    'MB': 1024 * 1024,
                    'GB': 1024 * 1024 * 1024,
                }.get(res_size.group(2).lower(), 1)

                self._step.update({
                    'size': size,
                    'time': time_length,
                    'speed': keyword.get('speed'),
                    'bitrate': keyword.get('bitrate', '').strip(),
                    'fps': keyword.get('fps', '').strip()
                })
            else:
                desc = {}
                for k, v in self.RE_DONE.findall(line):
                    desc[k] = v
                self._info.update(desc)


def ffmpeg_operator(func):
    @wraps(func)
    def wrapper(inputs, **kwargs):
        return ffmpeg(inputs, callable_cmd=func, **kwargs)

    # FFmpeg操作方法添加到ffmpeg请求器
    setattr(ffmpeg, func.__name__, wrapper)
    return wrapper


@ffmpeg_operator
def cmdline(inputs, output, cmd, input_getter=None):
    if input_getter is None:
        return cmd.format(*inputs, output=output)
    else:
        return cmd.format(inputs=input_getter(inputs), output=output)


@ffmpeg_operator
def concat_av(inputs, output):
    video, audio = inputs
    cmd = ['-i', f'{video}',
           '-i', f'{audio}',
           '-vcodec', 'copy', '-acodec', 'copy',
           f'{output}']
    return cmd


@ffmpeg_operator
def concat_demuxer(inputs, output):
    tempdir = dbg.root_info['tempdir']
    tempfile = os.path.join(tempdir, f'{hex(time.time_ns())}.txt')
    concat_input = '\n'.join([f'file \'{input}\'' for input in inputs])

    with open(tempfile, 'w') as f:
        f.write(concat_input)

    cmd = ['-f', 'concat', '-safe', '0',
           '-i', f'{tempfile}', '-c', 'copy', f'{output}']
    return cmd


@ffmpeg_operator
def concat_protocol(inputs, output):
    concat_input = '|'.join(inputs)
    cmd = ['-i', f'concat:\'{concat_input}\'', '-c copy', f'{output}']
    return cmd


@ffmpeg_operator
def convert(inputs, output, h265=False):
    input, *_ = inputs
    cmd = ['-i', input, '-y', '-qscale', '0', '-vcodec', 'libx264', output]
    return cmd