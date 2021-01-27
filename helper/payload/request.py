from helper.codetable import NodeState
from helper.ctxtools.mgr import copy_context_to_dict
from inspect import getfullargspec, iscoroutinefunction
from helper.ctxtools.vars.request import (
    progress_mapping_context,
    request_mapping_context,
    config_context,
    self_request
)
from utils.common import current_time
from helper.worker import get_worker, executor
from functools import wraps, partial
from helper.conf import get_conf
from traceback import format_exc
from contextlib import contextmanager, ExitStack
from traceback import print_exc
from typing import (
    Any,
    ClassVar,
    Tuple,
    List,
    Dict,
    Callable,
    Union,
    TypeVar,
    Optional,
)
from pydantic import BaseModel
from concurrent.futures import Future as threadFuture
from asyncio.futures import Future as asyncFuture
from .flow import FlowPayload
import threading
import asyncio


T = TypeVar('T')


def inline_prop(name: str):
    def setter(self, value: Union[Callable[[], T], T]) -> None:
        setattr(self, name, value)

    def getter(self) -> T:
        value = getattr(self, name)
        return value() if callable(value) else value

    return property(
        fget=getter,
        fset=setter,
    )


class Progress(object):
    """ """
    data: Dict
    logs: List

    __status__: str = NodeState.READY
    __percent__: float = 0
    __speed__: Union[float, str, int] = 0
    __timeleft__: float = float('inf')

    status = inline_prop('__status__')
    percent = inline_prop('__percent__')
    speed = inline_prop('__speed__')
    timeleft = inline_prop('__timeleft__')

    def __init__(self):
        self.data = {}
        self.logs = []

        self.stopmaker = StopMaker()

    def add_stopper(self, stopper):
        """ 停止器。"""
        self.stopmaker.add_stopper(stopper)

    def stop(self):
        """ """
        if self.status in (NodeState.RUNNING, NodeState.QUEUING):
            self.stopmaker.run()

    def getdata(self, key, default=None):
        result = self.data.get(key, default)
        if callable(result):
            result = result()
        return result

    def iterdata(self):
        return iter(self.data.items())

    def upload(self, **kwargs):
        for k, v in kwargs.items():
            self.data[k] = v

    def commit(self, item):
        pass

    def enqueue(self):
        self.status = NodeState.QUEUING
        self.percent = 0

    def start(self):
        self.status = NodeState.RUNNING
        self.percent = 0
        self.timeleft = float('inf')

    def close(self):
        self.stopmaker.destroy()

    def task_done(self):
        if self.status == NodeState.RUNNING:
            self.__status__ = NodeState.DONE
            self.percent = 100
            self.timeleft = 0

    def error(self, message):
        self.status = NodeState.ERROR
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

    def __repr__(self):
        msg = ' '.join([
            f'status={self.status}',
            f'percent={self.percent}',
            f'speed={self.speed}',
            f'timeleft={self.timeleft}',
        ])
        return f'<Progress {msg}>'


class Requester(FlowPayload):
    """ Request 请求对象是用来描述从脚本的开始到完成过程中的处理方式。
    """
    NAME: str
    WEIGHT: float

    progress: Progress

    __infomodel__: BaseModel = None
    __inherit__: bool = True

    __point__: Tuple[Union[int, Tuple], ...] = ()

    # 若属于异步协程任务，由执行器赋值，退出线程后重置为None
    __loop__: Optional[asyncio.BaseEventLoop] = None

    __constructor__ = None
    __decorated__ = None

    def start_request(
        self,
        context=None
    ) -> Union[threadFuture, asyncFuture]:
        """ 将请求交给工作线程池进行排队处理。
        在转交工作线程处理之前将当前的上下文环境拷贝一份交给工作线程。
        以保持上下文的连贯性。
        Args；
            context: 该上下文管理器允许
        """
        with apply_requester_context(self):
            new_context = copy_context_to_dict(inherit_scope=self.__inherit__)
            if context is None:
                context = {}

            new_context.update(context)

            self.progress.enqueue()
            return executor.submit(get_worker(self.NAME), context=new_context)

    def __make__(self, *args, **kwargs) -> FlowPayload:
        return self

    def end_request(self) -> Any:
        """ 结束请求。"""
        raise NotImplementedError

    def error_handler(self, exception) -> None:
        """ 异常处理。"""
        self.progress.error(format_exc())

    def getdata(self, name, default=None) -> Any:
        result = self.progress.getdata(name, default)
        return result

    def iterdata(self):
        return self.progress.iterdata()

    def infodata(self):
        if not self.__infomodel__:
            return {}
        return {
            k: self.getdata(k)
            for k in self.__infomodel__.__fields__.keys()
        }

    async def stop(self) -> None:
        return await executor.submit(
            get_worker('stopper'),
            args=(self.progress.stop,)
        )

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__}>'

    def __new__(cls, *args, **kwargs):
        inst = super().__new__(cls, *args, **kwargs)
        inst.progress = Progress()
        return inst

    def __getitem__(self, item):
        return self.getdata(item)

    def upload(self, **kwargs):
        for k, v in kwargs.items():
            self.progress.data[k] = v


