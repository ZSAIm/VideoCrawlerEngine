from typing import (
    List,
    Any,
    Union,
    Tuple,
)
from .flow import FlowPayload


class Optional(FlowPayload):
    NAME = 'optional'

    def __init__(self, options) -> None:
        """
        :param
            list:       可选择的项列表
            sort_key:   项目排序的key
        """
        self.__options_lst = options
        self.__active_option = None

    def __getattr__(self, item):
        return self.__active_option.__getattribute__(item)

    def __getitem__(self, item):
        return self.__active_option.__getitem__(item)

    def __repr__(self):
        return repr(self.__active_option)

    def __make__(self, rule, *args, **kwargs):
        if not self.__active_option:
            if rule == 'high':
                rule = 100
            elif rule == 'low':
                rule = 1
            elif rule == 'middle':
                rule = 50

            if isinstance(rule, int) and 1 <= rule <= 100:
                selected = self.__options_lst[
                    max(0, int((100 - rule) * len(self.__options_lst) / 100) - 1)]
            else:
                selected = self.__options_lst[0]
            self.__active_option = selected
            # return selected
            # self.select(rule)
        return self.__active_option.__make__()


class Option(FlowPayload):
    NAME = 'option'

    def __init__(self, content, descriptions=None) -> None:
        self.__payload = content
        if descriptions is None:
            descriptions = {}
        self.__desc = descriptions

    def __repr__(self) -> str:
        return str(self.__payload)

    def __getattr__(self, item):
        return self.__payload.__getattribute__(item)

    def __getitem__(self, item):
        return self.__payload.__getitem__(item)

    def __make__(self, *args, **kwargs):
        return self.__payload.__make__()


class Sequence(FlowPayload):
    """ """
    NAME = 'sequence'

    def __init__(self, *seqs):
        self.sequences = seqs

    def __iter__(self):
        return iter(self.sequences)

    def __len__(self):
        return len(self.sequences)

    def __make__(self, *args, **kwargs):
        return self.sequences


class Concurrent(FlowPayload):
    NAME = 'concurrent'

    def __init__(self, *tasks):
        self.tasks = tasks

    def __iter__(self):
        return iter(self.tasks)

    def __make__(self, *args, **kwargs):
        return self

    def payloads(self) -> Union[Tuple, List]:
        return self.tasks

    def __bool__(self):
        """ 当前payload不作为工作流的节点。"""
        return False


def optional(
    options: List[Any]
) -> Optional:
    return Optional(options)


def option(
    content,
    descriptions=None
) -> Option:
    return Option(content, descriptions)


def sequence(
    *seqs
) -> Sequence:
    return Sequence(*seqs)

