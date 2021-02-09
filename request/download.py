
from nbdler import Request as DlRequest, dlopen, HandlerError
from helper.ctxtools import ctx
from request import requester
from pydantic import BaseModel
from utils.model import DefaultField
from utils.common import readable_file_size
from typing import Dict, List
import threading
import requests
import asyncio
import aiohttp
import time


class DownloadDataModel(BaseModel):
    dstpath: str = DefaultField(title='文件存储路径')
    filesize: int = DefaultField(title='文件大小')
    downloadSize: int = DefaultField(title='已下载大小')
    writeSize: int = DefaultField(title='已写入文件大小')


@requester('download', weight=1, infomodel=DownloadDataModel)
async def download(
    uri: str = None,
    headers: Dict = None,
    *,
    multi_sources: List[Dict] = None,
    **kwargs
):
    """ 下载请求
    Args:
        uri: 下载uri
        headers: 指定下载请求头
        multi_sources: 多下载源的添加方式。
            [{'uri': 'http://xxx', 'headers': headers}, ...]

    """
    def speed():
        nonlocal dl
        transfer_rate = dl.transfer_rate()
        return f'{readable_file_size(transfer_rate)}/s'
        # unitdict = {
        #     'GB/s': 1024 * 1024 * 1024,
        #     'MB/s': 1024 * 1024,
        #     'KB/s': 1024,
        #     'B/s': 1,
        # }
        # for k, v in unitdict.items():
        #     if transfer_rate > v:
        #         return f'{round(transfer_rate / v, 2)} {k}'
        # return f'{round(transfer_rate / v, 2)} B/s'
    # 创建下载请求对象
    tempf = ctx.tempdir.mktemp()
    dlr = DlRequest(file_path=tempf.filepath)
    sources = []
    if uri:
        sources = [{
            'uri': uri,
            'headers': headers,
            **kwargs
        }]
    sources += multi_sources or []

    for source in sources:
        dlr.put(**source)
    async with dlopen(dlr) as dl:
        ctx.upload(
            filesize=dl.file.size,
            dstpath=dl.file.pathname,
            downloadSize=lambda: readable_file_size(dl.walk_length()),
            writeSize=lambda: readable_file_size(dl.done_length()),
        )
        ctx.set_percent(dl.percent_complete)
        ctx.set_timeleft(dl.remaining_time)
        ctx.set_speed(speed)

        dl.start(loop=asyncio.get_running_loop())
        # FIX: Nbdler 下载器在协程下出现的问题
        while not dl._future:
            await asyncio.sleep(0.01)

        # 创建下载停止器
        ctx.add_stopper(dl.pause)

        async for exception in dl.aexceptions():
            ctx.warning(exception.exc_info)
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
    ctx.upload(
        dstpath=dl.file.pathname,
        filesize=dl.file.size,
        downloadSize=lambda: readable_file_size(dl.walk_length()),
        writeSize=lambda: readable_file_size(dl.done_length()),
    )


@requester('download', weight=1, infomodel=DownloadDataModel)
async def stream_download(
    uri: str = None,
    headers: Dict = None,
    buffsize: float = 1024 * 1024,
    timeout: float = None,
    **kwargs
):
    """ 文件流下载，通常用于下载具有实时性的数据。 """
    def stop():
        nonlocal stop_flag
        stop_flag = True
        stop_event.wait()

    def size():
        nonlocal sizecnt
        return sizecnt

    def speed():
        nonlocal avgspeed
        return f'{readable_file_size(avgspeed)}/s'
        # unitdict = {
        #     'GB/s': 1024 * 1024 * 1024,
        #     'MB/s': 1024 * 1024,
        #     'KB/s': 1024,
        #     'B/s': 1,
        # }
        # for k, v in unitdict.items():
        #     if avgspeed > v:
        #         return f'{round(avgspeed / v, 2)} {k}'
        # return f'{avgspeed} B/s'

    def percent():
        nonlocal total_size
        return sizecnt / total_size

    maxsize = ctx.script.config['maxsize']
    stop_event = threading.Event()
    stop_flag = False
    ctx.add_stopper(stop)
    try:
        tempf = ctx.tempdir.mktemp()
        async with aiohttp.ClientSession() as sess:
            resp = await sess.get(
                url=uri,
                headers=headers,
                **kwargs
            )
            if resp.status not in (200, 206):
                raise ConnectionAbortedError()

            chunksize = 1024 * 4
            sizecnt = 0
            avgspeed = 0
            donesize = 0
            starttime = time.time()
            if resp.content_length is None:
                # 不确定的进度
                ctx.set_percent(None)
            else:
                total_size = resp.content_length
                ctx.set_percent(percent)

            buffcnt = 0
            buff_lst = []
            ctx.set_speed(speed)
            ctx.upload(
                filesize=size,
                dstpath=tempf.filepath,
                downloadSize=lambda: readable_file_size(sizecnt),
                writeSize=lambda: readable_file_size(donesize),
            )
            with tempf('wb') as f:
                try:
                    async for chunk in resp.content.iter_chunked(chunksize):
                        # 已下载文件大小
                        chunklen = len(chunk)
                        sizecnt += chunklen
                        buffcnt += chunklen
                        buff_lst.append(chunk)
                        # 缓冲溢出后写入文件
                        if buffcnt >= buffsize:
                            f.writelines(buff_lst)
                            donesize = sum([len(buff) for buff in buff_lst], donesize)
                            buffcnt = 0
                            buff_lst = []
                        # 计算平均下载速度
                        avgspeed = sizecnt / ((time.time() - starttime) or float('inf'))

                        if stop_flag:
                            stop_event.set()
                            break

                        # 切割视频
                        if maxsize <= sizecnt:
                            raise Warning()
                finally:
                    if buff_lst:
                        f.writelines(buff_lst)
    finally:
        stop_flag = True
        stop_event.set()

