"""本模块提供了一些常用的工具函数"""

from collections.abc import Callable
from typing import TypeVar

from nonebot.adapters.onebot.v11 import Message, MessageEvent
from nonebot.matcher import Matcher

T = TypeVar("T")


async def extract_match(
    extract_func: Callable[..., T],
    event: MessageEvent,
    matcher: Matcher,
    prompt: str | None = None,
    from_reply: bool = False,
) -> T:
    """从消息中提取指定内容。

    ### 参数
        extract_func: 提取函数

        event: 消息事件

        matcher: 事件响应器

        prompt: 当提取为空时的提示

        from_reply: 是否从回复消息中提取
    """
    message = reply.message if (reply := event.reply) and from_reply else event.message
    result = extract_func(message)
    if not result and prompt:
        await matcher.finish(prompt)
    return result


def extract_image_urls(message: Message) -> list[str]:
    """提取消息中的图片链接。

    ### 参数
        message: 消息对象

    ### 返回
        图片链接列表
    """
    return [
        segment.data["url"] for segment in message["image"] if "url" in segment.data
    ]


def extract_at_users(message: Message) -> list[str]:
    """提取消息中提及的用户。

    ### 参数
        message: 消息对象

    ### 返回
        提及用户列表
    """
    return [segment.data["qq"] for segment in message["at"]]


def extract_plain_text(message: Message) -> str:
    """提取消息中纯文本消息。

    ### 参数
        message: 消息对象

    ### 返回
        纯文本消息
    """
    return message.extract_plain_text().strip()
