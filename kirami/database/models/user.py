from typing import Any, TypeVar

from mango import Document, Field

T = TypeVar("T")


class User(Document):
    """用户文档"""

    id: int = Field(primary_key=True)
    """用户 ID"""
    data: dict[str, Any] = Field(default_factory=dict, init=False)
    """用户数据"""

    def get_data(self, name: str, default: T = None) -> T:
        return self.data.get(name, default)

    async def set_data(self, name: str, value: Any = None) -> None:
        self.data[name] = value
        await self.save()
