# 编写一个pydantic模型
from pydantic import BaseModel

class Status(BaseModel):
    status: str
    message: str
