from functools import wraps, partial
from inspect import getfullargspec, iscoroutinefunction

from context import impl_ctx
from utils import current_time
from worker import get_worker
from traceback import format_exc
import threading
from queue import Queue
import re


class Request:
    """ Request 请求对象是用来描述从脚本的开始到完成过程中的处理方式。
    name:           请求名称


    """
    name = None

    WEIGHT = 1
    __simple__ = None

    @property
    def progress(self):
        return self.__progress__

    def start_request(self, context=None):
        if context is None:
            context = {}

        context = impl_ctx(context)

        self.progress.enqueue()
        return get_worker(self.name).submit(self, context)

    def end_request(self):
        """ 结束请求。"""
        raise NotImplementedError

    def subrequest(self):
        """ 返回该请求的子请求。 """
        return []

    def error_handler(self, exception):
        """ 异常处理。"""
        self.progress.error(format_exc())

    def getresponse(self):
        """ 返回响应 """
        return self.__progress__.details()

    def get_data(self, name, default=None):
        return self.__progress__.data.get(name, default)

    def sketch(self):
        sketch = self.__progress__.sketch()
        sketch.update({
            'name': self.name,
        })
        return sketch

    def details(self, log=False):
        return self.__progress__.details(log)

    def stop(self):
        return self.progress.stop()

    def __repr__(self):
        return f'<{self.__class__.__name__}>'

    def __new__(cls, *args, **kwargs):
        inst = object.__new__(cls)
        inst.__progress__ = RequestProgress()
        return inst


def requester(request_name,
              weight=1,
              sketch_data=(),
              bases_cls=None,
              root=False,
              auto_search=True):
    """ 简单请求构建器。
    Args:
        request_name: 请求者名称
        weight: 当前请求器在百分比percent中所占的权重
        sketch_data: 上传upload的数据中被sketch()返回的数据字段组成的列表。
        bases_cls:
        root:
        auto_search:
    """
    def wrapper(func):
        nonlocal bases_cls
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
            req = result(**kws)
            req.end_request = _worker
            if callable(initializer):
                initializer(req)
            if auto_search:
                subs = _search_request(args)
                subs.extend(_search_request(kwargs))
                req.__subrequest__ = tuple(subs)
            return req

        initializer = None

        def wrapped_init(init_func):
            nonlocal initializer
            initializer = init_func
            return init_func

        wrapped.initializer = wrapped_init

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

        if sketch_data:
            def sketch(self):
                sk = Request.sketch(self)
                for k in sketch_data:
                    sk[k] = self.get_data(k)
                return sk
        else:
            sketch = Request.sketch

        __name__ = f'{request_name.title()}Request'

        __slots__ = tuple(list(argnames) + kwonlyargs + ['args', 'kwargs'])

        class_namespace = {
            'name': request_name,
            'subrequest': subrequest,
            'sketch': sketch,
            'WEIGHT': weight,
            '__slots__': __slots__,
            '__init__': __init__,
            '__repr__': __repr__,
            '__doc__': func.__doc__,
            '__subrequest__': (),
            '__simple__': wrapped,
        }

        if bases_cls is None:
            bases_cls = []
        if root:
            bases = (RootRequest,)
        else:
            bases = (Request,)
        if bases[0] not in bases_cls:
            bases_cls = bases + tuple(bases_cls)
        result = type(__name__, bases_cls, class_namespace)

        return wrapped
    return wrapper


def get_requester(name):
    """ 返回指定名称的请求器。
    Args:
        name: 请求器名称
    """
    for req_cls in Request.__subclasses__():
        if name == req_cls.name:
            if req_cls.__simple__:
                return req_cls.__simple__
            else:
                return req_cls
    return None


def _is_related_types(obj):
    return isinstance(obj, (Request, Option, Optional))


def _search_request(arg):
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
        typ = type(o)
        if typ in (list, tuple, set):
            _list_tuple_set(o)
        elif typ is dict:
            _dict(o)
        elif _is_related_types(o):
            rs.append(o)

    rs = []
    _do(arg)
    return rs


