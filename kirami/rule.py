"""本模块定义了内置响应器的各类规则"""

import re
from typing import Any

from nonebot.consts import ENDSWITH_KEY, STARTSWITH_KEY
from nonebot.rule import ArgumentParser as ArgumentParser
from nonebot.rule import EndswithRule, StartswithRule
from nonebot.rule import Rule as Rule

from kirami.database import Argot
from kirami.event import Event, MessageEvent, TimerNoticeEvent
from kirami.state import State


class PrefixRule(StartswithRule):
    """检查消息纯文本是否以指定字符串开头并移除前缀。

    ### 参数
        msg: 指定消息开头字符串元组

        ignorecase: 是否忽略大小写
    """

    __slots__ = ("msg", "ignorecase")

    def __repr__(self) -> str:
        return f"Prefix(msg={self.msg}, ignorecase={self.ignorecase})"

    async def __call__(self, event: Event, state: State) -> bool:
        try:
            text = event.get_plaintext()
        except Exception:
            return False
        if match := re.match(
            f"^(?:{'|'.join(re.escape(prefix) for prefix in self.msg)})",
            text,
            re.IGNORECASE if self.ignorecase else 0,
        ):
            prefix = match.group()
            state[STARTSWITH_KEY] = prefix

            # 从消息中移除前缀
            message = event.get_message()
            message_seg = message.pop(0)
            if message_seg.is_text() and (
                mseg_str := str(message_seg).removeprefix(prefix).lstrip()
            ):
                new_message = message.__class__(mseg_str)
                for new_segment in reversed(new_message):
                    message.insert(0, new_segment)
            return True
        return False


def prefix(msg: tuple[str, ...], ignorecase: bool = False) -> Rule:
    """匹配消息纯文本开头。在匹配成功时，会将前缀从消息中移除。

    ### 参数
        msg: 指定消息开头字符串元组

        ignorecase: 是否忽略大小写
    """
    return Rule(PrefixRule(msg, ignorecase))


class SuffixRule(EndswithRule):
    """检查消息纯文本是否以指定字符串结尾并移除后缀。

    ### 参数
        msg: 指定消息结尾字符串元组

        ignorecase: 是否忽略大小写
    """

    __slots__ = ("msg", "ignorecase")

    def __repr__(self) -> str:
        return f"Suffix(msg={self.msg}, ignorecase={self.ignorecase})"

    async def __call__(self, event: Event, state: State) -> bool:
        try:
            text = event.get_plaintext()
        except Exception:
            return False
        if match := re.search(
            f"(?:{'|'.join(re.escape(suffix) for suffix in self.msg)})$",
            text,
            re.IGNORECASE if self.ignorecase else 0,
        ):
            suffix = match.group()
            state[ENDSWITH_KEY] = suffix

            # 从消息中移除后缀
            message = event.get_message()
            message_seg = message.pop(0)
            if message_seg.is_text() and (
                mseg_str := str(message_seg).removesuffix(suffix).lstrip()
            ):
                new_message = message.__class__(mseg_str)
                for new_segment in reversed(new_message):
                    message.insert(0, new_segment)
            return True
        return False


def suffix(msg: tuple[str, ...], ignorecase: bool = False) -> Rule:
    """匹配消息纯文本结尾。在匹配成功时，会将后缀从消息中移除。

    ### 参数
        msg: 指定消息开头字符串元组

        ignorecase: 是否忽略大小写
    """
    return Rule(SuffixRule(msg, ignorecase))


class ReplyRule:
    """检查是否是回复消息"""

    __slots__ = ()

    def __repr__(self) -> str:
        return "ReplyMe()"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, self.__class__)

    def __hash__(self) -> int:
        return hash((self.__class__,))

    async def __call__(self, event: MessageEvent) -> bool:
        return bool(event.reply)


class ArgotRule:
    """检查是否存在暗语"""

    __slots__ = ()

    def __repr__(self) -> str:
        return "Argot()"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, self.__class__)

    def __hash__(self) -> int:
        return hash((self.__class__,))

    async def __call__(self, event: MessageEvent, state: State) -> bool:
        if not event.reply:
            return False
        if argot := await Argot.get(event.reply.message_id):
            state["_argot"] = argot.content
            return True
        return False


class TimerRule:
    """响应指定的定时器事件

    ### 参数
        timer_id: 定时器 ID

        timer_params: 定时器参数
    """

    __slots__ = ("timer_id", "timer_params")

    def __init__(self, timer_id: str, timer_params: dict[str, Any]) -> None:
        self.timer_id = timer_id
        self.timer_params = timer_params

    def __repr__(self) -> str:
        return f"Timer(timer_id={self.timer_id}), timer_params={self.timer_params}"

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, self.__class__)
            and self.timer_id == other.timer_id
            and self.timer_params == other.timer_params
        )

    def __hash__(self) -> int:
        return hash((self.__class__,))

    async def __call__(self, event: TimerNoticeEvent) -> bool:
        return event.timer_id == self.timer_id
