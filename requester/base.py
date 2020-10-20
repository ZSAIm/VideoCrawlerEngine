from functools import wraps, partial
from inspect import getfullargspec, iscoroutinefunction
from contextmgr import context_dict
from contexts import PROGRESS_CONTEXT, REQUEST_CONTEXT, WORKER_CONFIG_CONTEXT
from uitls import current_time
from worker import get_worker
from config import get_config, SECTION_WORKER
from traceback import format_exc
from contextlib import contextmanager
from traceback import print_exc
import threading


@contextmanager
def enter_request_context(request):
    with PROGRESS_CONTEXT.enter(request.progress), \
         REQUEST_CONTEXT.enter(request), \
         WORKER_CONFIG_CONTEXT.enter(dict(get_config(SECTION_WORKER, request.NAME))):
        yield


class Request:
    """ Request 请求对象是用来描述从脚本的开始到完成过程中的处理方式。
    name:           请求名称
    """
    NAME = None

    WEIGHT = 1
    SIMPLE = None

    __locale__ = ()

    @property
    def progress(self):
        return self.__progress__

    def start_request(self, context=None):
        with enter_request_context(self):
            ctx = context_dict()
            if context is None:
                context = {}

            ctx.update(context)

            self.progress.enqueue()
            return get_worker(self.NAME).submit(ctx)

    def end_request(self):
        """ 结束请求。"""
        raise NotImplementedError

    def subrequest(self):
        """ 返回该请求的子请求。 """
        return []

    def error_handler(self, exception):
        """ 异常处理。"""
        self.progress.error(format_exc())

    def get_data(self, name, default=None):
        result = self.__progress__.get_data(name, default)
        # if callable(result):
        #     result = result()
        return result

    async def stop(self):
        return await get_worker('stop').submit(self.progress.stop)

    def __repr__(self):
        return f'<{self.__class__.__name__}>'

    def __new__(cls, *args, **kwargs):
        inst = object.__new__(cls)
        inst.__progress__ = RequestProgress()

        subs = search_requests(args)
        subs.extend(search_requests(kwargs))
        inst.__subrequest__ = tuple(subs)
        return inst

    def __getitem__(self, item):
        return self.get_data(item)


def requester(request_name, weight=1, root=False):
    """ 简单请求构建器。
    Args:
        request_name: 请求者名称
        weight: 当前请求器在百分比percent中所占的权重
        root:
    """
    def wrapper(func):
        argnames, varargs, varkw, defaults, kwonlyargs, kwonlydefaults, annotations = getfullargspec(func)

        @wraps(func)
        def wrapped(*args, **kwargs):
            _worker = partial(inner_worker, *args, **kwargs)
            kws = {}

            # 设置默认的列表参数
            for i, v in enumerate(argnames[len(argnames) - len(defaults or ()):]):
                kws[v] = defaults[i]

            narg = min(len(args), len(argnames))
            # 设置列表参数
            for i in range(narg):
                kws[argnames[i]] = args[i]

            # 关键词转列表参数
            for k in tuple(kwargs):
                if k in argnames:
                    kws[k] = kwargs.pop(k)

            # 设置默认的关键词参数
            for k in kwonlyargs:
                kws[k] = kwargs.pop(k, kwonlydefaults[k])
            # 设置未定义的关键词参数
            kws.update({
                'args': args[narg:],
                'kwargs': kwargs
            })
            req = request_class(**kws)
            req.end_request = _worker
            return req

        if iscoroutinefunction(func):
            async def inner_worker(*args, **kwargs):
                return await func(*args, **kwargs)
        else:
            def inner_worker(*args, **kwargs):
                return func(*args, **kwargs)

        def __init__(self, **kwargs):
            self.args = ()
            self.kwargs = {}
            _ = {self.__setattr__(k, v) for k, v in kwargs.items()}

        def __repr__(self):
            return f'<{__name__}>'

        def subrequest(self):
            return self.__subrequest__

        __name__ = f'{request_name.title()}Requester'

        __slots__ = tuple(list(argnames) + kwonlyargs + ['args', 'kwargs'])

        class_namespace = {
            'NAME': request_name,
            'WEIGHT': weight,
            'SIMPLE': wrapped,
            'subrequest': subrequest,
            '__slots__': __slots__,
            '__init__': __init__,
            '__repr__': __repr__,
            '__doc__': func.__doc__,
            '__subrequest__': (),
        }

        if root:
            bases = (RootRequest,)
        else:
            bases = (Request,)
        request_class = type(__name__, bases, class_namespace)

        return wrapped
    return wrapper