class RequestProgress:
    EXPORT_ATTR = frozenset({
        'percent', 'speed', 'timeleft', 'status'
    })

    EXPORT_METH = frozenset({
        'upload', 'upload_default', 'start', 'close', 'task_done', 'get_data',
        'error', 'success', 'info', 'warning', 'report', 'sketch', 'details', 'add_stopper'
    })

    __slots__ = ('data', 'logs', '_status', '_percent', '_speed', '_timeleft',
                 '__worker__', '_stoppers', '_stoppers', '_closed', '_lock', '_started')

    def __init__(self):
        self.data = {}
        self.logs = []

        self._status = REQ_READY
        self._percent = 0
        self._speed = 0
        self._timeleft = float('inf')
        self.__worker__ = None
        self._stoppers = Queue()
        self._lock = threading.Lock()
        self._closed = False
        self._started = False

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

    def sketch(self):
        return {
            'percent': self.percent,
            'status': self.status,
            'speed': self.speed,
            'timeleft': self.timeleft,
            'latest': (self.logs and self.logs[-1]) or ''
        }

    def details(self, log=False):
        data = {k: v() if callable(v) else v for k, v in self.data.items()}
        info = self.sketch()
        info.update({
            'data': data,
        })
        if log:
            info['logs'] = self.logs
        return info

    def get_data(self, key, default=None):
        return self.data.get(key, default)

    def upload(self, **kwargs):
        """ 上传数据。
        :param
            **kwargs:     描述信息
        """
        for k, v in kwargs.items():
            self.data[k] = v

    def upload_default(self, key, default):
        if key not in self.data:
            self.data[key] = default

    def enqueue(self, message=''):
        self._status = REQ_QUEUING
        self.percent = 0
        self.report('ENQUEUE:' + message)

    def start(self, worker=None):
        with self._lock:
            self._started = True
            self._status = REQ_RUNNING
            self.percent = 0
            self.timeleft = float('inf')
            self.report('START:')
            self.__worker__ = worker

    def stop(self):
        self._status = REQ_STOPPED
        with self._lock:
            if self._started:
                if self._closed:
                    return False
                while True:
                    stopper = self._stoppers.get()
                    if stopper is None:
                        break
                    try:
                        stopper()
                    except:
                        pass

    def close(self, *args, **kwargs):
        self._stoppers.put(None)

    def add_stopper(self, func):
        self._stoppers.put(func)

    def task_done(self, message=''):
        if self.status == REQ_RUNNING:
            self._status = REQ_DONE
            self.percent = 100
            self.timeleft = 0
            self.report('TASK DONE:' + message)

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


class Response:
    def __init__(self, request, **desc):
        self.__name = request.name
        desc.update(request.progress.data)
        self.__datadict = desc

    def __getattr__(self, item):
        return self.__datadict[item]

    def __repr__(self):
        return '<%s %s>' % (self.__name, str(self.__dict__))


REQ_READY = 0
REQ_QUEUING = 1
REQ_RUNNING = 2
REQ_STOPPED = 3
REQ_WARNING = 4
REQ_ERROR = -1
REQ_DONE = 5


RE_VALID_PATHNAME = re.compile(r'[\\/:*?"<>|\r\n]+')


class RootRequest(Request):
    name = 'root'

    discard_next = False

    def end_request(self):
        raise NotImplementedError


def _all_status(iteration):
    status = REQ_DONE
    for i in iteration:
        _b = i.status()
        if _b == REQ_ERROR:
            status = REQ_ERROR
            break
        elif _b == REQ_STOPPED:
            status = REQ_STOPPED
            break
        elif _b == REQ_RUNNING:
            status = REQ_RUNNING
            break
        elif _b != REQ_DONE:
            status = REQ_QUEUING
            break
    return status


def requester_info():
    return_dict = {}
    for v in Request.__subclasses__():
        return_dict[v.name] = {
            'weight': v.WEIGHT
        }
    return return_dict

