from pydantic import Field
from pydantic.main import BaseModel
from typing import List, Dict, Union, Any, Tuple


class TaskCreateParams(BaseModel):
    pass


class StopTaskParams(BaseModel):
    pass


class TaskCreateParams(BaseModel):
    pass


class CreateTaskParams(BaseModel):
    pass




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


class NewTaskParams(BaseModel):
    url: str = Field(title='URL链接')
    options: Dict[str, Any] = Field(title='配置选项', default={})


class ListTaskParams(BaseModel):
    offset: int = Field(title='任务列表偏移（起始位置）', default=0)
    limit: int = Field(title='返回条数', default=20)