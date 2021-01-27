import json
from typing import Dict, List, Deque

from app.taskflow.taskmgr import TaskFlowManager
from exception import DataExistsError, PageOutOfRange, DataNotFound
from utils.common import gen_sign, cat_a5g
from collections import deque

__key_task: Dict[str, TaskFlowManager] = {}
__task_lst: Deque[TaskFlowManager] = deque()


def create(
    url: str,
    options: dict
):
    key = gen_sign(json.dumps(dict(
        url=url,
        options=options,
    )))
    # sign = gen_key(url=url, options=options)
    if key in __key_task:
        raise DataExistsError(f'任务{key}已存在。', key)

    task = TaskFlowManager(
        url, options
    )
    __task_lst.appendleft(task)
    __key_task[key] = task
    return task


def list(
    offset: int = 0,
    limit: int = 9999,
    active_key: str = None,
):
    start = offset
    end = offset + limit
    tasklen = len(__task_lst)
    if start > tasklen:
        raise PageOutOfRange('页数超出范围。')
    if tasklen < end:
        end = len(__task_lst)

    return [
        view(__task_lst[i].sign, active_key == __task_lst[i].sign)
        for i in range(start, end)
    ]


def view(
    key: str,
    more: bool = False
):
    def format_mul(_val, _ratio=1, default=None):
        if _val in (None, float('inf')):
            return default
        return _val * _ratio

    def format_sum(iterable, default=None):
        try:
            ret = sum(iterable)
            if ret in (float('inf'), None):
                return default
            return ret
        except TypeError:
            return default

    task = __key_task[key]
    all_nodes = {}

    # ================ node ==================
    for a5gtuple, node in task.iternodes():
        _a5g = cat_a5g(a5gtuple)

        prog = node.progress
        timeleft = format_mul(prog.timeleft)
        percent = format_mul(prog.percent)
        all_nodes[_a5g] = {
            'id': f'{id(node):x}',
            'a5g': _a5g,
            'name': node.NAME,
            'sign': node.SIGN,
            'weight': node.WEIGHT,
            'percent': percent,
            'status': prog.status,
            'speed': prog.speed,
            'timeleft': timeleft,
            'data': node.infodata() if more else {},
        }

    # 运行节点
    running = [cat_a5g(node) for node in task.running_nodes]

    # ================ layer ==================
    # 计算分支执行主层进度信息
    all_layers = {}
    for abc, nodes in task.mounted_layers.items():
        abc = cat_a5g(abc)
        a5gs = [cat_a5g(n) for n in nodes]
        # 确定layer的总状态
        status = 'done'
        for n in a5gs:
            s = all_nodes[n]['status']
            if s == 'running':
                status = 'running'
                break
            elif s == 'error':
                status = 'error'
                break
            elif s == 'ready':
                status = 'ready'

        # 计算执行层进度
        timeleft = format_sum([all_nodes[n]['timeleft'] for n in a5gs])
        total_weight = sum([all_nodes[n]['weight'] for n in a5gs])

        layer_nodes = [{
            'a5g': n,
            'weight': all_nodes[n]['weight'],
            'ratio': all_nodes[n]['weight'] / total_weight,
            'percent': format_mul(all_nodes[n]['percent'], all_nodes[n]['weight'] / total_weight),
        } for n in a5gs]
        percent = format_sum([node['percent'] for node in layer_nodes])

        all_layers[abc] = {
            'abc': abc,
            'percent': percent,
            'status': status,
            'timeleft': timeleft,
            'weight': total_weight,
            'nodes': layer_nodes
        }

    running_layers = [cat_a5g(v) for v in task.running_layers]

    # ================ root ==================
    # 计算根节点（起始节点）的进度信息
    all_roots = {}
    for _a, layers_abc in task.mounted_roots.items():
        a = cat_a5g(_a)
        root = task.allroots[_a[0]]

        layers_abc = [cat_a5g(abc) for abc in layers_abc]
        layers = [all_layers[abc] for abc in layers_abc]
        total_weight = sum([layer['weight'] for layer in layers])
        root_layers = [{
            'abc': layer['abc'],
            # 'percent': layer['percent'] * layer['weight'] / total_weight,
            'percent': format_mul(layer['percent'], layer['weight'] / total_weight),
            'ratio': layer['weight'] / total_weight
        } for layer in layers]

        status = 'done'
        for layer in layers:
            s = layer['status']
            if s == 'running':
                status = 'running'
                break
            elif s == 'error':
                status = 'error'
                break
            elif s == 'ready':
                status = 'ready'

        # percent = sum([layer['percent'] for layer in root_layers])
        percent = format_sum([layer['percent'] for layer in root_layers])
        # try:
        #     timeleft = sum([layer['timeleft'] for layer in layers])
        # except TypeError:
        #     # None + int
        #     timeleft = None
        timeleft = format_sum([layer['timeleft'] for layer in layers])

        all_roots[a] = ({
            'a': a,
            'url': root.getdata('url'),
            'title': root.getdata('title'),
            'percent': percent,
            'timeleft': timeleft,
            'status': status,
            'weight': total_weight,
            'root': {
                'name': root.NAME,
                'sign': root.SIGN,
                'percent': root.progress.percent,
                'status': root.progress.status,
                'speed': root.progress.speed,
                'timeleft': root.progress.timeleft,
                'data': root.infodata()
            },
            'layers': root_layers,
        })

    running_roots = [cat_a5g(v) for v in task.running_roots]

    # 计算合计进度
    total_weight = sum([root['weight'] for root in all_roots.values()])
    # total_percent = sum([root['percent'] * root['weight'] / total_weight for root in all_roots.values()])
    total_percent = format_sum([format_mul(root['percent'], root['weight'] / total_weight)
                                for root in all_roots.values()])
    if all_roots:
        status = 'done'
        for root in all_roots.values():
            s = root['status']
            if s == 'running':
                status = 'running'
                break
            elif s == 'error':
                status = 'error'
                break
            elif s == 'ready':
                status = 'ready'
    else:
        status = 'ready'
    timeleft = format_sum([root['timeleft'] for root in all_roots.values()])

    return {
        'sign': task.sign,
        'url': task.url,
        'name': task.name,
        'title': task.title or task.sign,
        'options': task.options,
        'percent': total_percent,
        'timeleft': timeleft,
        'status': status,
        'allRoots': all_roots,
        'runningRoots': running_roots,
        'allLayers': all_layers if more else [],
        'runningLayers': running_layers,
        'allNodes': all_nodes if more else [],
        'runningNodes': running,
        'rawFlows': task.raw_flow_node if more else [],
    }


def get(sign: str):
    return __key_task.get(sign, None)


def stop(
    key: str,
):
    task = __key_task.get(key, None)
    if not task:
        raise DataNotFound(f'不存在的任务KEY: {key}')
    return task.stop()


def restart(
    key: str,
):
    pass