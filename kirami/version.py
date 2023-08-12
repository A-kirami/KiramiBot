"""本模块用于获取元数据及版本信息"""

from importlib.metadata import metadata

from pydantic import BaseModel


class Metadata(BaseModel):
    name: str
    version: str
    summary: str

    class Config:
        extra = "allow"


__metadata__ = Metadata(**metadata("kiramibot").json)  # type: ignore

__version__ = __metadata__.version
