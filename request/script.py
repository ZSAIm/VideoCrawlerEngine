from typing import List, Optional, Union, Dict, Any
from app.script.manager import ScriptTask
from helper.client import get_client
from helper.ctxtools import ctx
from helper.payload import requester, Requester
from utils.common import safety_filename
from pydantic import BaseModel
from utils.model import DefaultField
import time
import os


class ScriptDataModel(BaseModel):
    url: str = DefaultField(title='脚本要处理的目标URL')
    name: str = DefaultField(title='脚本处理器名称')
    rule: str = DefaultField(title='脚本处理规则')
    quality: str = DefaultField(title='质量名称')
    config: Dict[str, Any] = DefaultField(title='脚本配置')
    title: str = DefaultField(title='脚本唯一标题')
    n: int = DefaultField(title='分支数量')


@requester('script', root=True, infomodel=ScriptDataModel)
def fake_script(
    request_items: List[Requester],
    rule: str or int,
    **options
):
    """ (调试模式) 调试模式下的虚假脚本请求Root。"""
    from app.script.manager import ScriptTask
    from app.script import ScriptBaseClass

    url = 'http://fake.script'
    script = ScriptTask(ScriptBaseClass)('')
    ctx.upload(
        url=url,
        name=script.name,
        script=script,
        rule=rule,
        quality=100,
        title=f'debug_{time.time() * 1000}',
        tempdir=ctx.glb.config['tempdir'],
        n=1,
        config=script.config,
    )
    ctx.upload(**options)
    ctx.upload(items=[request_items])
    return ctx.getdata('items')


@requester('script', root=True, infomodel=ScriptDataModel)
def simple_script(
    url: str,
    rule: Optional[Union[str, int]],
    script_task: ScriptTask,
    *,
    prevent: bool = False,
    **kwargs
):
    if rule is None:
        rule = script_task.config.get('default_rule')
    qn = script_task.quality_ranking
    quality = qn[max(0, round((100 - int(rule)) * len(qn) / 100) - 1)]

    # 请求来源脚本请求
    ctx.upload(
        url=url,
        name=script_task.name,
        script={
            'name': script_task.name,
            'config': script_task.config,
            'version': script_task.version,
            'quality_ranking': script_task.quality_ranking
        },
        config=script_task.config,
        rule=rule,
        quality=quality,
    )

    # 创建并运行脚本
    script_task(
        url=url,
        quality=quality,
        prevent=prevent,
        **kwargs
    ).run()

    return dict(ctx.iterdata())


@requester('script', root=True, infomodel=ScriptDataModel)
def script_request(
    url: str,
    rule: Optional[Union[str, int]] = None,
    *,
    prevent: bool = False,
    **kwargs
):
    """
    Args:
        url: 目标URL
        rule: 选择规则
        prevent: 是否允许子脚本请求

    """

    cli = get_client('script')
    result = cli.exec_script(
        url=url,
        # rule=100
    )
    ctx.upload(**result)
    title = safety_filename(ctx.getdata('title', ''))

    srp = ctx.getdata('script', {})
    # 创建临时目录
    tempdir = os.path.realpath(os.path.join(
        ctx.glb.config['tempdir'],
        srp['name'],
        title,
    ))

    items = ctx.getdata('items', [])
    if not items:
        item = ctx.getdata('item', None)
        if item:
            items = [item]
        else:
            raise ValueError('没有上传有效的处理流程。')
    ctx.upload(
        items=items,
        title=title,
        tempdir=tempdir,
        n=len(items),
    )

    return items