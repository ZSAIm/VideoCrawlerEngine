
from helper.payload import (
    FlowPayload,
    export_func,
    Sequence,
    Concurrent,
)
from helper.ctxtools import ctx
from helper.worker import get_worker, executor
from request import requester, Requester
from request.ffmpeg import ffmpeg
from typing import Callable, Awaitable
from traceback import print_exc
from .ffmpeg import ffmpeg
from exception import RemoteApplyException
import asyncio
import shutil
import os


@requester('live')
async def live_daemon(
    live_getter: Callable[[], Awaitable[FlowPayload]] = None,
):
    """ 直播录像服务。
    """
    checkinterval = ctx.glb.script['interval'] or 10

    strict = ctx.script.config.get('strict', None)
    if not strict:
        strict = ctx.script.basecnf.get('strict', False)

    if strict:
        converter = ffmpeg.convert
    else:
        converter = ffmpeg.fast_convert
    pcount = 0
    while True:
        try:
            payload = await live_getter()
            # 更新脚本数据
            ctx.glb.script.upload(
                **dict(ctx.iterdata())
            )
        except RemoteApplyException as err:
            # 直播未开始还是需要更新直播间信息
            ctx.glb.script.upload(
                **err.context
            )
        except Exception:
            # 未知异常
            pass
        else:
            subflow = ctx.flow.get_subflow(payload)
            try:
                await subflow.run()
            finally:
                # 转换已下载的录播视频
                downloads = subflow.find_by_name('download')
                for dl in downloads:
                    dstpath = dl.getdata('dstpath')
                    if not dstpath:
                        # 这说明下载未真正开始，可能是无网络状态
                        # 进行小延时，避免占用过高的CPU
                        await asyncio.sleep(0.1)
                    # 这里不需要等待转换结束
                    subflow = ctx.flow.get_subflow(
                        settle(
                            converter([dstpath]),
                            prefix=f'{pcount:03}',
                            subdir='',
                        ),
                    )
                    # subflow = ctx.flow.get_subflow(
                    #     Concurrent(
                    #         settle(
                    #             converter([dstpath]),
                    #             prefix=f'{pcount:03}',
                    #             subdir='',
                    #         ),
                    #         ffmpeg.convert()
                    #     ),
                    # )
                    subflow.run()
                pcount += 1

            continue

        await asyncio.sleep(checkinterval)


@requester('after', weight=0.1)
def settle(
    what: Requester,
    prefix: str,
    subdir: str = None,
):
    """ 安置录播片段。"""
    srcpath = what.getdata('dstpath')
    if not srcpath:
        return

    savedir = os.path.realpath(ctx.glb.config['savedir'])
    savedir = os.path.join(savedir, subdir or '')

    if not os.path.isdir(savedir):
        os.makedirs(savedir)

    # 重命名临时文件流程前缀
    srcname = os.path.basename(srcpath)
    dstname = f"{prefix}.{srcname.split('.', 1)[-1]}"
    dstpath = os.path.join(savedir, dstname)
    shutil.move(srcpath, dstpath)


