# -*- coding: utf-8 -*-
from request.layer.flow import SubFlowLayer
from request.task import start_task
from helper.ctxtools.vars.flow import a5g, glb, flow_mgr
from typing import Tuple, List, Dict, Iterator, Any, Union, Generator
from collections import defaultdict
from exception import DataExistsError, PageOutOfRange
from helper.ctxtools import ctx
from utils.common import gen_sign, cat_a5g
from helper.payload import FlowPayload, Requester
from contextlib import contextmanager
from helper.worker import get_worker, executor
from helper.ctxtools.mgr import ContextManager
from contextlib import ExitStack
from helper.conf import get_conf
from functools import partial
import threading
import asyncio
import json


class TaskFlowManager(object):

    def __init__(self, url: str, options: Dict) -> None:
        self.url = url
        self.options = options

        self._task = start_task(
            url, **options
        )
        self._lock = threading.Lock()

        self.layers = defaultdict(list)
        self.running_layers = defaultdict(set)
        self.running_nodes = set()
        # allnodes 维度如下: [(a, b)][(a, b, c, d, e, f)]
        # f = (sb, sc, sd, se)
        # [(a, b)]              : 具体到某一条分支
        # [(c, d, e, f)]        : 具体到分支中的工作节点
        # [sb]                  : 工作节点的分支编号，父节点为0
        # [g[sc, sd, se, sf]]   : 父节点为()
        self.allnodes = defaultdict(
            partial(defaultdict, partial(defaultdict, dict))
        )

    @property
    def sign(self) -> str:
        return gen_sign(json.dumps(dict(
            url=self.url,
            options=self.options,
        )))

    @property
    def branch(self) -> Generator[Tuple[int, Requester], None, None]:
        ab = ctx.a, ctx.b
        for k2, v2 in self.allnodes[ab].items():
            for k3, v3 in v2.items():
                for k4, v4 in v3.items():
                    yield ab + k2 + ((k3,) + k4,), v4

    @contextmanager
    def enter_node(self) -> Any:
        _a, _b, _c, *_ = _a5g = a5g.get()
        self.running_layers[(_a, _b, _c)].add(_a5g)
        self.running_nodes.add(_a5g)
        yield self
        self.running_nodes.remove(_a5g)

    @contextmanager
    def enter_layer(self, abc):
        yield self
        del self.running_layers[abc]

    def iternodes(self) -> Generator[Tuple[str, Requester], None, None]:
        for k1, v1 in self.allnodes.items():
            for k2, v2 in v1.items():
                for k3, v3 in v2.items():
                    for k4, v4 in v3.items():
                        yield k1 + k2 + ((k3,) + k4,), v4

    def run_async(self) -> Any:
        """ 异步运行任务。"""
        conf = get_conf('taskflow')
        ctxmgr_value = {
            flow_mgr: self,
            glb['config']: conf['global'],
            glb['task']: self,
        }
        with ExitStack() as ctx_stack:
            contexts = [
                ctx_stack.enter_context(ctxmgr.apply(value))
                for ctxmgr, value in ctxmgr_value.items()
            ]
            return self._task.start_request()

    def add(self, work: Requester) -> Tuple[Union[int, Tuple], ...]:
        _a, _b, _c, _d, _e, _f, _g = work.__point__
        sb, *scdef = _g

        self.allnodes[(_a, _b)][(_c, _d, _e, _f)][sb][tuple(scdef)] = work
        return work.__point__

    def find_by_name(self, name: str) -> List[Requester]:
        return [v for k, v in self.branch if v.NAME == name]

    def get_by_a5g(self, abcdefg: Tuple) -> Requester:
        _a, _b, _c, _d, _e, _f, _g = abcdefg
        sb, *scdef = _g

        return self.allnodes[(_a, _b)][(_c, _d, _e, _f)][sb][tuple(scdef)]

    def stop(self):
        # 由于Requester使用的时异步停止方法，需要交由异步停止器运行
        return executor.submit(
            get_worker('async_stopper'),
            args=(self._task.stop,),
            force_sync=True
        )

    def get_subflow(self, payload: FlowPayload):
        """ 根据payload生成当前流程的子流程。"""
        with self._lock:
            _a, _b, _c, _d, _e, _f, _g = ctx.a5g
            subflow = SubFlowLayer(
                self,
                ctx.a5g,
                len(self.allnodes[(_a, _b)][(_c, _d, _e, _f)]),
                payload
            )
            return subflow

    def show(self):
        allnodes = {}
        for a5gtuple, node in self.iternodes():
            _a5g = cat_a5g(a5gtuple)

            prog = node.progress
            timeleft = prog.timeleft
            if timeleft in (float('inf'), float('nan')):
                timeleft = None
            allnodes[_a5g] = {
                'id': f'{id(node):x}',
                'a5g': _a5g,
                'name': node.NAME,
                'sign': node.SIGN,
                'weight': node.WEIGHT,
                'percent': prog.percent,
                'status': prog.status,
                'speed': prog.speed,
                'timeleft': timeleft,
                'data': node.infodata(),
            }

        # 运行节点
        running = [cat_a5g(node) for node in self.running_nodes]

        # 计算分支执行主层进度信息
        layers = {}
        for abc, nodes in self.layers.items():
            abc = cat_a5g(abc)
            a5gs = [cat_a5g(n) for n in nodes]
            # 确定layer的总状态
            status = 'done'
            for n in a5gs:
                s = allnodes[n]['status']
                if s == 'running':
                    status = 'running'
                    break
                elif s == 'error':
                    status = 'error'
                    break
                elif s == 'ready':
                    status = 'ready'

            # 确定layer的百分比进度和剩余时间
            percent = 0
            timeleft = 0
            for n in a5gs:
                percent += allnodes[n]['percent']
                timeleft += allnodes[n]['timeleft'] if allnodes[n]['timeleft'] is not None else float('inf')
            percent = percent / len(nodes)
            if timeleft == float('inf'):
                timeleft = None

            # 确定节点
            total_weight = sum([allnodes[n]['weight'] for n in a5gs])
            # 计算执行层
            layers[abc] = {
                'abc': abc,
                'percent': percent,
                'status': status,
                'timeleft': timeleft,
                'nodes': [{
                    'a5g': n,
                    'name': allnodes[n]['name'],
                    'weight': allnodes[n]['weight'],
                    'ratio': allnodes[n]['percent'] * allnodes[n]['weight'] / total_weight,
                } for n in a5gs]
            }
        running_layers = [cat_a5g(v) for v in self.running_layers.keys()]
        return {
            'sign': self.sign,
            'url': self.url,
            'title': self._task.getdata('title', self.sign),
            'options': self.options,
            'running_nodes': running,
            'layers': layers,
            'running_layers': running_layers,
            'allnodes': allnodes,

        }


__key_task: Dict[str, TaskFlowManager] = {}
__task_lst: List[TaskFlowManager] = []


def create_task(
    url: str,
    options: dict
):
    sign = gen_sign(json.dumps(dict(
        url=url,
        options=options,
    )))
    # sign = gen_key(url=url, options=options)
    if sign in __task_lst:
        raise DataExistsError(f'任务{sign}已存在。')

    task = TaskFlowManager(
        url, options
    )
    __task_lst.append(task)
    __key_task[sign] = task
    return task


def list_task(
    offset: int = 0,
    limit: int = 10,
):
    start = offset
    end = offset + limit
    tasklen = len(__task_lst)
    if start >= tasklen:
        raise PageOutOfRange('页数超出范围。')
    if tasklen < end:
        end = len(__task_lst)

    return [
        v.show()
        for v in __task_lst[start: end]
    ]


if __name__ == '__main__':
    pass

