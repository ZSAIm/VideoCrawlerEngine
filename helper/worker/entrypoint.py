from traceback import print_exc

from helper.ctxtools import ctx
from helper.ctxtools.mgr import (
    copy_context_to_dict,
    run_context_from_dict,
)
import asyncio

__EPS__ = {}


class Entrypoint:
    NAME: str

    def run(self, *args, **kwargs):
        raise NotImplementedError

    async def arun(self, *args, **kwargs):
        raise NotImplementedError

    def __init_subclass__(cls, **kwargs):
        if cls.NAME in __EPS__:
            raise ValueError(f'存在重名的entrypoint -> {cls.NAME}')
        __EPS__[cls.NAME] = cls


class SubmitEntrypoint(Entrypoint):
    NAME = 'submit'

    def run(self, __context, __fn, *args, **kwargs):
        # with run_context_from_dict(self.context):
        with run_context_from_dict(__context):
            try:
                result = __fn(*args, **kwargs)
            except Exception:
                # print_exc()
                raise
            return result

    async def arun(self, __context, __fn, *args, **kwargs):
        # with run_context_from_dict(self.context):
        with run_context_from_dict(__context):
            try:
                result = await __fn(*args, **kwargs)
            except Exception:
                # print_exc()
                raise
            return result


class RequesterEntrypoint(Entrypoint):
    NAME = 'requester'

    def run(self, context):
        with run_context_from_dict(context) as dbg:
            try:
                print(f'进入：{dbg.get_NAME()}')
                dbg.start()
                result = dbg.end_request()
                dbg.task_done()
            except BaseException as err:
                print_exc()
                dbg.error_handler(err)
                raise
            finally:
                dbg.close()
                print(f'退出：{dbg.get_NAME()}')
        return result

    async def arun(self, context):
        with run_context_from_dict(context) as dbg:
            try:
                print(f'进入：{dbg.get_NAME()}')
                dbg.__request__.__loop__ = asyncio.get_running_loop()
                dbg.start()
                result = await dbg.end_request()
                dbg.task_done()
            except BaseException as err:
                print_exc()
                dbg.error_handler(err)
                raise
            finally:
                dbg.close()
                dbg.__request__.__loop__ = None
                print(f'退出：{dbg.get_NAME()}')

        return result


def get_ep(name):
    """ 返回入口点。"""
    ep_cls = __EPS__.get(name, None)
    if ep_cls is None:
        raise ValueError(f'找不到名称为{name}的入口点。')
    ep = ep_cls()
    return ep
