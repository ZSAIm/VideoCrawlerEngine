
from _request import (Optional, Option, requester, Request, RootRequest,
                      _is_related_types, get_requester, RequestProgress,
                      RE_VALID_PATHNAME)
from script import select_script, supported_script, get_script
from workflow import RequestWorkflow, factor_request, run_workflow
from nbdler import Request as DlRequest, dlopen
from subprocess import list2cmdline
from nbdler.uri import URIs
from debugger import dbg
import asyncio
import shutil
import os


def next_script(url, descriptions=None, **kwargs):
    """ 下一个脚本请求。 """
    return Option(ScriptRequest(url, discard_script=True, **kwargs),
                  descriptions)


def script_request(url, **kwargs):
    return ScriptRequest(url, discard_script=True, **kwargs)


@requester('jsruntime')
def jsruntime(session, **kwargs):
    session.leave()


@requester('convert')
async def convert():
    import _ffmpeg
    results = []

    merges = dbg.flow.find_by_name('ffmpeg')
    for pathname in [merge.get_data('pathname') for merge in merges]:
        results.append(pathname)

    if not results:
        # 对于没有经过ffmpeg处理的工具，默认将下载的音频资源全经过
        downloads = dbg.flow.find_by_name('download')
        for filename in [download.get_data('pathname') for download in downloads]:
            converter = _ffmpeg.convert(filename)
            node = dbg.flow.attach_node(converter)
            result = await node.start_request()
            results.append(converter.get_data('pathname'))

    # 修改文件名并移动文件
    storage_dir = dbg.root_info['storage_dir']
    for pathname in results:
        path, name = os.path.split(pathname)
        dst_name = name.split('.', 1)[-1]
        dst_pathname = os.path.join(os.path.realpath(storage_dir), dst_name)
        shutil.move(pathname, dst_pathname)


@requester('cleanup')
async def cleanup():
    if dbg.root_info['remove_tempdir']:
        tempdir = dbg.root_info['tempdir']
        shutil.rmtree(tempdir)


class DownloadRequest(Request, URIs):
    name = 'download'

    def __init__(self, **kwargs):
        URIs.__init__(self)
        if kwargs:
            self.put(**kwargs)

    async def end_request(self):
        # '[32-0-01-9].example'
        a, b, c, d, e = dbg.flow.abcde
        name = f'[{"-".join([f"{_:02}" for _ in [a, b, c, d]])}].{dbg.root_info["title"]}'
        path = dbg.root_info['tempdir']
        file_path = os.path.join(path, name)
        rq = DlRequest(file_path=file_path)
        for uri in self.dumps():
            uri.pop('id')
            rq.put(**uri)

        exception = None
        print(name)
        async with dlopen(rq) as dl:
            dbg.upload(
                size=dl.file.size,
                pathname=dl.file.pathname,
            )
            dbg.set_percent(dl.percent_complete)
            dbg.set_timeleft(dl.remaining_time)
            dbg.set_speed(lambda: f'{(dl.transfer_rate() / 1024):.2f} kb/s')

            dl.start(loop=asyncio.get_running_loop())
            while not dl._future:
                await asyncio.sleep(0.01)

            async for exception in dl.aexceptions():
                dbg.warning(exception.exc_info)
                print(exception)
                await dl.apause()
            await dl.ajoin()

        if exception:
            # 若发生异常，抛出异常
            raise exception

        # 更新文件信息
        dbg.upload(
            pathname=dl.file.pathname,
            size=dl.file.size,
        )