def get_requester(name):
    """ 返回指定名称的请求器。
    Args:
        name: 请求器名称
    """
    for req_cls in Request.__subclasses__():
        if name == req_cls.NAME:
            if req_cls.SIMPLE:
                return req_cls.SIMPLE
            else:
                return req_cls
    return None


def _is_related_types(obj):
    return isinstance(obj, (Request, Option, Optional))


def search_requests(arg):
    def _list_tuple_set(o):
        for v in o:
            if _is_related_types(v):
                rs.append(v)
            else:
                _do(v)

    def _dict(o):
        for k, v in o.items():
            if _is_related_types(k):
                rs.append(k)
            else:
                _do(k)
            if _is_related_types(v):
                rs.append(v)
            else:
                _do(v)

    def _do(o):
        if isinstance(o, (list, tuple, set)):
            _list_tuple_set(o)
        elif isinstance(o, dict):
            _dict(o)
        elif _is_related_types(o):
            rs.append(o)

    rs = []
    _do(arg)
    return rs


class Brake:
    """ 请求制动器。"""
    def __init__(self):
        self.stopper_lst = []
        self.sema = threading.Semaphore(0)

    def run(self):
        with self.sema:
            for stopper in self.stopper_lst:
                try:
                    stopper()
                except Exception:
                    print_exc()

    def add_stopper(self, stopper):
        """ 仅允许非协程函数作为停止器。
        如果是协程函数，使用functools.partial(asyncio.run, stopper())来实现
        """
        assert not iscoroutinefunction(stopper)
        assert callable(stopper)
        self.stopper_lst.append(stopper)
        self.sema.release()

    def destroy(self):
        with self.sema._cond:
            self.sema._value = float('inf')
            self.sema._cond.notify_all()


class RequestProgress:

    def __init__(self):
        self.data = {}
        self.logs = []
        self._status = REQ_READY
        self._percent = 0
        self._speed = 0
        self._timeleft = float('inf')

        self.brake = Brake()

    @property
    def status(self):
        status = self._status
        return status() if callable(status) else status

    @status.setter
    def status(self, value):
        self._status = value

    @property
    def percent(self):
        percent = self._percent
        return percent() if callable(percent) else percent

    @percent.setter
    def percent(self, value):
        self._percent = value

    @property
    def speed(self):
        speed = self._speed
        return speed() if callable(speed) else speed

    @speed.setter
    def speed(self, value):
        self._speed = value

    @property
    def timeleft(self):
        timeleft = self._timeleft
        return timeleft() if callable(timeleft) else timeleft

    @timeleft.setter
    def timeleft(self, value):
        self._timeleft = value

    def add_stopper(self, stopper):
        """ 停止器。"""
        self.brake.add_stopper(stopper)

    def stop(self):
        """ """
        if self.status in (REQ_RUNNING, REQ_QUEUING):
            self.brake.run()

    def get_data(self, key, default=None, ignore_safe=True):
        result = self.data.get(key, default)
        if isinstance(result, CallableData):
            result = result()
        elif isinstance(result, (list, tuple, dict, int, str, bytes, set)):
            pass
        elif not ignore_safe:
            result = default
        return result

    def iter_data(self, safe=True):
        if safe:
            return iter([(k, self.get_data(k, ignore_safe=not safe)) for k, v in self.data.items()])
        else:
            return iter(self.data)

    def upload(self, **kwargs):
        """ 上传数据。
        :param
            **kwargs:     描述信息
        """
        for k, v in kwargs.items():
            self.data[k] = v

    def enqueue(self):
        self._status = REQ_QUEUING
        self.percent = 0

    def start(self):
        self._status = REQ_RUNNING
        self.percent = 0
        self.timeleft = float('inf')

    def close(self):
        self.brake.destroy()

    def task_done(self):
        if self.status == REQ_RUNNING:
            self._status = REQ_DONE
            self.percent = 100
            self.timeleft = 0

    def error(self, message):
        self._status = REQ_ERROR
        self.report('ERROR: ' + message)

    def success(self, message):
        self.report('SUCCESS: ' + message)

    def info(self, message):
        self.report('INFO: ' + message)

    def warning(self, message):
        self.report('WARNING: ' + message)

    def report(self, message):
        message = current_time() + ' ' + message
        self.logs.append(message)


