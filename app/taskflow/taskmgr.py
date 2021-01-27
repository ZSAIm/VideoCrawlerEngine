# -*- coding: utf-8 -*-
# from app.taskflow.helper.task import view_task
from request.layer.flow import SubFlowLayer
from request.task import start_task
from helper.ctxtools.vars.flow import a5g, glb, flow_mgr
from typing import Tuple, List, Dict, Any, Union, Generator
from collections import defaultdict
from helper.ctxtools import ctx
from utils.common import gen_sign, cat_a5g
from helper.payload import FlowPayload, Requester
from contextlib import contextmanager
from helper.worker import get_worker, executor
from contextlib import ExitStack
from helper.conf import get_conf
from functools import partial
import threading
import json


class TaskFlowManager(object):

    def __init__(self, url: str, options: Dict) -> None:
        self.url = url
        self.options = options

        self._task = start_task(
            url, **options
        )
        self._lock = threading.Lock()

        self.mounted_roots = defaultdict(set)
        self.running_roots = set()

        self.mounted_layers = defaultdict(set)
        self.running_layers = set()

        # allnodes 维度如下: [(a, b)][(a, b, c, d, e, f)]
        # f = (sb, sc, sd, se)
        # [(a, b)]              : 具体到某一条分支
        # [(c, d, e, f)]        : 具体到分支中的工作节点
        # [sb]                  : 工作节点的分支编号，父节点为0
        # [g[sc, sd, se, sf]]   : 父节点为()
        self.allnodes = defaultdict(
            partial(defaultdict, partial(defaultdict, dict))
        )
        self.running_nodes = set()

    @property
    def sign(self) -> str:
        return gen_sign(json.dumps(dict(
            url=self.url,
            options=self.options,
        )))

    @property
    def name(self) -> str:
        return self._task.getdata('name', '')

    @property
    def title(self) -> str:
        return self._task.getdata('title', self.sign)

    @property
    def allroots(self):
        return self._task.getdata('roots', [])

    @property
    def branch(self) -> Generator[Tuple[int, Requester], None, None]:
        ab = ctx.a, ctx.b
        for k2, v2 in self.allnodes[ab].items():
            for k3, v3 in v2.items():
                for k4, v4 in v3.items():
                    yield ab + k2 + ((k3,) + k4,), v4

    @property
    def raw_flow_node(self):
        def get_raw_flow_a5g(o):
            if isinstance(o, (list, tuple)):
                return [get_raw_flow_a5g(i) for i in o]
            elif isinstance(o, Requester):
                if not o.__point__:
                    raise Warning()
                return cat_a5g(o.__point__)
            raise ValueError(f'type error:{type(o)}')
        try:
            return [get_raw_flow_a5g(root_layer.raw_flows)
                    for root_layer in self._task.getdata('root_layers', [])]
        except Warning:
            return []

    @contextmanager
    def enter_node(self) -> Any:
        _a, _b, _c, *_ = _a5g = a5g.get()
        # self.running_layers[(_a, _b, _c)].add(_a5g)
        self.running_layers.add((_a, _b, _c))
        self.running_nodes.add(_a5g)
        yield self
        self.running_nodes.remove(_a5g)

    @contextmanager
    def enter_layer(self, abc):
        yield self
        # del self.running_layers[abc]
        self.running_layers.remove(abc)

    @contextmanager
    def enter_root(self, a):
        print('enter_root')
        self.running_roots.add((a,))
        yield self
        self.running_roots.remove((a,))

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
            for ctxmgr, value in ctxmgr_value.items():
                ctx_stack.enter_context(ctxmgr.apply(value))

            return self._task.start_request()

    def mount_node(self, node: Requester) -> Tuple[Union[int, Tuple], ...]:
        _a, _b, _c, _d, _e, _f, _g = point = node.__point__
        abc = (_a, _b, _c)
        sb, *scdef = _g

        self.allnodes[(_a, _b)][(_c, _d, _e, _f)][sb][tuple(scdef)] = node

        # 节点挂载到主层下
        if point not in self.mounted_layers[abc]:
            self.mounted_layers[(_a, _b, _c)].add(point)

        # 主层挂载到对应的脚本层下
        if (_a,) not in self.mounted_roots:
            self.mounted_roots[(_a,)].add(abc)

        return point

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


if __name__ == '__main__':
    pass