@requester('ffmpeg')
async def ffmpeg(inputs, callable_cmd, **kwargs):
    from _ffmpeg import FFmpegEngine

    def input2pathname(input):
        if isinstance(input, str):
            return input
        elif _is_related_types(input):
            return input.get_data('pathname')
        assert input

    def percent():
        nonlocal time_length, _ffmpeg
        return _ffmpeg.length() * 100 / (time_length or float('info'))

    time_length = dbg.root_info.get_data('length', None)

    # '[32-0-01-9].example'
    a, b, c, d, e = dbg.flow.abcde
    name = f'[{"-".join([f"{_:02}" for _ in [a, b, c, d, *e]])}].{dbg.root_info["title"]}'
    path = dbg.root_info['tempdir']

    file_path = os.path.join(path, name + dbg.root_info['to_format'])

    inputs = inputs
    if not isinstance(inputs, (list, tuple, set)):
        inputs = [inputs]

    cmd = callable_cmd(
        inputs=[input2pathname(input) for input in inputs],
        output=file_path,
        **kwargs
    )

    source = os.path.join(dbg.config['source'], dbg.config['name'])

    if isinstance(cmd, (list, tuple)):
        cmd = [source] + list(cmd)
        cmd = list2cmdline(cmd)
    else:
        cmd = f'{source} ' + cmd

    if dbg.config['overwrite']:
        cmd += ' -y'

    process = await asyncio.create_subprocess_shell(
        cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _ffmpeg = FFmpegEngine(process)
    dbg.set_speed(_ffmpeg.speed)
    dbg.set_percent(percent)

    dbg.upload(
        cmd=cmd,
        pathname=file_path
    )

    await _ffmpeg.run(timeout=dbg.config.get('timeout', None))


class TaskRequest(Request):
    name = 'task'

    def __init__(self, url, rule, **kwargs):
        self.url = url
        self.rule = rule
        self.kwargs = kwargs

        self.starter = ScriptRequest(url, rule, discard_script=False)
        self.scripts = []
        self.flows = []

    async def end_request(self):

        async def execute_script(a, srp_request):
            """ 执行脚本，并为脚本的项目请求生成工作流。
            Args:
                a: 被执行脚本号
                srp_request: 脚本请求
            """
            nonlocal work_sema, work_queue

            async with work_sema:
                rs = await srp_request.start_request()

            flows = []
            other_srp = []
            desc = {}
            for item in rs:
                flow, srp = factor_request(item, self.rule, desc)
                if flow:
                    for name in srp_request.script.config['append']:
                        flow.append(get_requester(name)())
                    flows.append(flow)

                if srp:
                    other_srp.extend(srp)

            workflow = RequestWorkflow(a, srp_request, flows)
            self.flows[a] = workflow
            with dbg.run(srp_request) as d:
                d.upload(**desc)

            await work_queue.put(workflow)

            # 初始标题作为主标题
            if not dbg.get_data('title'):
                dbg.upload(title=srp_request.get_data('title'))

            if not srp_request.discard_script:
                [await work_queue.put(srp) for srp in other_srp]

        def percent():
            """ 任务完成百分比。 """
            p = [[node.cont.progress.percent if node.is_active() else 0
                  for node in flow.every()] for flow in self.flows if flow]
            p = [sum(i)/len(i) for i in p if i]
            if not p:
                return 0
            return sum(p) / len(p)

        loop = asyncio.get_running_loop()

        work_queue = asyncio.Queue()
        work_sema = asyncio.Semaphore(2)

        dbg.set_percent(percent)

        await work_queue.put(self.starter)
        while True:
            task = await work_queue.get()
            if isinstance(task, ScriptRequest):
                new_id = len(self.scripts)
                self.scripts.append(task)
                self.flows.append(None)
                coro = execute_script(new_id, task)
            elif isinstance(task, RequestWorkflow):
                coro = run_workflow(task, work_sema)
            else:
                dbg.warning(f'无法处理的任务类型{type(task)}: {str(task)}')
                continue

            fut = asyncio.run_coroutine_threadsafe(coro, loop=loop)
            fut.add_done_callback(lambda f: work_queue.task_done())

    def getresponse(self):
        for flow in self.flows:
            pass

    def sketch(self):
        sketch = super().sketch()
        sketch.update({
            'n': len(self.scripts),
            'title': self.get_data('title'),
        })
        return sketch

    def details(self, log=False):
        def _node_sketch(node):
            sketch = node.cont.sketch()
            abcde = node.abcde
            sketch.update({
                'abcde': str(abcde),
            })
            return sketch

        details = self.__progress__.details(True)
        flow_sketch = []
        for flow in self.flows:
            if not flow:
                continue
            flow_sketch.append(
                [_node_sketch(node) for node in flow.every() if node.is_active()])
        details.update({
            'n': len(flow_sketch),
            'flows': flow_sketch
        })
        return details


class ScriptRequest(RootRequest):
    """ 脚本请求任务 """
    name = 'script'

    def __init__(self, url,
                 rule=None,
                 discard_script=False,
                 script=None,
                 **kwargs):
        self.url = url
        self.rule = rule
        self.kwargs = kwargs
        self.discard_script = discard_script
        self.__progress__ = RequestProgress()

        self.script = script

    def end_request(self):
        script = self.script
        if script is None:
            name = select_script(supported_script(self.url))
            script = get_script(name)
            self.script = script

        script_config = script.config

        # 请求来源脚本请求
        dbg.upload(
            url=self.url,
            name=self.script.name,
        )

        # 创建并运行脚本
        script(self.url, self.rule, discard_script=self.discard_script).run()

        # 合法文件路径
        origin_title = dbg.get_data('title')
        title = RE_VALID_PATHNAME.sub('_', origin_title)

        # 创建临时目录
        tempdir = os.path.join(dbg.config['tempdir'],
                               self.script.name,
                               title)
        tempdir = os.path.realpath(tempdir)
        if not os.path.isdir(tempdir):
            os.mkdir(tempdir)

        storage_dir = os.path.join(script_config['storage_dir'], self.script.name)

        dbg.upload(
            title=title,
            tempdir=tempdir,
            storage_dir=storage_dir,
            remove_tempdir=script_config.get('remove_tempdir', True),
            to_format=script_config.get('to_format', ['.mp4'])[0]

        )

        return self.get_data('items', [])

    def subrequest(self):
        return self.get_data('items', [])

    def sketch(self):
        sketch = super().sketch()
        sketch.update({
            'title': self.get_data('title'),

        })
        return sketch

    def __repr__(self):
        return f'<ScriptRequest "{self.url}">'


download = DownloadRequest
# ffmpeg = FFmpegRequest


__all__ = ('download',
           # 'FFmpegRequest',
           'ffmpeg',
           'cleanup',
           'convert',
           'requester',
           'TaskRequest')