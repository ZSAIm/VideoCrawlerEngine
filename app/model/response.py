from typing import List, Dict, Any

from pydantic import Field

from app.model.base import APIRespModel
from app.model.data import (
    ScriptModel,
    TaskModel,
    ApplyModel,
    ListTaskModel,
    StopTaskModel,
    AppConfModel,
    ModifyRespModel,
    SystemStateModel,
    AppRespModel
)


class GetSupportedResp(APIRespModel):
    data: List[ScriptModel] = Field(title='支持的脚本')


class GetVersionsResp(APIRespModel):
    data: List[ScriptModel] = Field(title='脚本')


class RegisterResp(APIRespModel):
    pass


class RemoteApplyResp(APIRespModel):
    data: ApplyModel = Field(title='调用响应')


class NotImplementResp(APIRespModel):
    data: Dict = Field(title='接口未实现。')


class ExecuteScriptResp(APIRespModel):
    data: Dict = Field(title='脚本执行响应。')


class NewTasksResp(APIRespModel):
    data: List[TaskModel] = Field(title='新建任务响应。')


class StopTasksResp(APIRespModel):
    data: List[StopTaskModel] = Field(title='暂停任务响应')


class ListTasksResp(APIRespModel):
    data: List[ListTaskModel] = Field(title='任务列表。')


class ConfQueryResp(APIRespModel):
    data: List[AppConfModel] = Field(title='应用配置选项')


class ConfModifyResp(APIRespModel):
    data: List[ModifyRespModel] = Field(title='配置修改响应结果')


class SystemStateResp(APIRespModel):
    data: SystemStateModel = Field(title='获取应用系统状态。', default=[])


class ConfReloadResp(APIRespModel):
    data: Any = Field(title='系统配置重载')


class AppResponse(APIRespModel):
    data: List[AppRespModel] = Field(title='系统状态响应')