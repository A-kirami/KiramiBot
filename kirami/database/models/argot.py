from datetime import datetime, timedelta
from typing import Any

from mango import Document, Field

from kirami.event import MessageEvent


class Argot(Document):
    msg_id: int = Field(primary_key=True)
    """消息 ID"""
    content: dict[str, Any]
    """内容"""
    time: datetime = Field(
        default_factory=lambda: datetime.now().astimezone(),
        expire=int(timedelta(days=1).total_seconds()),
        init=False,
    )
    """创建时间"""

    @classmethod
    async def mark(cls, event: MessageEvent, content: dict[str, Any]) -> None:
        """标记一条消息为暗语"""
        mid = event.message_id
        await Argot(msg_id=mid, content=content).save()
