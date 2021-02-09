from typing import Union, Tuple, List, Sequence

from .base import BasePayload


class FlowPayload(BasePayload):
    """ """
    def payloads(self) -> Union[Tuple, List]:
        return findall_subpayload([self.__args__, self.__kwargs__])

    def __make__(self, *args, **kwargs):
        raise NotImplementedError


def findall_subpayload(
    arg: Sequence
) -> List[Union[List[FlowPayload], List[List], FlowPayload]]:
    """ 迭代搜索请求的payload。"""
    def search_array(o) -> None:
        """ 搜索 list, tuple, set迭代对象。"""
        for v in o:
            if isinstance(v, FlowPayload):
                payloads.append(v)
            else:
                goto_search(v)

    def search_dict(o) -> None:
        """ 搜索字典。"""
        for k, v in o.items():
            if isinstance(k, FlowPayload):
                payloads.append(k)
            else:
                goto_search(k)

            if isinstance(v, FlowPayload):
                payloads.append(v)
            else:
                goto_search(v)

    def goto_search(o) -> None:
        """ 迭代搜索。注意在交叉嵌套的情况下会出现无限迭代的问题。
        但事实上payload通常不存在交叉嵌套的情况。
        """
        if isinstance(o, (list, tuple, set)):
            search_array(o)
        elif isinstance(o, dict):
            search_dict(o)
        elif isinstance(o, FlowPayload):
            payloads.append(o)

    payloads = []
    goto_search(arg)
    return payloads


