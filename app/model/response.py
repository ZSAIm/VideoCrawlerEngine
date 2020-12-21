from typing import List, Dict

from pydantic import Field

from app.model.base import APIRespModel
from app.model.data import (
    ScriptModel,
    TaskModel,
    ApplyModel,
    ListTaskModel,
)


class GetSupportedResp(APIRespModel):
    data: List[ScriptModel] = Field(title='支持的脚本')


class GetVersionsResp(APIRespModel):
    data: List[ScriptModel] = Field(title='脚本')


class RegisterResp(APIRespModel):
    pass


class ExecuteScriptResp(APIRespModel):
    data: Dict = Field(title='脚本执行响应。')


class NewTaskResp(APIRespModel):
    data: List[TaskModel] = Field(title='新建任务响应。')


class RemoteApplyResp(APIRespModel):
    data: ApplyModel = Field(title='调用响应')


class ListTaskResp(APIRespModel):
    data: List[ListTaskModel] = Field(title='任务列表。')


class NotImplementResp(APIRespModel):
    data: Dict = Field(title='接口未实现。')