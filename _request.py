from functools import wraps, partial
from inspect import getfullargspec, iscoroutinefunction

from context import impl_ctx
from utils import current_time
from worker import get_worker
import re


class Request:
    """ Request 请求对象是用来描述从脚本的开始到完成过程中的处理方式。
    name:           请求名称


    """
    name = None
    __progress__ = None

    @property
    def progress(self):
        return self.__progress__

    def is_active(self):
        return bool(self.__progress__)

    def start_request(self, context=None):
        if context is None:
            context = {}

        if self.__progress__ is None:
            self.__progress__ = RequestProgress()

        context = impl_ctx(context)

        self.__progress__.enqueue()
        return get_worker(self.name).submit(self, context)

    def end_request(self):
        """ 结束请求。"""
        raise NotImplementedError

    def subrequest(self):
        """ 返回该请求的子请求。 """
        return []

    def error_handler(self, exception):
        """ 异常处理。"""
        raise

    def getresponse(self):
        """ 返回响应 """
        return self.__progress__.details()

    def get_data(self, name, default=None):
        return self.__progress__.data.get(name, default)

    def sketch(self):
        return self.__progress__.sketch()

    def details(self, log=False):
        return self.__progress__.details(log)

    def pause(self):
        return NotImplemented

    def stop(self):
        return NotImplemented

    def __repr__(self):
        return f'<{self.__class__.__name__}>'


def requester(request_name,
              sketch_data=(),
              auto_search=True):
    """ 简单请求构建器。
    Args:
        request_name: 请求者名称
        sketch_data: 上传upload的数据中被sketch()返回的数据字段组成的列表。
        auto_search:
    """
    def wrapper(func):
        argnames, varargs, varkw, defaults, kwonlyargs, kwonlydefaults, annotations = getfullargspec(func)

        @wraps(func)
        def wrapped(*args, **kwargs):
            kws = {}
            narg = min(len(args), len(argnames))
            # 设置列表参数
            for i in range(narg):
                kws[argnames[i]] = args[i]

            # 设置已定义的关键词参数
            for k in kwonlyargs:
                kws[k] = kwargs.pop(k, kwonlydefaults[k])
            # 设置未定义的关键词参数
            kws.update({
                'args': args[narg:],
                'kwargs': kwargs
            })
            req = result(**kws)
            req.end_request = partial(inner_worker, *args, **kwargs)
            if auto_search:
                subs = _search_request(args)
                subs.extend(_search_request(kwargs))
                req.__subrequest__ = tuple(subs)
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
            return f'<{self.__name__}>'

        def subrequest(self):
            return self.__subrequest__

        __doc__ = f''

        __name__ = f'{request_name.title()}Request'

        __slots__ = tuple(list(argnames) + kwonlyargs + ['args', 'kwargs'])
        class_namespace = {
            'name': request_name,
            'subrequest': subrequest,
            '__slots__': __slots__,
            '__init__': __init__,
            '__repr__': __repr__,
            '__subrequest__': (),
            '__simple__': wrapped
        }

        result = type(__name__, (Request, ), class_namespace)

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
                    _dict(arg)
                elif _is_related_types(arg):
                    rs.append(arg)

            rs = []
            _do(arg)
            return rs

        return wrapped
    return wrapper


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


def get_requester(name):
    """ 返回指定名称的请求器。
    Args:
        name: 请求器名称
    """
    for req_cls in Request.__subclasses__():
        if name == req_cls.name:
            if getattr(req_cls, '__simple__', None):
                return req_cls.__simple__
            else:
                return req_cls
    return None


def _is_related_types(obj):
    return isinstance(obj, (Request, Option, Optional))


class RequestProgress:
    EXPORT_ATTR = frozenset({
        'percent', 'speed', 'timeleft', 'status'
    })

    EXPORT_METH = frozenset({
        'upload', 'upload_default', 'start', 'close', 'task_done', 'get_data',
        'error', 'success', 'info', 'warning', 'report', 'sketch', 'details'
    })

    def __init__(self):
        self.data = {}
        self.logs = []

        self._status = REQ_READY
        self._percent = 0
        self._speed = 0
        self._timeleft = float('inf')

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

    def start(self, message=''):
        self._status = REQ_RUNNING
        self.percent = 0
        self.timeleft = float('inf')
        self.report('START:' + message)

    def close(self, *args, **kwargs):
        pass

    def task_done(self, message=''):
        self._status = REQ_DONE
        self.percent = 100
        self.timeleft = 0
        self.report('END:' + message)

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
REQ_SUSPENDED = 3
REQ_ERROR = -1
REQ_DONE = 5


RE_VALID_PATHNAME = re.compile(r'[\\/:*?"<>|\r\n]+')


class RootRequest(Request):
    name = 'root'

    def end_request(self):
        raise NotImplementedError


