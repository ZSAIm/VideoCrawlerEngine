

from pydantic import BaseModel, Field
from typing import List, Union, TypeVar, Any
from typing import Generic


class APIRespModel(BaseModel):
    code: int = Field(title='响应代码', default=0)
    msg: str = Field(title='响应代码说明消息', default='ok')
    data: Any = Field(title='响应数据', default=None)




