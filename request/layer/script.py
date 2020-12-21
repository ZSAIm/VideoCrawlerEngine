import asyncio

from helper import worker
from traceback import print_exc
from helper.ctxtools import ctx as dbg
from helper.ctxtools.vars.flow import glb, b, tempdir
from helper.ctxtools.vars.script import script
from .flow import ParallelLayer
from .base import BaseLayer
from helper.payload import get_payload_by_name, get_payload_by_sign, gen_linear_flow
from request.helper.tempfile import TemporaryDir
from contextlib import ExitStack


class ScriptLayer(BaseLayer):
    def __init__(self, script):
        self.depth = 0

        self.script = script

        self.subscripts = None
        self.layers = None

    def __len__(self):
        return len(self.layers)

    def __iter__(self):
        return iter(self.layers or [])

    async def execute_script(self):
        key = f'{id(self.script):x}'
        with script['key'].apply(key):
            try:
                all_items = await self.script.start_request()
            except Exception as e:
                print_exc()
                raise
        subscripts = []
        subnodes = []

        ctxmgr_value = {
            glb['script']: self.script,
            script['key']: key,
            script['config']: self.script.getdata('config', {})
        }

        with ExitStack() as stack:
            contexts = [
                stack.enter_context(ctxmgr.apply(value))
                for ctxmgr, value in ctxmgr_value.items()
            ]
            for index, item in enumerate(all_items):
                with b.apply(index):
                    f, s = gen_linear_flow(item, self.script['rule'])

                    extra_flows = [
                        get_payload_by_name(name)()
                        for name in self.script.getdata('config', {}).get('append', [])
                    ]
                    f.extend(extra_flows)
                    subnodes.append(f)
                    subscripts.extend(ScriptLayer(s))

            self.layers = ParallelLayer(1, subnodes, is_scriptlayer=True)
            self.subscripts = subscripts

        return subscripts

    def __enter__(self):
        self.setpoint()
        return self

    def setpoint(self):
        """"""
        self.layers.setpoint()

    async def run(self, reload=False):
        if not self.layers and not self.subscripts:
            await self.execute_script()

        with glb['script'].apply(self.script), \
             tempdir.apply(TemporaryDir(self.script.getdata('tempdir'))):

            return await self.layers.run()

    async def stop(self):
        return await asyncio.wait([layer.stop() for layer in self.layers])
