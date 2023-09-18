"""本模块定义了消息构造器，可用于快速创建混合消息"""

import contextlib
from collections.abc import Callable
from io import BytesIO
from pathlib import Path
from typing import ClassVar, Protocol, TypeVar, runtime_checkable

from flowery import Imager
from flowery.typing import PILImage
from nonebot.adapters import MessageTemplate as MessageTemplate
from nonebot.adapters.onebot.v11 import Message as BaseMessage
from nonebot.adapters.onebot.v11 import MessageSegment as BaseMessageSegment
from typing_extensions import Self

from kirami.exception import ReadFileError


@runtime_checkable
class MessageResource(Protocol):
    path: Path

    def message(self, *args, **kwargs) -> "MessageSegment":
        ...


def file_handle(
    file: str | bytes | BytesIO | Path | MessageResource,
) -> Path | bytes | BytesIO | str:
    """处理文件路径"""
    if isinstance(file, str) and "://" not in file:
        with contextlib.suppress(OSError):
            if Path(file).is_file():
                return Path(file)
            raise ReadFileError(f"不是一个有效的文件: {file}")
    if isinstance(file, MessageResource):
        file = file.path
    return file


class MessageSegment(BaseMessageSegment):
    """消息段构造器"""

    @classmethod
    def text(cls, text: str) -> Self:
        """返回一个纯文本消息段。

        ### 参数
            text: 文本内容
        """
        return super().text(text)

    @classmethod
    def face(cls, id_: int) -> Self:
        """返回一个表情消息段。

        ### 参数
            id_: 表情 ID
        """
        return super().face(id_)

    @classmethod
    def at(cls, user_id: int | str) -> Self:
        """返回一个 @ 某人消息段。

        ### 参数
            user_id: 要 @ 的用户 ID
        """
        return super().at(user_id)

    @classmethod
    def reply(cls, id_: int) -> Self:
        """返回一个回复消息段。

        ### 参数
            id_: 回复的消息 ID
        """
        return super().reply(id_)

    @classmethod
    def image(
        cls,
        file: str | bytes | BytesIO | Path | MessageResource | PILImage | Imager,
        *args,
        **kwargs,
    ) -> Self:
        """返回一个图片消息段。

        ### 参数
            file: 图像文件，可传入本地路径、网络链接或者其他支持的对象

            type_: 图片类型，无此参数表示普通图片。默认为 None

            cache: 是否使用缓存。默认为 True

            proxy: 是否使用代理。默认为 True

            timeout: 超时时间。默认为 None

        ### 异常
            ReadFileError: 读取文件错误，不是一个有效的文件
        """
        if isinstance(file, PILImage):
            file = Imager(file)
        if isinstance(file, Imager):
            file = f"base64://{file.to_base64()}"
        file = file_handle(file)
        return super().image(file, *args, **kwargs)

    @classmethod
    def record(
        cls,
        file: str | bytes | BytesIO | Path | MessageResource,
        *args,
        **kwargs,
    ) -> Self:
        """返回一个语音消息段。

        ### 参数
            file: 语音文件，可传入本地路径、网络链接或者其他支持的对象

            magic: 是否是变声文件。默认为 False

            cache: 是否使用缓存。默认为 True

            proxy: 是否使用代理。默认为 True

            timeout: 超时时间。默认为 None

        ### 异常
            ReadFileError: 读取文件错误，不是一个有效的文件
        """
        file = file_handle(file)
        return super().record(file, *args, **kwargs)

    @classmethod
    def video(
        cls,
        file: str | bytes | BytesIO | Path | MessageResource,
        *args,
        **kwargs,
    ) -> Self:
        """返回一个视频消息段。

        ### 参数
            file: 视频文件，可传入本地路径、网络链接或者其他支持的对象

            cache: 是否使用缓存。默认为 True

            proxy: 是否使用代理。默认为 True

            timeout: 超时时间。默认为 None

        ### 异常
            ReadFileError: 读取文件错误，不是一个有效的文件
        """
        file = file_handle(file)
        return super().video(file, *args, **kwargs)

    @classmethod
    def poke(cls, id_: int | str) -> Self:
        """返回一个戳一戳消息段。

        ### 参数
            id_: 目标用户 ID
        """
        return cls("poke", {"qq": str(id_)})

    @classmethod
    def refer(cls, id_: int) -> Self:
        """返回一个合并转发引用消息段。

        ### 参数
            id_: 引用的消息 ID
        """
        return super().node(id_)

    @classmethod
    def node(cls, user_id: int | str, nickname: str, content: "str | Message") -> Self:
        """返回一个合并转发节点消息段。

        ### 参数
            user_id: 用户 ID

            nickname: 用户昵称

            content: 节点内容
        """
        return super().node_custom(int(user_id), nickname, content)


M = TypeVar("M", bound=BaseMessage)


class MessageBuilder:
    def __init__(self, ms: type[BaseMessageSegment]) -> None:
        self.ms = ms

    def __set_name__(self, _owner: type[M], name: str) -> None:
        self.name = name

    def __get__(self, instance: M, owner: type[M]) -> Callable[..., M]:
        def chain(*args, **kwargs) -> M:
            msg = owner() if instance is None else instance
            return msg + getattr(self.ms, self.name)(*args, **kwargs)

        return chain


class Message(BaseMessage):
    """链式消息构造器"""

    __segments: ClassVar[tuple[str, ...]] = (
        "text",
        "face",
        "at",
        "reply",
        "image",
        "anonymous",
        "refer",
        "node",
    )

    for segment in __segments:
        locals()[segment] = MessageBuilder(MessageSegment)