def requester(
    request_name: str,
    weight: float = 1,
    root: bool = False,
    infomodel: ClassVar[BaseModel] = None,
    inherit: bool = True,
    no_payload: bool = False,
):
    """ 简单请求构建器。
    Args:
        request_name: 请求者名称
        weight: 当前请求器在百分比percent中所占的权重
        root:
        infomodel: 有效数据类型
        inherit: 从父节点继承上下文
        no_payload: 是否禁用搜索参数中的payload
    """
    def wrapper(func) -> Callable:
        """ 创建请求器构造器（类）。"""
        (
            argnames,
            varargs,
            varkw,
            defaults,
            kwonlyargs,
            kwonlydefaults,
            annotations
        ) = getfullargspec(func)

        @wraps(func)
        def wrapped(*args, **kwargs) -> Requester:
            """ 请求器参数到实例参数的转接初始化。"""
            _worker = partial(inner, *args, **kwargs)
            kws = {}

            # 设置默认的列表参数
            for i, v in enumerate(
                argnames[len(argnames) - len(defaults or ()):]
            ):
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
                '__unspecified_args__': args[narg:],
                '__unspecified_kwargs__': kwargs
            })
            req = request_class(**kws)
            req.end_request = _worker

            return req

        # 根据是否协程函数进行处理
        if iscoroutinefunction(func):
            async def inner(*args, **kwargs):
                return await func(*args, **kwargs)
        else:
            def inner(*args, **kwargs):
                return func(*args, **kwargs)

        def __init__(
            self,
            __unspecified_args__: Union[List, Tuple] = None,
            __unspecified_kwargs__: Dict = None,
            **kwargs
        ) -> None:
            self.__unspecified_args__ = __unspecified_args__ or ()
            self.__unspecified_args__ = __unspecified_kwargs__ or {}
            # list(map(lambda kv: self.__setattr__(kv[0], kv[1]), kwargs.items()))
            _ = {self.__setattr__(k, v) for k, v in kwargs.items()}

        def __repr__(self) -> str:
            return f'<{__name__} sign={self.SIGN}>'

        __name__ = f'{request_name.title()}Requester'

        cls_namespace = {
            'NAME': request_name,
            'WEIGHT': weight,
            '__init__': __init__,
            '__repr__': __repr__,
            '__doc__': func.__doc__,
            '__infomodel__': infomodel,
            '__inherit__': inherit,
            # '__payloads__': not no_payload,
            '__module__': func.__module__,

            '__constructor__': wrapped,
            '__decorated__': func,
        }

        if root:
            bases = (RootRequester,)
        else:
            bases = (Requester,)

        request_class = type(__name__, bases, cls_namespace)

        # wrapped func update
        update_attr = {
            'NAME': request_name,
            'SIGN': request_class().SIGN
        }
        for k, v in update_attr.items():
            setattr(wrapped, k, v)

        return wrapped
    return wrapper


class StopMaker(object):
    def __init__(self) -> None:
        self.stopper_lst = []
        # 使用信号量实现锁
        self.counter = threading.Semaphore(0)

    def run(self) -> None:
        with self.counter:
            for stopper in self.stopper_lst:
                try:
                    print(f'开始：{repr(stopper)}')
                    stopper()
                    print(f'完成：{repr(stopper)}')
                except Exception:
                    print_exc()

    def add_stopper(
        self,
        stopper: Callable[[], Any],
    ) -> None:
        stop_maker = stopper
        if iscoroutinefunction(stopper):
            def stop_maker():
                return executor.submit(
                    get_worker('async_stopper'),
                    args=(stopper,),
                    force_sync=True
                ).result()

        assert callable(stopper)
        self.stopper_lst.append(stop_maker)
        # 添加暂停处理器后允许使用暂停操作，否则阻塞至任务结束
        self.counter.release()

    def destroy(self) -> None:
        with self.counter._cond:
            # 无限释放信号量，释放所有锁
            self.counter._value = float('inf')
            self.counter._cond.notify_all()


class RootRequester(Requester):
    NAME = 'root'


@contextmanager
def apply_requester_context(
    request: Requester
):
    """  """
    var_value = {
        progress_mapping_context: request.progress,
        request_mapping_context: request,
        config_context: dict(get_conf('payload').get(request.NAME, {})),
        self_request: request,
    }
    with ExitStack() as ctx_stack:
        contexts = [
            ctx_stack.enter_context(var.apply(value))
            for var, value in var_value.items()
        ]
        yield


def gen_linear_flow(
    payload: FlowPayload,
    rule
) -> Tuple[List[FlowPayload], List[FlowPayload]]:
    """ 生成payload的线性执行流程
    Args:
        payload:
        rule:
    """
    def make_payload(o):
        """ payload根据规则rule处理。"""
        if not isinstance(o, FlowPayload):
            raise TypeError(f'非定义语法: {type(o)}')
        return o.__make__(rule)

    def lookup_payload(o):
        """ 建立工作流串并行链。"""
        # payload
        o = make_payload(o)

        # root请求器优先，如果存在就抛弃其他请求
        if isinstance(o, RootRequester):
            srp.append(o)
            return None

        # 为了兼容Sequence方法，所有o都以列表的形式迭代处理。
        if not isinstance(o, (list, tuple)):
            o = [o]

        subpayloads = []
        for i in o:
            for req in i.payloads():
                # 处理payloads里的请求
                pls = lookup_payload(req)

                # 如果返回的是None是因为该请求属于root请求，
                # 这将屏蔽所有的请求
                if pls is None:
                    return None
                subpayloads.extend(pls)

        # 请求的payload + 原请求对象，
        # 完成先处理payloads再到处理请求
        if subpayloads:
            o = [i for i in o if i]
            return [subpayloads] + o

        return o

    srp = []
    flow = lookup_payload(payload)
    return flow, srp

