import asyncio
from typing import Optional
import chardet
from functools import partial

STREAM_OUT = 1
STREAM_ERROR = 2


class PipeStreamHandler:
    def __init__(self, process):
        self.process = process
        # 默认使用ascii编码对bytes进行解码，这只是默认，
        # 如果默认的编码无法处理，会根据对应的chardet进行识别处理。
        self.encoding = 'ascii'
        # 修复\r不作为换行分隔符导致readline无法处理的问题。
        manual_patch(self.process.stdout)
        manual_patch(self.process.stderr)

        self._loop = asyncio.get_running_loop()

    @property
    def stdin(self):
        return self.process.stdin

    @property
    def stdout(self):
        return self.process.stdout

    @property
    def stderr(self):
        return self.process.stderr

    def kill(self):
        """ """
        self.process.kill()

    def terminate(self):
        self.process.terminate()

    def feed_threadsafe(self, data):
        """ 线程安全喂数据。"""
        return asyncio.run_coroutine_threadsafe(self.feed_data(data), self._loop)

    async def feed_data(self, data: Optional[bytes]):
        """ 异步喂数据。"""
        self.stdin.write(data)
        await self.stdin.drain()

    async def _stream_handler(self, stream_id, line):
        raise NotImplementedError

    async def run(self, input=None, close_stdin=True, timeout=None):
        async def _stream_reader(fd, stream_id):
            nonlocal stream_getter
            while True:
                line = await fd.readline()
                if isinstance(line, bytes):
                    encoding = self.encoding
                    try:
                        line = line.decode(encoding)
                    except UnicodeDecodeError:
                        encoding = chardet.detect(line)['encoding']
                        self.encoding = encoding
                        line = line.decode(encoding)
                if not line:
                    break
                await stream_getter.put((stream_id, line))
            fd._transport.close()
            await stream_getter.put(None)

        async def _stream_handler():
            nonlocal stream_getter

            while True:
                data = await stream_getter.get()
                if data is None:
                    if transport_is_closing():
                        break
                else:
                    await self._stream_handler(*data)

        def transport_is_closing():
            return (self.stdout._transport.is_closing() and
                    self.stderr._transport.is_closing())

        if input:
            await self.feed_data(input)
        if close_stdin:
            self.stdin.close()

        stream_getter = asyncio.Queue()
        return await asyncio.wait([
            _stream_handler(),
            _stream_reader(self.stdout, STREAM_OUT),
            _stream_reader(self.stderr, STREAM_ERROR)],
            timeout=timeout
        )


def global_patch():
    """ 全局打补丁."""
    manual_patch(asyncio.streams.StreamReader, False)


def manual_patch(stream_reader, include_self=True):
    """ 单次补丁。"""
    if include_self:
        new_readline = partial(readline, stream_reader)
        new_readuntil = partial(readuntil, stream_reader)
    else:
        new_readline = readline
        new_readuntil = readuntil
    stream_reader.readline = new_readline
    stream_reader.readuntil = new_readuntil


# ==============================================================================
# 以下代码源于 asyncio/streams.py 文件中StreamReader类下的方法
# 修复 readline 在windows下无法读取\r结尾的行。
# ==============================================================================

async def readline(self):
    """Read chunk of data from the stream until newline (b'\n') is found.

    On success, return chunk that ends with newline. If only partial
    line can be read due to EOF, return incomplete line without
    terminating newline. When EOF was reached while no bytes read, empty
    bytes object is returned.

    If limit is reached, ValueError will be raised. In that case, if
    newline was found, complete line including newline will be removed
    from internal buffer. Else, internal buffer will be cleared. Limit is
    compared against part of the line without newline.

    If stream was paused, this function will automatically resume it if
    needed.
    """
    sep = b'\n'
    seplen = len(sep)
    seps = (b'\n', b'\r')
    try:
        line = await self.readuntil(seps)
    except asyncio.IncompleteReadError as e:
        return e.partial
    except asyncio.LimitOverrunError as e:
        if self._buffer.startswith(sep, e.consumed):
            del self._buffer[:e.consumed + seplen]
        else:
            self._buffer.clear()
        self._maybe_resume_transport()
        raise ValueError(e.args[0])
    return line


