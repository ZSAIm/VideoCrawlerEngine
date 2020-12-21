from contextlib import contextmanager
from contextvars import ContextVar, copy_context as _copy_context, Token
from typing import Union, Any, TypeVar


class Undefined(object):
    pass


undefined = Undefined()

__global_context__ = {}


class GlobalContext:
    def __init__(self, name, namespace='', default=undefined):
        self.value = None
        self.name = '.'.join(([namespace] if namespace else []) + [name])
        self.entered = False
        self.default = default

    def apply(self, value):
        self.entered = True
        self.value = value
        __global_context__[self.name] = self.value
        return self

    def reset(self):
        del __global_context__[self.name]
        self.value = None
        self.entered = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.reset()

    def get(self, default=undefined):
        # assert self.entered
        if not self.entered:
            default = default if isinstance(default, Undefined) else self.default
            if isinstance(default, Undefined):
                raise LookupError('')
            return default
        return self.value


def context_var(name, *, default=None, has_default):
    if has_default:
        return ContextVar(name, default=default)
    else:
        return ContextVar(name)


class ContextManager:
    def __init__(self, name, namespace='', default: Union[Any, Undefined] = undefined):
        self.context = context_var(
            '.'.join(([namespace] if namespace else []) + [name]),
            default=[None, default], has_default=not isinstance(default, Undefined)
        )

    @property
    def name(self):
        return self.context.name

    def apply(self, value):
        values = [None, value]
        token = self.context.set(values)
        values[0] = token
        return self

    def reset(self):
        token, value = self.context.get()
        self.context.reset(token)

    def get(self, default: Union[Undefined, Any] = undefined):
        try:
            return self.context.get()[-1]
        except LookupError:
            if isinstance(default, Undefined):
                raise
            return default

    __call__ = get

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.reset()

    def __getitem__(self, item):
        token, value = self.context.get()
        return value[item]

    __getattr__ = __getitem__


def lookup_chain_object(obj, chain_name):
    """ 查找链式对象。 """
    o = obj
    for name in chain_name.split('.'):
        o = getattr(o, name)
    return o


class AttributeContext:
    def __init__(
        self,
        name: str,
        namespace: str = '',
        default: Union[Any, Undefined] = undefined
    ):
        *basename, objname = name.rsplit('.', 1)
        self.getter = ContextManager(
            '.'.join(([namespace] if namespace else []) + basename + [f'get_{objname}']),
            default=default
        )
        self.setter = ContextManager(
            '.'.join(([namespace] if namespace else []) + basename + [f'set_{objname}']),
            default=default
        )
        self.name = name

    def apply(self, obj):
        def _getter():
            return lookup_chain_object(obj, self.name)

        def _setter(value):
            o = obj
            *basename, objname = self.name.split('.')
            for name in basename:
                o = getattr(o, name)
            setattr(o, objname, value)

        try:
            values = [None, obj]
            token = self.getter.apply(_getter)
            values[0] = token

            values = [None, obj]
            token = self.setter.apply(_setter)
            values[0] = token
            return self
        except Exception:
            self.reset()
            raise

    def reset(self):
        self.getter.reset()
        self.setter.reset()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.reset()


class ObjectMappingContext:
    def __init__(
        self,
        attrs: str = '',
        meths: str = '',
        namespace: str = '',
        default: Union[Any, Undefined] = undefined
    ):
        if isinstance(attrs, str):
            attrs = [name.strip() for name in attrs.split(' ') if name.strip()]

        if isinstance(meths, str):
            meths = [name.strip() for name in meths.split(' ') if name.strip()]

        self.attrs = {
            name: AttributeContext(
                '.'.join([namespace, name]) if namespace else name,
                default=default
            ) for name in attrs
        }
        self.meths = {
            name: ContextManager(
                '.'.join([namespace, name]) if namespace else name,
                default=default
            ) for name in meths
        }

    def apply(self, obj):
        try:
            for k, v in self.attrs.items():
                v.apply(obj)

            for k, v in self.meths.items():
                v.apply(lookup_chain_object(obj, k))
            return self
        except Exception:
            self.reset()
            raise

    def reset(self):
        for k, v in self.attrs.items():
            v.reset()

        for k, v in self.meths.items():
            v.reset()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.reset()

    def __getitem__(self, item):
        if item in self.attrs:
            return self.attrs[item]
        elif item in self.meths:
            return self.meths[item]
        raise AttributeError

    __getattr__ = __getitem__


