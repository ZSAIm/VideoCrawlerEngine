

from contextvars import ContextVar, copy_context as _copy_context, Token

__global_context__ = {}


class GlobalContext:
    def __init__(self, name, namespace=''):
        """
        Initialize an attribute.

        Args:
            self: (todo): write your description
            name: (str): write your description
            namespace: (str): write your description
        """
        self.value = None
        self.name = '.'.join(([namespace] if namespace else []) + [name])
        self.entered = False

    def enter(self, value):
        """
        Returns a global variable.

        Args:
            self: (todo): write your description
            value: (todo): write your description
        """
        self.entered = True
        self.value = value
        __global_context__[self.name] = self.value
        return self

    def leave(self):
        """
        Clears the context.

        Args:
            self: (todo): write your description
        """
        del __global_context__[self.name]
        self.value = None
        self.entered = False

    def __enter__(self):
        """
        Decor function.

        Args:
            self: (todo): write your description
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit the given exception.

        Args:
            self: (todo): write your description
            exc_type: (todo): write your description
            exc_val: (todo): write your description
            exc_tb: (todo): write your description
        """
        self.leave()

    def get(self):
        """
        Returns the value of the current node.

        Args:
            self: (todo): write your description
        """
        assert self.entered
        return self.value


class ContextManager:
    def __init__(self, name, namespace='', default=None):
        """
        Initialize a new namespace.

        Args:
            self: (todo): write your description
            name: (str): write your description
            namespace: (str): write your description
            default: (str): write your description
        """
        self.context = ContextVar('.'.join(([namespace] if namespace else []) + [name]), default=[None, default])
        self.default = default

    @property
    def name(self):
        """
        Return the name of the context.

        Args:
            self: (todo): write your description
        """
        return self.context.name

    def enter(self, value):
        """
        Creates a new context.

        Args:
            self: (todo): write your description
            value: (todo): write your description
        """
        values = [None, value]
        token = self.context.set(values)
        values[0] = token
        return self

    def leave(self):
        """
        Reset the token.

        Args:
            self: (todo): write your description
        """
        token, value = self.context.get()
        self.context.reset(token)

    def get(self):
        """
        Get the current result.

        Args:
            self: (todo): write your description
        """
        return self.context.get()[-1]

    __call__ = get

    def __enter__(self):
        """
        Decor function.

        Args:
            self: (todo): write your description
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit the given exception.

        Args:
            self: (todo): write your description
            exc_type: (todo): write your description
            exc_val: (todo): write your description
            exc_tb: (todo): write your description
        """
        self.leave()

    def __getitem__(self, item):
        """
        Return the value of a given item.

        Args:
            self: (todo): write your description
            item: (str): write your description
        """
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
    def __init__(self, name, namespace='', default=None):
        """
        Initialize a namespace.

        Args:
            self: (todo): write your description
            name: (str): write your description
            namespace: (str): write your description
            default: (str): write your description
        """
        *basename, objname = name.rsplit('.', 1)
        self.getter = ContextManager('.'.join(([namespace] if namespace else []) + basename + [f'get_{objname}']),
                                     default=[None, default])
        self.setter = ContextManager('.'.join(([namespace] if namespace else []) + basename + [f'set_{objname}']),
                                     default=[None, default])
        self.name = name

    def enter(self, obj):
        """
        Enter an object.

        Args:
            self: (todo): write your description
            obj: (todo): write your description
        """
        def _getter():
            """
            Return the object from the given object.

            Args:
            """
            return lookup_chain_object(obj, self.name)

        def _setter(value):
            """
            Set the given value of an attribute.

            Args:
                value: (todo): write your description
            """
            o = obj
            *basename, objname = self.name.split('.')
            for name in basename:
                o = getattr(o, name)
            setattr(o, objname, value)

        values = [None, obj]
        token = self.getter.enter(_getter)
        values[0] = token

        values = [None, obj]
        token = self.setter.enter(_setter)
        values[0] = token
        return self

    def leave(self):
        """
        Sets the inputed pipe.

        Args:
            self: (todo): write your description
        """
        self.getter.leave()
        self.setter.leave()

    def __enter__(self):
        """
        Decor function.

        Args:
            self: (todo): write your description
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit the given exception.

        Args:
            self: (todo): write your description
            exc_type: (todo): write your description
            exc_val: (todo): write your description
            exc_tb: (todo): write your description
        """
        self.leave()


class ObjectMappingContext:
    def __init__(self, attrs='', meths='', namespace='', default=None):
        """
        Initialize the attributes.

        Args:
            self: (todo): write your description
            attrs: (str): write your description
            meths: (str): write your description
            namespace: (str): write your description
            default: (str): write your description
        """
        if isinstance(attrs, str):
            attrs = [name for name in attrs.split(' ') if name]

        if isinstance(meths, str):
            meths = [name for name in meths.split(' ') if name]

        self.attrs = {name: AttributeContext('.'.join([namespace, name])
                                             if namespace else name, default=[None, default]) for name in attrs}
        self.meths = {name: ContextManager('.'.join([namespace, name])
                                           if namespace else name, default=[None, default]) for name in meths}

    def enter(self, obj):
        """
        Enter an object on - link.

        Args:
            self: (todo): write your description
            obj: (todo): write your description
        """
        for k, v in self.attrs.items():
            v.enter(obj)

        for k, v in self.meths.items():
            v.enter(lookup_chain_object(obj, k))
        return self

    def leave(self):
        """
        Leave all attributes from the context.

        Args:
            self: (todo): write your description
        """
        for k, v in self.attrs.items():
            v.leave()

        for k, v in self.meths.items():
            v.leave()

    def __enter__(self):
        """
        Decor function.

        Args:
            self: (todo): write your description
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit the given exception.

        Args:
            self: (todo): write your description
            exc_type: (todo): write your description
            exc_val: (todo): write your description
            exc_tb: (todo): write your description
        """
        self.leave()


class ContextNamespace:
    """ 上下文命名空间。 """
    def __init__(self, namespace):
        """
        Initialize a namespace.

        Args:
            self: (todo): write your description
            namespace: (str): write your description
        """
        self.namespace = namespace
        self.__context = {}

    def contextmanager(self, name):
        """ 创建一个上下文管理器。"""
        context = ContextManager(name, self.namespace)
        self.__context[name] = context
        return context

    def attributecontext(self, name):
        """ 创建一个属性上下文管理器。"""
        context = AttributeContext(name, self.namespace)
        self.__context[name] = context
        return context

    def objectmappingcontext(self, name):
        """ 创建一个对象方法映射上下文管理器。"""
        context = ObjectMappingContext(name, self.namespace)
        self.__context[name] = context
        return context

    def globalcontext(self, name):
        """
        Returns a global context. context.

        Args:
            self: (todo): write your description
            name: (str): write your description
        """
        context = GlobalContext(name, self.namespace)
        self.__context[name] = context
        return context

    def __getitem__(self, item):
        """
        Return the item from the given item.

        Args:
            self: (todo): write your description
            item: (str): write your description
        """
        return self.__context[item]

    __getattr__ = __getitem__


def context_dict():
    """ """
    # 全局上下文，常量、静态上下文
    contexts = dict(__global_context__)
    # 动态上下文
    contexts.update({
        k.name: v[1]
        for k, v in _copy_context().items()
        if isinstance(v, list) and len(v) == 2 and isinstance(v[0], Token)
    })
    return contexts

