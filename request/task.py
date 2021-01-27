import asyncio
import threading
from typing import Union

from request.layer.script import ScriptLayer
from helper.ctxtools import ctx
from helper.ctxtools.vars.flow import a, b
from helper.ctxtools.vars.script import script
from contextlib import ExitStack
from helper.payload.request import requester, Requester
from functools import partial
from helper.worker import get_worker, executor
from helper.conf import get_conf
from request.script import (
    fake_script,
    script_request,
    simple_script,
)


@requester('task')
async def start_task(
    url: str,
    rule: Union[int, str] = None,
    **options
):
    """ 创建任务的起点：

    """
    async def _worker(index, layer):
        """ 执行流程。"""
        ctxmgr_value = {
            a: index,
            script['key']: f'{id(script_req):x}',
            script['config']: script_req.getdata('config', {}),
            script['basecnf']: dict(get_conf('script')['base']),
            # 方便获取脚本数据
            script['__getitem__']: script_req.__getitem__,
        }
        with ExitStack() as stack:
            for ctxmgr, value in ctxmgr_value.items():
                stack.enter_context(ctxmgr.apply(value))

            stack.enter_context(layer)
            async with sema:
                return await layer.run()

    async def _stop():
        return await asyncio.wait([layer.stop() for layer in [scriptlay] + subscripts])

    script_req = script_request(
        url=url,
        rule=rule,
        prevent=False,
    )

    scriptlay = ScriptLayer(script_req)

    with a.apply(0):
        subscripts = await scriptlay.execute_script()

    ctx.upload(
        title=script_req.getdata('title'),
        url=script_req.getdata('url'),
        name=script_req.getdata('name'),
        roots=[scriptlay.script] + [s.script for s in subscripts],
        root_layers=[scriptlay] + subscripts
    )

    max_workers = 3
    sema = asyncio.Semaphore(max_workers)
    tasks = [
        asyncio.create_task(_worker(i, s))
        for i, s in enumerate([scriptlay] + subscripts)
    ]
    # 使用当前任务协程事件循环来停止任务
    ctx.add_stopper(_stop)
    return await asyncio.wait(tasks)


class FakeTask(Requester):
    """ fake task for debugging."""
    NAME = 'task'

    def __init__(self, **fake_script_options):
        self._queue = None
        self._ready = threading.Event()
        self.fake_script_options = fake_script_options
        self.loop = None

    async def end_request(self):
        async def _worker(layer, index):
            with b.apply(index), layer:
                # layer.locale()
                async with sema:
                    return await layer.run()

        self._queue = asyncio.Queue()
        self._ready.set()
        self.loop = asyncio.get_running_loop()
        acnt = 0
        while True:
            data, options = await self._queue.get()
            with a.apply(acnt):
                rule = options.get('rule', 1)
                options['rule'] = rule

                script = ScriptLayer(fake_script(data, **options))
                await script.execute_script()

                tasks = [
                    asyncio.create_task(_worker(s, i))
                    for i, s in enumerate([script])
                ]

                max_workers = 3
                sema = asyncio.Semaphore(max_workers)

                ctx.add_stopper(script.stop)
                await asyncio.wait(tasks)
                self._queue.task_done()
            acnt += 1

    def run(self, o, **options):
        self._ready.wait(timeout=10)
        asyncio.run_coroutine_threadsafe(
            self._queue.put((o, options)),
            loop=self.loop
        )