class ContextNamespace:
    """ 上下文命名空间。 """
    def __init__(self, namespace: str):
        self.namespace = namespace
        self.__context = {}

    def contextmanager(self, name, default: Union[Undefined, Any] = undefined):
        """ 创建一个上下文管理器。"""
        context = ContextManager(name, self.namespace, default)
        self.__context[name] = context
        return context

    def attributecontext(self, name, default: Union[Undefined, Any] = undefined):
        """ 创建一个属性上下文管理器。"""
        context = AttributeContext(name, self.namespace, default)
        self.__context[name] = context
        return context

    def objectmappingcontext(self, attr: str = '', meths: str = '', default: Union[Undefined, Any] = undefined):
        """ 创建一个对象方法映射上下文管理器。"""
        context = ObjectMappingContext(attr, meths, self.namespace, default)
        for name in list(context.attrs.keys()) + list(context.meths.keys()):
            self.__context[name] = context
        return context

    def globalcontext(self, name):
        context = GlobalContext(name, self.namespace)
        self.__context[name] = context
        return context

    def __getitem__(self, item):
        return self.__context[item]

    __getattr__ = __getitem__


def copy_context_to_dict(
    inherit_scope: bool = False
):
    """ """
    contexts = {}
    if inherit_scope:
        contexts.update(__scope__.get({}))
    # 全局上下文，常量、静态上下文
    contexts.update(dict(__global_context__))
    # 动态上下文
    contexts.update({
        k.name: v[1]
        for k, v in _copy_context().items()
        if isinstance(v, list) and len(v) == 2 and isinstance(v[0], Token)
    })

    return contexts


__scope__ = ContextManager('__scope__')


@contextmanager
def run_context_from_dict(context):
    """ 运行"""
    global __scope__
    with __scope__.apply(context):
        yield __scope__


@contextmanager
def run_context_from_scope():
    context = copy_context_to_dict()
    # with run(context) as _:
    #     yield _
    with run_context_from_dict(context) as scope:
        yield scope


class LookupSpecialMethods(object):
    def __lookup__(self, item):
        raise NotImplementedError

    def __len__(self):
        return self.__lookup__('__len__')()

    def __call__(self, *args, **kwargs):
        return self.__lookup__('__call__')(*args, **kwargs)

    def __enter__(self):
        return self.__lookup__('__enter__')()

    def __exit__(self, exc_type, exc_val, exc_tb):
        result = self.__lookup__('__exit__')(exc_type, exc_val, exc_tb)
        if any([exc_type, exc_val, exc_tb]):
            raise
        return result

    async def __aenter__(self):
        return self.__lookup__('__aenter__')()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return self.__lookup__('__aexit__')(exc_type, exc_val, exc_tb)

    def __getitem__(self, item):
        return self.__lookup__('__getitem__')(item)

    def __setitem__(self, key, value):
        return self.__lookup__('__setitem__')(key, value)

    def __iter__(self):
        return self.__lookup__('__iter__')()


class _InvokeChain(LookupSpecialMethods):
    def __init__(self, prename, name):
        self.__prename__ = prename
        self.__name__ = name

    def __lookup__(self, item):
        prename = [self.__prename__] if self.__prename__ else []
        obj_chain = f'{".".join(prename + [self.__name__, item])}'
        try:
            obj = _lookup_scope(obj_chain)
        except (KeyError, LookupError):
            raise LookupError(prename, obj_chain)
        return obj

    def __getattr__(self, item):
        try:
            return self.__lookup__(item)
        except LookupError as e:
            prename, *_ = e.args
            return _InvokeChain(f'{".".join(prename + [self.__name__])}', item)

    def __repr__(self):
        return f'<DebugChain {self.__str__()}>'

    def __str__(self):
        prename = [self.__prename__] if self.__prename__ else []
        return ".".join(prename + [self.__name__])


def _lookup_scope(chain):
    return __scope__[chain]


@contextmanager
def run_in_debug_mode(**options):
    from helper.worker import init_workers
    from conf import load_config
    from task import TaskStack

    global __debug_mode__
    load_config()
    init_workers()
    __debug_mode__ = True

    task = TaskStack(None)
    yield task


T = TypeVar('T')


def get_ctx(
    context: Union[_InvokeChain, T],
    default: Union[Undefined, Any] = undefined
) -> T:
    if isinstance(context, _InvokeChain):
        if not isinstance(default, Undefined):
            return default
        raise LookupError(f'未应用上下文变量：{context}')
    return context
