from pydantic import Field
from pydantic.main import BaseModel
from typing import List, Dict, Union, Any, Tuple, Optional


class GetSupportedParams(BaseModel):
    url: str = Field(title='URL链接')


class GetVersionsParams(BaseModel):
    name: str = Field(title='查询的脚本名称')


class RegisterParams(BaseModel):
    path: str = Field(title='脚本路径')
    sha256: str = Field(title='脚本文件SHA256')


class CallScriptParams(BaseModel):
    url: str = Field(title='URL链接')
    rule: Union[str, int] = Field(title='脚本处理规则')
    extra: Dict = Field(title='额外字段参数', default={})


class ExecuteScriptParams(BaseModel):
    url: str = Field(title='URL链接')
    rule: Union[int, str] = Field(title='参考处理规则', default=None)
    name: str = Field(title='脚本名称，带版本号后可忽略version参数', default=None)
    version: str = Field(title='脚本版本号，可在name后带版本号.', default=None)
    options: Dict = Field(title='额外处理选项', default={})


class RemoteApplyParams(BaseModel):
    funcid: str = Field(title='函数ID')
    args: tuple = Field(title='列表函数')
    kwargs: Dict = Field(title='字典参数')


class NewTasksListParams(BaseModel):
    """ 创建任务参数。"""
    urls: List[str] = Field(title='URLs列表')
    options: Dict = Field(title='配置选项', default={})


class StopTaskParams(BaseModel):
    """ 暂停任务参数。"""
    keys: List[str] = Field(title='任务KEY列表')


class RestartTaskParams(BaseModel):
    """ 重试任务参数。"""
    keys: List[str] = Field(title='任务KEY列表')


class ListTaskParams(BaseModel):
    """ 任务状态列表参数。"""
    offset: int = Field(title='任务列表偏移（起始位置）', default=0)
    limit: int = Field(title='返回条数', default=20)
    active: Optional[str] = Field(title='选择的任务KEY', default=None)


class QueryConfigureParams(BaseModel):
    pass


class ConfItemModifyParams(BaseModel):
    link: List[str] = Field(title='修改索引链接')
    newVal: Any = Field(title='修改后的值')
    oldVal: Any = Field(title='修改前的值')


class ConfModifyParams(BaseModel):
    items: List[ConfItemModifyParams] = Field(title='被修改的项列表')


class SystemStateParams(BaseModel):
    """ 获取服务状态。 """


class ConfReloadParams(BaseModel):
    """ 服务配置重载。"""


