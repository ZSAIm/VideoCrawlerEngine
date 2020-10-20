# -*- coding: utf-8 -*-
from traceback import print_exc
import threading
from requester.base import requester, factor_request, get_requester
from requester.base import REQ_STOPPED, REQ_DONE, REQ_ERROR, REQ_READY, REQ_RUNNING
from layer import Layer, ParallelLayer
from script import select_script
from requester.utils.tempfile import TemporaryDir
from requester.request import fake_script
from contexts import a, b, tempdir, abcde
from requester.request import script_request
from collections import defaultdict
from requester.base import Request
from functools import _make_key as make_key
from script import supported_script, get_script
import hashlib
import worker
import asyncio
from contexts import glb
import debugger as dbg


__task_stacks__ = {}


class ScriptLayer(Layer):
    def __init__(self, script):
        self.depth = 0

        self.script = script

        self.subscripts = None
        self.flows = None

    def __len__(self):
        return len(self.flows)

    def __iter__(self):
        return iter(self.flows or [])

    async def execute_script(self):
        try:
            result = await self.script.start_request()
        except Exception as e:
            print_exc()
            raise

        subscripts = []
        subflows = []
        for item in result:
            f, s = factor_request(item, self.script.rule)

            if not dbg.__debug_mode__:
                extra_flows = [
                    get_requester(name)()
                    for name in self.script.get_data('config', {}).get('append', [])
                ]
                f.extend(extra_flows)
            subflows.append(f)
            subscripts.extend(ScriptLayer(s))

        self.flows = ParallelLayer(1, subflows)
        self.subscripts = subscripts

        return subscripts

    async def locale(self):
        """"""
        await self.flows.locale(mark_branch_index=True)

    async def run(self):
        if not self.flows and not self.subscripts:
            await self.execute_script()

        with glb['script'].enter(self.script.progress.data), \
             tempdir.enter(TemporaryDir(self.script.get_data('tempdir'))):

            return await self.flows.run()

    def stop(self):
        asyncio.run(asyncio.wait([f.stop() for f in self.flows]))
        # 重启stop worker线程，避免过多的线程滞留
        worker.restart('stop')


@requester('task')
async def start_task(url, rule=None, **options):
    async def _worker(index, layer):
        # 定位工作层节点并编号
        # with b.enter(index):
        with a.enter(index):
            await layer.locale()

        async with sema:
            with a.enter(index):
                return await layer.run()

    s = get_script(select_script(supported_script(url)))

    script_req = script_request(url, rule, script=s, dismiss=False)

    scriptlay = ScriptLayer(script_req)

    subscripts = await scriptlay.execute_script()

    dbg.upload(
        title=script_req.get_data('title'),
        url=script_req.get_data('url'),
    )

    max_workers = 1
    sema = asyncio.Semaphore(max_workers)
    tasks = [
        asyncio.create_task(_worker(i, s))
        for i, s in enumerate([scriptlay] + subscripts)
    ]

    dbg.add_stopper(scriptlay.stop)
    return await asyncio.wait(tasks)


class FakeTask(Request):
    """ fake task for debugging."""
    NAME = 'task'

    def __init__(self, **fake_script_options):
        self._queue = None
        self._ready = threading.Event()
        self.fake_script_options = fake_script_options
        self.loop = None

    async def end_request(self):
        async def _worker(layer, index):
            with b.enter(index):
                await layer.locale()

            async with sema:
                with b.enter(index):
                    return await layer.run()

        self._queue = asyncio.Queue()
        self._ready.set()
        self.loop = asyncio.get_running_loop()
        acnt = 0
        while True:
            data, options = await self._queue.get()
            with a.enter(acnt):
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

                dbg.add_stopper(script.stop)
                await asyncio.wait(tasks)
                self._queue.task_done()
            acnt += 1

    def run(self, o, **options):
        self._ready.wait(timeout=10)
        asyncio.run_coroutine_threadsafe(self._queue.put((o, options)),
                                         loop=self.loop)


def cat_abcde(abcde_lst, cat_str='-'):
    return cat_str.join([str(i) for i in abcde_lst])