async def readuntil(self, separators=(b'\n', b'\r')):
    """Read data from the stream until ``separator`` is found.

    On success, the data and separator will be removed from the
    internal buffer (consumed). Returned data will include the
    separator at the end.

    Configured stream limit is used to check result. Limit sets the
    maximal length of data that can be returned, not counting the
    separator.

    If an EOF occurs and the complete separator is still not found,
    an IncompleteReadError exception will be raised, and the internal
    buffer will be reset.  The IncompleteReadError.partial attribute
    may contain the separator partially.

    If the data cannot be read because of over limit, a
    LimitOverrunError exception  will be raised, and the data
    will be left in the internal buffer, so it can be read again.
    """
    assert separators
    # seplen = len(separator)
    # 这里强制设为1无关紧要，只要separators的元素都不为空就行
    seplen = 1
    if seplen == 0:
        raise ValueError('Separator should be at least one-byte string')

    if self._exception is not None:
        raise self._exception

    # Consume whole buffer except last bytes, which length is
    # one less than seplen. Let's check corner cases with
    # separator='SEPARATOR':
    # * we have received almost complete separator (without last
    #   byte). i.e buffer='some textSEPARATO'. In this case we
    #   can safely consume len(separator) - 1 bytes.
    # * last byte of buffer is first byte of separator, i.e.
    #   buffer='abcdefghijklmnopqrS'. We may safely consume
    #   everything except that last byte, but this require to
    #   analyze bytes of buffer that match partial separator.
    #   This is slow and/or require FSM. For this case our
    #   implementation is not optimal, since require rescanning
    #   of data that is known to not belong to separator. In
    #   real world, separator will not be so long to notice
    #   performance problems. Even when reading MIME-encoded
    #   messages :)

    # `offset` is the number of bytes from the beginning of the buffer
    # where there is no occurrence of `separator`.
    offset = 0

    # Loop until we find `separator` in the buffer, exceed the buffer size,
    # or an EOF has happened.
    while True:
        buflen = len(self._buffer)

        # Check if we now have enough data in the buffer for `separator` to
        # fit.
        if buflen - offset >= seplen:
            # 多种处理方式，并且有顺序的，先检测 \n，然后是\r
            # 并且保证\r不在最后一字节，以优先匹配\r\n
            for separator in separators:
                isep = self._buffer.find(separator, offset)
                try:
                    if separator == b'\r' and isep != -1 and self._buffer[isep + 1] == b'\n':
                        continue
                except IndexError:
                    pass
                if isep != -1:
                    # `separator` is in the buffer. `isep` will be used later
                    # to retrieve the data.
                    break
            else:
                # see upper comment for explanation.
                offset = buflen + 1 - seplen
                if offset > self._limit:
                    raise asyncio.LimitOverrunError(
                        'Separator is not found, and chunk exceed the limit',
                        offset)
            break

        # Complete message (with full separator) may be present in buffer
        # even when EOF flag is set. This may happen when the last chunk
        # adds data which makes separator be found. That's why we check for
        # EOF *ater* inspecting the buffer.
        if self._eof:
            chunk = bytes(self._buffer)
            self._buffer.clear()
            raise asyncio.IncompleteReadError(chunk, None)

        # _wait_for_data() will resume reading if stream was paused.
        await self._wait_for_data('readuntil')

    if isep > self._limit:
        raise asyncio.LimitOverrunError(
            'Separator is found, but chunk is longer than limit', isep)

    chunk = self._buffer[:isep + seplen]
    del self._buffer[:isep + seplen]
    self._maybe_resume_transport()
    return bytes(chunk)
