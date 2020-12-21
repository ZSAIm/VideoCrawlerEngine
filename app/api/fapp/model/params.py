
from pydantic import BaseModel, Field
from typing import Union, List, Dict


class TaskCreateParams(BaseModel):
    url: str = Field(title='任务URL')
    rule: Union[str, int] = Field(title='任务处理规则')

