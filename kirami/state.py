"""本模块定义了会话状态类"""

from re import Match
from typing import Any

from nonebot.adapters.onebot.v11 import Message, MessageSegment
from nonebot.consts import (
    CMD_ARG_KEY,
    CMD_KEY,
    CMD_START_KEY,
    CMD_WHITESPACE_KEY,
    ENDSWITH_KEY,
    FULLMATCH_KEY,
    KEYWORD_KEY,
    PREFIX_KEY,
    RAW_CMD_KEY,
    REGEX_MATCHED,
    SHELL_ARGS,
    SHELL_ARGV,
    STARTSWITH_KEY,
)
from nonebot.exception import ParserExit
from nonebot.rule import Namespace
from nonebot.typing import T_State
from typing_extensions import Self


class BaseState(T_State):
    def __getattr__(self, name: str, /) -> Any:
        if name in self:
            item = super().__getitem__(name)
            return self.__class__(item) if isinstance(item, dict) else item
        return super().__getattribute__(name)

    def __setattr__(self, name: str, value: Any, /) -> None:
        return super().__setitem__(name, value)

    def __delattr__(self, name: str, /) -> None:
        return super().__delitem__(name)

    def copy(self) -> Self:
        return self.__class__(super().copy())


class State(BaseState):
    """会话状态"""

    @property
    def argot(self) -> dict[str, Any]:
        """暗语"""
        return self["_argot"]

    @property
    def startswith(self) -> str:
        """响应触发前缀"""
        return self[STARTSWITH_KEY]

    @property
    def prefix(self) -> str:
        """响应触发前缀"""
        return self[STARTSWITH_KEY]

    @property
    def endswith(self) -> str:
        """响应触发后缀"""
        return self[ENDSWITH_KEY]

    @property
    def suffix(self) -> str:
        """响应触发后缀"""
        return self[ENDSWITH_KEY]

    @property
    def fullmatch(self) -> str:
        """响应触发完整消息"""
        return self[FULLMATCH_KEY]

    @property
    def keyword(self) -> str:
        """响应触发关键字"""
        return self[KEYWORD_KEY]

    @property
    def matched(self) -> Match[str]:
        """正则匹配结果"""
        return self[REGEX_MATCHED]

    @property
    def shell_args(self) -> Namespace | ParserExit:
        """shell 命令解析后的参数字典"""
        return self[SHELL_ARGS]

    @property
    def shell_argv(self) -> list[str | MessageSegment]:
        """shell 命令原始参数列表"""
        return self[SHELL_ARGV]

    @property
    def command(self) -> tuple[str, ...]:
        """消息命令元组"""
        return self[PREFIX_KEY][CMD_KEY]

    @property
    def raw_command(self) -> str:
        """消息命令文本"""
        return self[PREFIX_KEY][RAW_CMD_KEY]

    @property
    def command_arg(self) -> Message:
        """消息命令参数"""
        return self[PREFIX_KEY][CMD_ARG_KEY]

    @property
    def command_start(self) -> str:
        """消息命令开头"""
        return self[PREFIX_KEY][CMD_START_KEY]

    @property
    def command_whitespace(self) -> str:
        """消息命令与参数间空白符"""
        return self[PREFIX_KEY][CMD_WHITESPACE_KEY]
