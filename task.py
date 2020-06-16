import asyncio
from hashlib import md5
from _request import (get_requester, RootRequest,
                      REQ_DONE, REQ_QUEUING, REQ_RUNNING, REQ_ERROR, REQ_WARNING, )
from debugger import dbg
from requester.request import script_request, requester
from script import select_script, supported_script
from workflow import factor_request, Workflow, run_workflow, PendingWorkflow, BrokenWorkflow
from traceback import format_exc
import shutil
import os


CODE_SUCCESS = 0
CODE_EXISTED = -2
CODE_UNSUPPORTED = -1

tasks = {}


class Task:
    def __init__(self, key, url, task, **kwargs):
        self.key = key
        self.url = url
        self.task = task
        task.start_request()

    def get_key(self):
        return self.key

    def task_details(self, key):
        pass

    def task_list(self):
        task = self.task
        flows = task.get_data('flows', ())

        sketch = task.sketch()
        sketch.update({
            'url': self.url,
            'n': len(flows),
            'flows': [flow.sketch() for flow in flows],
        })
        return sketch

    def stop(self):
        self.task.stop()

    def __repr__(self):
        return f'<Task key={self.key}>'


def new_task(url, rule=None, **kwargs):
    global tasks
    key = md5(url.encode('utf-8')).hexdigest()
    code = CODE_SUCCESS
    if key in tasks:
        code = CODE_EXISTED
    scripts = supported_script(url)
    if not scripts:
        code = CODE_UNSUPPORTED

    if scripts and code == CODE_SUCCESS:
        sel_script = select_script(scripts)
        tasks[key] = Task(key, url, task_request(url, rule))
    else:
        sel_script = None

    return {
        'code': code,
        'key': key,
        'supported': scripts,
        'selected': sel_script,
        'url': url,
        'rule': rule
    }


def get_task_list_info():
    global tasks
    task_list = {k: v.task_list() for k, v in tasks.items()}
    return task_list


def stop_all():
    for task in tasks.values():
        task.stop()


@requester('task', sketch_data=('title', ))
async def task_request(url, rule, **kwargs):
    """
    Uploaded Data:
        flows: 工作流列表
        scripts: 子脚本列表
        title: 任务标题


    """
    scripts = []
    flows = []
    stopped = False
    dbg.upload(
        scripts=scripts,
        flows=flows,
    )

    async def execute_script(a, srp_req):
        """ 执行脚本，并为脚本的项目请求生成工作流。
        Args:
            a: 被执行脚本号
            srp_req: 脚本请求
        """
        nonlocal work_sema, work_queue
        try:
            async with work_sema:
                rs = await srp_req.start_request()
        except BaseException as err:
            dbg.warning(f'[SCRIPTS[{a}]]\n{format_exc()}')
            flows[a] = BrokenWorkflow()
            return
        flow = []
        other_srp = []
        desc = {}
        script_config = srp_req.get_data('script').config
        sel_rule = srp_req.get_data('rule')
        for item in rs:
            fl, srp = factor_request(item, sel_rule, desc)
            if fl:
                for name in script_config['append']:
                    fl.append(get_requester(name)())
                flow.append(fl)

            if srp:
                other_srp.extend(srp)

        workflow = Workflow(a, srp_req, flow)
        flows[a] = workflow
        with dbg.run(srp_req) as d:
            d.upload(**desc)

        # 创建临时目录
        tempdir = srp_req.get_data('tempdir')
        if not os.path.isdir(tempdir):
            os.mkdir(tempdir)

        await work_queue.put(workflow)

        # 初始标题作为主标题
        if not dbg.get_data('title'):
            dbg.upload(title=srp_req.get_data('title'))

        if not srp_req.discard_next:
            [await work_queue.put(srp) for srp in other_srp]

    def _percent():
        """ 任务完成百分比。 """
        p = [flow.percent() for flow in flows]

        if not p:
            return 0
        return round(sum(p) / len(p), 2)

    def _status():
        if any([flow.status() == REQ_ERROR for flow in flows]):
            if all([flow.status() == REQ_ERROR for flow in flows]):
                status = REQ_ERROR
            else:
                status = REQ_WARNING
        else:
            if all([flow.status() == REQ_DONE for flow in flows]):
                status = REQ_DONE
            else:
                status = REQ_RUNNING

        return status

    def _task_done_cb(f):
        """ 任务完成回调，用于判断是否所有工作流已完成或发生错误。
        任意一个工作流还在工作中都不会停止任务执行。
        """
        nonlocal work_queue, stopped
        work_queue.task_done()
        if stopped or not any([flow.status() in (REQ_QUEUING, REQ_RUNNING) for flow in flows]):
            work_queue.put_nowait(None)

            # 如果工作流成功执行完，则清除改任务的临时目录
            if isinstance(f.task, Workflow):
                if f.task.status() == REQ_DONE:
                    tempdir = f.task.root.get_data('tempdir')
                    shutil.rmtree(tempdir, ignore_errors=True)

    def _stopper():
        nonlocal stopped
        stopped = True
        for flow in flows:
            flow.stop()

    loop = asyncio.get_running_loop()

    work_queue = asyncio.Queue()
    work_sema = asyncio.Semaphore(2)

    dbg.set_percent(_percent)
    dbg.set_status(_status)

    dbg.add_stopper(_stopper)

    starter = script_request(url, rule, discard_next=False)
    await work_queue.put(starter)
    while True:
        task = await work_queue.get()
        if task is None:
            work_queue.task_done()
            break
        if isinstance(task, RootRequest):
            new_id = len(scripts)
            scripts.append(task)
            # 入列等待工作流
            flows.append(PendingWorkflow())
            coro = execute_script(new_id, task)
        elif isinstance(task, Workflow):
            coro = run_workflow(task, work_sema)
        else:
            dbg.warning(f'无法处理的任务类型{type(task)}: {str(task)}')
            continue

        fut = asyncio.run_coroutine_threadsafe(coro, loop=loop)
        # 携带协程任务对象，以便回调使用
        fut.task = task
        fut.add_done_callback(_task_done_cb)

