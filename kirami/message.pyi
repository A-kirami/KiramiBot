from io import BytesIO
from pathlib import Path
from typing import Protocol

from flowery import Imager
from flowery.typing import PILImage
from nonebot.adapters import MessageTemplate as MessageTemplate
from nonebot.adapters.onebot.v11 import Message as BaseMessage
from nonebot.adapters.onebot.v11 import MessageSegment as BaseMessageSegment
from typing_extensions import Self

# ruff: noqa: PYI021

class MessageResource(Protocol):
    def message(self, *args, **kwargs) -> MessageSegment: ...

class MessageSegment(BaseMessageSegment):
    @classmethod
    def text(cls, text: str) -> Self: ...
    @classmethod
    def face(cls, id_: int) -> Self: ...
    @classmethod
    def at(cls, user_id: int | str) -> Self: ...
    @classmethod
    def reply(cls, id_: int) -> Self: ...
    @classmethod
    def image(
        cls,
        file: str | bytes | BytesIO | Path | MessageResource | PILImage | Imager,
        type_: str | None = None,
        cache: bool = True,
        proxy: bool = True,
        timeout: int | None = None,
    ) -> Self: ...
    @classmethod
    def record(
        cls,
        file: str | bytes | BytesIO | Path | MessageResource,
        magic: bool | None = None,
        cache: bool = True,
        proxy: bool = True,
        timeout: int | None = None,
    ) -> Self: ...
    @classmethod
    def video(
        cls,
        file: str | bytes | BytesIO | Path | MessageResource,
        cache: bool = True,
        proxy: bool = True,
        timeout: int | None = None,
    ) -> Self: ...
    @classmethod
    def poke(cls, id_: int | str) -> Self: ...
    @classmethod
    def refer(cls, id_: int) -> Self: ...
    @classmethod
    def node(
        cls, user_id: int | str, nickname: str, content: str | Message
    ) -> Self: ...

class Message(BaseMessage):
    @classmethod
    def text(cls, text: str) -> Self:
        """纯文本消息。

        ### 参数
            text: 文本内容
        """
        ...
    @classmethod
    def face(cls, id_: int) -> Self:
        """表情消息。

        ### 参数
            id_: 表情 ID
        """
        ...
    @classmethod
    def at(cls, user_id: int | str) -> Self:
        """@ 某人消息。

        ### 参数
            user_id: 要 @ 的用户 ID
        """
        ...
    @classmethod
    def reply(cls, id_: int) -> Self:
        """回复消息。

        ### 参数
            id_: 回复的消息 ID
        """
        ...
    @classmethod
    def image(
        cls,
        file: str | bytes | BytesIO | Path | MessageResource | PILImage | Imager,
        type_: str | None = None,
        cache: bool = True,
        proxy: bool = True,
        timeout: int | None = None,
    ) -> Self:
        """图片消息。

        ### 参数
            file: 图像文件，可传入本地路径、网络链接或者其他支持的对象

            type_: 图片类型，无此参数表示普通图片。默认为 None

            cache: 是否使用缓存。默认为 True

            proxy: 是否使用代理。默认为 True

            timeout: 超时时间。默认为 None

        ### 异常
            ReadFileError: 读取文件错误，不是一个有效的文件
        """
        ...
    @classmethod
    def anonymous(cls, ignore_failure: bool | None = None) -> Self:
        """匿名消息。

        ### 参数
            ignore_failure: 无法匿名时是否继续发送。默认为 None
        """
        ...
    @classmethod
    def refer(cls, id_: int) -> Self:
        """合并转发引用消息。

        ### 参数
            id_: 引用的消息 ID
        """
        ...
    @classmethod
    def node(cls, user_id: int | str, nickname: str, content: str | Self) -> Self:
        """合并转发节点消息。

        ### 参数
            user_id: 用户 ID

            nickname: 用户昵称

            content: 节点内容
        """
        ...
