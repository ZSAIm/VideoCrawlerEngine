
from nbdler import Request as DlRequest, dlopen, HandlerError
from helper.ctxtools import ctx
from request import requester
from pydantic import BaseModel
from utils.model import DefaultField
from typing import Dict, List
import threading
import requests
import asyncio
import aiohttp
import time


class DownloadDataModel(BaseModel):
    dstpath: str = DefaultField(title='文件存储路径')
    filesize: int = DefaultField(title='文件大小')


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
        )
        ctx.set_percent(dl.percent_complete)
        ctx.set_timeleft(dl.remaining_time)
        ctx.set_speed(lambda: dl.transfer_rate())

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
    )


@requester('download', weight=1, infomodel=DownloadDataModel)
async def easy_download(
    uri: str = None,
    headers: Dict = None,
    buffsize: float = 1024 * 1024,
    timeout: float = None,
    **kwargs
):
    def stop():
        nonlocal stop_flag
        stop_flag = True
        stop_event.wait()

    def size():
        nonlocal sizecnt
        return sizecnt

    def speed():
        nonlocal avgspeed
        unitdict = {
            'GB/s': 1024 * 1024 * 1024,
            'MB/s': 1024 * 1024,
            'KB/s': 1024,
            'B/s': 1,
        }
        for k, v in unitdict.items():
            if avgspeed > v:
                return f'{round(avgspeed / v, 2)} {k}'
        return f'{avgspeed} B/s'
    ctx.glb.task.show()
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
            chunksize = 1024 * 4
            sizecnt = 0
            avgspeed = 0
            starttime = time.time()

            buffcnt = 0
            buff_lst = []
            ctx.set_speed(speed)
            ctx.upload(
                filesize=size,
                dstpath=tempf.filepath,
            )
            with tempf('wb') as f:
                async for chunk in resp.content.iter_chunked(chunksize):
                    # 已下载文件大小
                    chunklen = len(chunk)
                    sizecnt += chunklen
                    buffcnt += chunklen
                    buff_lst.append(chunk)
                    # 缓冲溢出后写入文件
                    if buffcnt >= buffsize:
                        f.writelines(buff_lst)
                        buffcnt = 0
                        buff_lst = []
                    # 计算平均下载速度
                    avgspeed = sizecnt / ((time.time() - starttime) or float('inf'))

                    if stop_flag:
                        stop_event.set()
                        break
    finally:
        stop_flag = True
        stop_event.set()

