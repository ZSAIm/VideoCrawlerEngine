
from typing import List, Dict, Tuple, AnyStr, Any, Optional, Union
from pydantic import Field
from pydantic.main import BaseModel
from app.model.base import APIRespModel


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
    # allLayers: Dict = Field(title='执行主层信息')
    # runningLayers: List[str] = Field(title='运行中的执行主层')
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


class ConfItemModel(BaseModel):
    title: str = Field(title='配置项标题')
    name: str = Field(title='配置项名称')
    tag: str = Field(title='配置项类型')
    desc: str = Field(title='配置项描述')
    value: Any = Field(title='配置项的值')
    validation: Dict = Field(title='校验配置')
    disabled: bool = Field(title='配置是否可修改')
    extra: Dict = Field(title='额外信息')


class ConfGroupModel(BaseModel):
    title: str = Field(title='配置标题')
    name: str = Field(title='配置名称')
    items: List[ConfItemModel] = Field(title='组配置项列表')


class AppConfModel(BaseModel):
    title: str = Field(title='配置标题')
    name: str = Field(title='配置名称')
    groups: List[ConfGroupModel] = Field(title='组配置列表(SECTION)')


class ModifyRespModel(BaseModel):
    id: Any = Field(title='响应ID')
    errcode: int = Field(title='错误代码')
    errmsg: str = Field(title='错误响应消息')


class AppStateModel(BaseModel):
    id: str = Field(title='应用ID')
    name: str = Field(title='应用名称')
    latency: int = Field(title='延迟')


class WorkerStateModel(BaseModel):
    name: str = Field(title='工作者名称')
    maxConcurrent: Optional[int] = Field(title='最大并发量')
    independent: bool = Field(ttile='独占线程')
    asyncType: bool = Field(title='异步类型')
    count: int = Field(title='')


class SystemStateModel(BaseModel):
    worker: List[WorkerStateModel] = Field(title='工作者状态', default=[])


class AppRespModel(APIRespModel):
    name: str = Field(title='服务名称')
    latency: float = Field(title='网络延迟(毫秒)')
    gateway: str = Field(title='服务网关')
