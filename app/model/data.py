
from typing import List, Dict, Tuple, AnyStr, Any, Optional
from pydantic import Field
from pydantic.main import BaseModel


class ScriptModel(BaseModel):
    name: str = Field(title='名称')
    version: str = Field(title='版本号')
    supported_domains: List[str] = Field(title='支持的域名')
    author: str = Field(title='作者')
    createdDate: str = Field(title='创建日期')
    license: str = Field(title='许可证')
    qn: List = Field(title='质量排序')


class TaskModel(BaseModel):
    sign: str = Field(title='任务签名')
    title: str = Field(title='任务标题')
    url: str = Field(title='任务链接')
    errcode: int = Field(title='错误代码')
    errmsg: str = Field(title='错误消息', default=None)


class ListTaskModel(BaseModel):
    sign: str = Field(title='任务签名sign')
    url: str = Field(title='任务url')
    title: str = Field(title='任务标题')
    name: str = Field(title='头像名称')
    percent: Optional[float] = Field(title='进度百分比')
    timeleft: Optional[float] = Field(title='估计剩余时间')
    status: str = Field(title='任务状态')
    options: Dict = Field(title='任务选项设置')
    allRoots: Dict = Field(title='所有根节点')
    runningRoots: List[str] = Field(title='运行中的根节点')
    allLayers: Dict = Field(title='执行主层信息')
    runningLayers: List[str] = Field(title='运行中的执行主层')
    runningNodes: List[str] = Field(title='运行中的节点')
    allNodes: Dict = Field(title='所有节点')
    rawFlows: List = Field(title='原始节点流')


class StopTaskModel(BaseModel):
    errcode: int = Field(title='错误代码')
    errmsg: str = Field(title='错误消息', default=None)


class ApplyModel(BaseModel):
    key: str = Field(title='脚本KEY')
    funcid: str = Field(title='函数ID')
    context: Any = Field(title='上下文消息')
    ret: Any = Field(title='函数返回值', default=None)
    exc: str = Field(title='异常回溯消息。', default=None)