class TaskStack:
    def __init__(self, url, **options):
        self.url = url
        self.options = options
        if dbg.__debug_mode__:
            task = FakeTask(**options)
        else:
            task = start_task(url, **options)
        self.taskreq = task
        self.running = set()
        self.all_branches_works = defaultdict(dict)

    @property
    def key(self):
        return hashlib.md5(
            hex(make_key((self.url,), self.options, True).hashvalue).encode('utf-8')
        ).hexdigest()

    @property
    def blen(self):
        return len(self.all_branches_works)

    @property
    def current_branch(self):
        return self.all_branches_works[f'{a()}-{b()}']

    def all_works(self):
        for k, v in self.all_branches_works.items():
            yield from v.items()

    def run_background(self):
        with a.enter(0), glb['task'].enter(self):
            return self.taskreq.start_request()

    def debug(self, o, **options):
        assert dbg.__debug_mode__
        with glb['task'].enter(self):
            self.taskreq.start_request()
            self.taskreq.run(o, **options)

    def stop(self):
        self.taskreq.stop()

    def __enter__(self):
        print(abcde.get())
        self.running.add(abcde.get())

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.running.remove(abcde.get())

    def add_work(self, work):
        self.current_branch[work.__locale__] = work

    def find_by_name(self, name):
        """ 寻找节点。"""
        return [v for k, v in self.current_branch.items() if v.NAME == name]

    def simple(self):
        all_nodes = {}
        requesters = defaultdict(list)
        sum_weight = 0
        all_works = dict(self.all_works())
        # details = {}
        for k, v in all_works.items():
            all_nodes[cat_abcde(k)] = {
                'id': '-'.join([str(i) for i in k]),
                'name': v.NAME,
                'weight': v.WEIGHT,
                'percent': round(v.progress.percent, 3),
                'status': v.progress.status,
                'log': (len(v.progress.logs) and v.progress.logs[-1]) or '',
                'errMsg': '',
            }
            if v.NAME not in requesters:
                sum_weight += v.WEIGHT
            requesters[v.NAME].append(v)
            # details[cat_abcde(k)] = self.detail(cat_abcde(k))

        # 节点进度权重计算
        sum_percent = 0
        requester_ratio = []

        error_flag = False
        stopped_flag = False
        for k, v in requesters.items():
            # 请求器完成百分比
            req_percent = sum([i.progress.percent for i in v])
            weight = v[0].WEIGHT
            percent = (req_percent / len(v)) * (weight / sum_weight)
            # 运行状态
            is_stopped = any([i.progress.status == REQ_STOPPED for i in v])
            is_error = any([i.progress.status == REQ_ERROR for i in v])
            status = REQ_READY
            if is_stopped:
                status = REQ_STOPPED
                stopped_flag = True
            elif is_error:
                status = REQ_ERROR
                error_flag = True
            elif req_percent / len(v) == 100:
                status = REQ_DONE
            elif req_percent > 0:
                status = REQ_RUNNING

            requester_ratio.append({
                'name': k,
                'weight': weight,
                'percent': round(percent, 3),
                'status': status,
            })
            sum_percent += percent

        if sum_percent == 100:
            status = REQ_DONE
        elif error_flag:
            status = REQ_ERROR
        elif stopped_flag:
            status = REQ_STOPPED
        elif sum_percent > 0:
            status = REQ_RUNNING
        elif sum_percent == 0:
            status = REQ_READY
        else:
            status = 'unknown'

        return {
            'title': self.taskreq.get_data('title') or self.key,
            'n': len(all_works),
            'runningNodes': [cat_abcde(i) for i in self.running],
            'allNodes': all_nodes,
            'requesterRatio': requester_ratio,
            'percent': round(sum_percent, 3),
            'url': self.taskreq.get_data('url'),
            'status': status,
            # 'details': details
        }

    def detail(self, abcde_str):
        a, b, c, d, e = abcde_str.split('-')
        abcde_tuple = (int(a), int(b), int(c), int(d), int(e))
        request = self.all_branches_works[f'{a}-{b}'][abcde_tuple]
        data = dict(request.progress.iter_data())
        return data

    @classmethod
    def new(cls, url, **options):
        global __task_stacks__
        key = hashlib.md5(
            hex(make_key((url,), options, True).hashvalue).encode('utf-8')
        ).hexdigest()
        if key in __task_stacks__:
            raise FileExistsError()
        task = cls(url, **options)
        __task_stacks__[key] = task

        sel_script = select_script(cls.get_supported(url))
        task.run_background()
        return {
            'script': sel_script,
            'key': key,
            'url': url,
        }

    @classmethod
    def get_supported(cls, url):
        return supported_script(url)

    @classmethod
    def simple_all(cls):
        global __task_stacks__
        return {
            k: v.simple() for k, v in __task_stacks__.items()
        }

    @staticmethod
    def get_task(key):
        global __task_stacks__
        return __task_stacks__[key]



def get_task(key):
    return __task_stacks__[key]


if __name__ == '__main__':
    class TestNode:
        def __init__(self, name):
            print(name)
