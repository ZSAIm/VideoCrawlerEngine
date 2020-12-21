
from typing import List, Dict, Tuple, AnyStr, Any
from pydantic import Field
from pydantic.main import BaseModel


class ScriptModel(BaseModel):
    name: str = Field(title='名称')
    version: str = Field(title='版本号')
    supported_domains: List[str] = Field(title='支持的域名')
    author: str = Field(title='作者')
    created_date: str = Field(title='创建日期')
    license: str = Field(title='许可证')
    qn_ranking: List = Field(title='质量排序')


class TaskModel(BaseModel):
    sign: str = Field(title='任务签名')
    title: str = Field(title='任务标题')
    url: str = Field(title='')


class ListTaskModel(BaseModel):
    sign: str = Field(title='任务签名sign')
    url: str = Field(title='任务url')
    title: str = Field(title='任务标题')
    options: Dict = Field(title='任务选项设置')
    running_nodes: List[str] = Field(title='运行中的节点')
    layers: Dict = Field(title='执行主层信息')
    running_layers: List[str] = Field(title='运行中的执行主层')
    allnodes: Dict = Field(title='所有节点')


class ApplyModel(BaseModel):
    key: str = Field(title='脚本KEY')
    funcid: str = Field(title='函数ID')
    context: Any = Field(title='上下文消息')
    ret: Any = Field(title='函数返回值', default=None)
    exc: str = Field(title='异常回溯消息。', default=None)