class Optional:
    """ 可选请求列表 """
    __slots__ = '_options', '_selected'

    def __init__(self, options):
        """
        :param
            list:       可选择的项列表
            sort_key:   项目排序的key
        """
        self._options = options
        self._selected = None

    def __iter__(self):
        return iter(self._options)

    @property
    def selected(self):
        """ 返回被选择的项。"""
        if self._selected is None:
            raise ValueError('未选择的列表。')
        return self._selected

    def select(self, rule):
        """ 根据rule来选择最恰当的选项。
        :param
            rule:   选择规则
                - high:     最高质量 100
                - middle:   中等质量 50
                - low:      最低质量 1
                - %d:       1-100   [1,100] - (注意: 倾向于高质量。)
        """
        if rule == 'high':
            rule = 100
        elif rule == 'low':
            rule = 1
        elif rule == 'middle':
            rule = 50

        if isinstance(rule, int) and 1 <= rule <= 100:
            selected = self._options[max(0, int((100-rule) * len(self._options) / 100) - 1)]
        else:
            selected = self._options[0]
        self._selected = selected
        return selected

    def __getattr__(self, item):
        return getattr(self._selected, item)

    def __repr__(self):
        return repr(self._selected)


class Option:
    """ 可选列表的选项 """
    __slots__ = '_content', 'descriptions'

    def __init__(self, content, descriptions=None):
        self._content = content
        if descriptions is None:
            descriptions = {}
        self.descriptions = descriptions

    def __repr__(self):
        return str(self._content)

    def __getattr__(self, item):
        return getattr(self._content, item)

    @property
    def content(self):
        return self._content


REQ_READY = 'ready'
REQ_QUEUING = 'queuing'
REQ_RUNNING = 'running'
REQ_STOPPED = 'stopped'
REQ_WARNING = 'warning'
REQ_ERROR = 'error'
REQ_DONE = 'done'


class RootRequest(Request):
    NAME = 'root'

    discard_next = False

    def end_request(self):
        raise NotImplementedError


def factor_request(request, rule):
    """ 分解请求工作链。注意这可能存在无限迭代问题。
    Args:
        request: 被分解的请求
        rule: 请求选择规则
    """
    def _select(o):
        """ 处理选择请求的关系链。"""
        if isinstance(o, Request):
            return o
        elif isinstance(o, Option):
            return _select(o.content)
        elif isinstance(o, Optional):
            return _select(o.select(rule))

        raise RuntimeError()

    def _lookup(o):
        """ 建立工作流串并行链。"""
        o = _select(o)
        if isinstance(o, RootRequest):
            srp.append(o)
            return None
        s = []
        for req in o.subrequest():
            r = _lookup(req)
            if r is None:
                return None
            s.extend(r)

        if s:
            return [s, o]
        return [o]

    srp = []
    flow = _lookup(request)
    return flow, srp


class CallableData(partial):
    pass


callable_data = CallableData
