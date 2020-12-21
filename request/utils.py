import os
import shutil
from typing import Any, Dict
from helper.payload import requester
from helper.ctxtools import ctx
from request.ffmpeg import ffmpeg


@requester('jsruntime')
def jsruntime(session, **kwargs):
    """ """
    session.reset()


@requester('cleanup', weight=0.3)
def cleanup():
    """ 清楚临时文件。 """
    ctx.tempdir.rmfiles(True)


@requester('checkpoint', weight=0.5)
async def checkpoint():
    """ 同一转换未经过ffmpeg处理的视频，以达到目标的视频编码方式。

    该方法在以下两种情况下在视频处理方面做出的不同的处理：
    1. download下载的视频未经过ffmpeg编码处理：
        1) 搜索所有download下载的视频文件。
        2) 对所有的download下载的视频文件经过ffmpeg指定编码处理。
        3) 得到经过了ffmpeg编码处理的视频文件。

    2. download下载的视频已经经过了ffmpeg编码处理：
        1) 搜索所有经过ffmpeg处理的视频文件。

    将以上两种情况下经过ffmpeg处理的视频文件按照规则从临时目录移动并重命名到目的存储目录。

    在多视频文件的情况下会在视频文件加上前缀，并且放到以标题为名称的子目录下。
    """

    # 如果已经过了ffmpeg处理，经跳过该转换流程
    merges = ctx.flow.find_by_name('ffmpeg')

    results = [merge.getdata('dstpath') for merge in merges]

    strict = ctx.script.config.get('strict', None)
    if not strict:
        strict = ctx.script.basecnf.get('strict', False)

    if not results:
        # 对于没有经过ffmpeg处理的工具，转换所有的音视频文件
        downloads = ctx.flow.find_by_name('download')
        for filename in [dl.getdata('dstpath') for dl in downloads]:
            if strict:
                converter = ffmpeg.convert(filename)
            else:
                converter = ffmpeg.fast_convert(filename)
            await converter.end_request()
            results.append(converter.getdata('dstpath'))

    # 修改文件名并移动文件
    savedir = os.path.realpath(ctx.glb.config['savedir'])
    # 当文件多于一个的时候在存储目录添加一级目录
    n = ctx.glb.script['n']
    if n > 1:
        savedir = os.path.join(os.path.realpath(savedir), ctx.glb.script['title'])
        if not os.path.isdir(savedir):
            os.makedirs(savedir)

    for filepath in results:
        name = os.path.basename(filepath)
        name = name.split('.', 1)[-1]
        if n > 1:
            name = f'{ctx.b :03}.{name}'
        dstpath = os.path.join(savedir, name)
        shutil.move(filepath, dstpath)



