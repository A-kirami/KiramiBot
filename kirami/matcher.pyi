import re
from datetime import datetime, timedelta, tzinfo
from typing import Any, Literal, NoReturn, TypeVar, overload

from nonebot.dependencies import Dependent
from nonebot.matcher import Matcher as BaseMatcher
from nonebot.permission import Permission
from nonebot.plugin import CommandGroup as BaseCommandGroup
from nonebot.plugin import MatcherGroup as BaseMatcherGroup
from nonebot.rule import ArgumentParser, Rule
from nonebot.typing import (
    T_Handler,
    T_PermissionChecker,
    T_RuleChecker,
)

from kirami.typing import (
    Event,
    Message,
    MessageSegment,
    MessageTemplate,
    State,
)

# ruff: noqa: PYI021

_T = TypeVar("_T")

class Matcher(BaseMatcher):
    state: State
    @classmethod
    async def send(
        cls,
        message: str | Message | MessageSegment | MessageTemplate,
        *,
        at_sender: bool = False,
        reply_message: bool = False,
        recall_time: int = 0,
        argot_content: dict[str, Any] | None = None,
        **kwargs,
    ) -> Any: ...
    @classmethod
    async def finish(
        cls,
        message: str | Message | MessageSegment | MessageTemplate | None = None,
        *,
        at_sender: bool = False,
        reply_message: bool = False,
        recall_time: int = 0,
        argot_content: dict[str, Any] | None = None,
        **kwargs,
    ) -> NoReturn: ...
    @overload
    def get_argot(self, key: None = None) -> dict[str, Any]: ...
    @overload
    def get_argot(self, key: str, default: _T) -> Any | _T: ...
    @overload
    def get_argot(self, key: str, default: None = None) -> Any | None: ...

class MatcherCase(Matcher):
    matcher: type[Matcher] = ...

    def __init__(self, matcher: type[Matcher]) -> None: ...
    @overload
    def __call__(self, func: T_Handler) -> T_Handler: ...
    @overload
    def __call__(self) -> Matcher: ...

def on(
    type: str = "",
    /,
    *,
    rule: Rule | T_RuleChecker | None = None,
    permission: Permission | T_PermissionChecker | None = None,
    handlers: list[T_Handler | Dependent] | None = None,
    temp: bool = False,
    expire_time: datetime | timedelta | None = None,
    priority: int = 1,
    block: bool = False,
    state: State | None = None,
) -> MatcherCase: ...
def on_type(
    *types: type[Event],
    rule: Rule | T_RuleChecker | None = None,
    permission: Permission | T_PermissionChecker | None = None,
    handlers: list[T_Handler | Dependent] | None = None,
    temp: bool = False,
    expire_time: datetime | timedelta | None = None,
    priority: int = 1,
    block: bool = False,
    state: State | None = None,
) -> MatcherCase: ...
def on_metaevent(
    *,
    rule: Rule | T_RuleChecker | None = None,
    handlers: list[T_Handler | Dependent] | None = None,
    temp: bool = False,
    expire_time: datetime | timedelta | None = None,
    priority: int = 1,
    block: bool = False,
    state: State | None = None,
) -> MatcherCase: ...
def on_message(
    *,
    rule: Rule | T_RuleChecker | None = None,
    permission: Permission | T_PermissionChecker | None = None,
    handlers: list[T_Handler | Dependent] | None = None,
    temp: bool = False,
    expire_time: datetime | timedelta | None = None,
    priority: int = 1,
    block: bool = False,
    state: State | None = None,
    to_me: bool = False,
    reply: bool = False,
    argot: bool = False,
) -> MatcherCase: ...
def on_notice(
    *,
    rule: Rule | T_RuleChecker | None = None,
    handlers: list[T_Handler | Dependent] | None = None,
    temp: bool = False,
    expire_time: datetime | timedelta | None = None,
    priority: int = 1,
    block: bool = False,
    state: State | None = None,
) -> MatcherCase: ...
def on_request(
    *,
    rule: Rule | T_RuleChecker | None = None,
    handlers: list[T_Handler | Dependent] | None = None,
    temp: bool = False,
    expire_time: datetime | timedelta | None = None,
    priority: int = 1,
    block: bool = False,
    state: State | None = None,
) -> MatcherCase: ...
def on_command(
    *cmds: str | tuple[str, ...],
    force_whitespace: str | bool | None = None,
    rule: Rule | T_RuleChecker | None = None,
    permission: Permission | T_PermissionChecker | None = None,
    handlers: list[T_Handler | Dependent] | None = None,
    temp: bool = False,
    expire_time: datetime | timedelta | None = None,
    priority: int = 1,
    block: bool = True,
    state: State | None = None,
    to_me: bool = False,
    reply: bool = False,
    argot: bool = False,
) -> MatcherCase: ...
def on_shell_command(
    *cmds: str | tuple[str, ...],
    parser: ArgumentParser | None = None,
    rule: Rule | T_RuleChecker | None = None,
    permission: Permission | T_PermissionChecker | None = None,
    handlers: list[T_Handler | Dependent] | None = None,
    temp: bool = False,
    expire_time: datetime | timedelta | None = None,
    priority: int = 1,
    block: bool = True,
    state: State | None = None,
    to_me: bool = False,
    reply: bool = False,
    argot: bool = False,
) -> MatcherCase: ...
def on_startswith(
    *msgs: str,
    ignorecase: bool = False,
    rule: Rule | T_RuleChecker | None = None,
    permission: Permission | T_PermissionChecker | None = None,
    handlers: list[T_Handler | Dependent] | None = None,
    temp: bool = False,
    expire_time: datetime | timedelta | None = None,
    priority: int = 1,
    block: bool = True,
    state: State | None = None,
    to_me: bool = False,
    reply: bool = False,
    argot: bool = False,
) -> MatcherCase: ...
def on_endswith(
    *msgs: str,
    ignorecase: bool = False,
    rule: Rule | T_RuleChecker | None = None,
    permission: Permission | T_PermissionChecker | None = None,
    handlers: list[T_Handler | Dependent] | None = None,
    temp: bool = False,
    expire_time: datetime | timedelta | None = None,
    priority: int = 1,
    block: bool = True,
    state: State | None = None,
    to_me: bool = False,
    reply: bool = False,
    argot: bool = False,
) -> MatcherCase: ...
def on_fullmatch(
    *msgs: str,
    ignorecase: bool = False,
    rule: Rule | T_RuleChecker | None = None,
    permission: Permission | T_PermissionChecker | None = None,
    handlers: list[T_Handler | Dependent] | None = None,
    temp: bool = False,
    expire_time: datetime | timedelta | None = None,
    priority: int = 1,
    block: bool = True,
    state: State | None = None,
    to_me: bool = False,
    reply: bool = False,
    argot: bool = False,
) -> MatcherCase: ...
def on_keyword(
    *keywords: str,
    rule: Rule | T_RuleChecker | None = None,
    permission: Permission | T_PermissionChecker | None = None,
    handlers: list[T_Handler | Dependent] | None = None,
    temp: bool = False,
    expire_time: datetime | timedelta | None = None,
    priority: int = 1,
    block: bool = True,
    state: State | None = None,
    to_me: bool = False,
    reply: bool = False,
    argot: bool = False,
) -> MatcherCase: ...
def on_regex(
    pattern: str,
    /,
    *,
    flags: int | re.RegexFlag = 0,
    rule: Rule | T_RuleChecker | None = None,
    permission: Permission | T_PermissionChecker | None = None,
    handlers: list[T_Handler | Dependent] | None = None,
    temp: bool = False,
    expire_time: datetime | timedelta | None = None,
    priority: int = 1,
    block: bool = True,
    state: State | None = None,
    to_me: bool = False,
    reply: bool = False,
    argot: bool = False,
) -> MatcherCase: ...
def on_prefix(
    *msgs: str,
    ignorecase: bool = False,
    rule: Rule | T_RuleChecker | None = None,
    permission: Permission | T_PermissionChecker | None = None,
    handlers: list[T_Handler | Dependent] | None = None,
    temp: bool = False,
    expire_time: datetime | timedelta | None = None,
    priority: int = 1,
    block: bool = True,
    state: State | None = None,
    to_me: bool = False,
    reply: bool = False,
    argot: bool = False,
) -> MatcherCase: ...
def on_suffix(
    *msgs: str,
    ignorecase: bool = False,
    rule: Rule | T_RuleChecker | None = None,
    permission: Permission | T_PermissionChecker | None = None,
    handlers: list[T_Handler | Dependent] | None = None,
    temp: bool = False,
    expire_time: datetime | timedelta | None = None,
    priority: int = 1,
    block: bool = True,
    state: State | None = None,
    to_me: bool = False,
    reply: bool = False,
    argot: bool = False,
) -> MatcherCase: ...
@overload
def on_time(
    trigger: Literal["cron"],
    /,
    *,
    year: int | str | None = None,
    month: int | str | None = None,
    day: int | str | None = None,
    week: int | str | None = None,
    day_of_week: int | str | None = None,
    hour: int | str | None = None,
    minute: int | str | None = None,
    second: int | str | None = None,
    jitter: int | None = None,
    start_date: datetime | str | None = None,
    end_date: datetime | str | None = None,
    timezone: tzinfo | str | None = None,
    misfire_grace_time: int = 30,
    rule: Rule | T_RuleChecker | None = None,
    handlers: list[T_Handler | Dependent] | None = None,
    temp: bool = False,
    expire_time: datetime | timedelta | None = None,
    priority: int = 1,
    block: bool = False,
    state: State | None = None,
    **kwargs: Any,
) -> MatcherCase:
    """注册一个 cron 定时事件响应器。

    在当前时间与所有指定的时间约束匹配时触发，与 UNIX cron 调度程序的工作方式类似。

    与 crontab 表达式不同，可以省略不需要的字段。

    大于显式定义的最低有效字段的字段默认为*，而较小字段默认为其最小值，除了默认为*的 `week` 和 `day_of_week`。

    例如，`day=1, minute=20`等于`year='*', month='*', day=1, week='*', day_of_week='*', hour='*'', minute=20, second=0`。

    然后，此定时事件响应器将在每年每月的第一天执行，每小时20分钟。

    ### 表达式类型

    | 表达式 | 时间段 | 描述 |
    |:-----:|:----:|:----:|
    | * |  任何 | 每个时间段触发 |
    | */a | 任何 | 从最小值开始, 每隔 a 个时间段触发 |
    | a-b | 任何 | 在 a-b 范围内的每个时间段触发（a 必须小于 b） |
    | a-b/c | 任何 | 在 a-b 范围内每隔 c 个时间段触发 |
    | xth y | day | 第 x 个星期 y 触发 |
    | last x | day | 月份最后一个星期 x 触发 |
    | last | day | 月份最后一天触发 |
    | x,y,z | 任何 | 可以将以上表达式任意组合 |

    ### 参数
        year: 4位数字的年份

        month: 1-12月

        day: 1-31日

        week: 1-53周

        day_of_week: 一周中的第几天，工作日的数字或名称（0-6或 mon、 tue、 ws、 thu、 fri、 sat、 sun），第一个工作日总是星期一

        hour: 0-23小时

        minute: 0-59分钟

        second: 0-59秒

        start_date: 定时任务开始时间

        end_date: 定时任务结束时间

        timezone: 用于日期/时间计算的时区

        jitter: 定时器执行时间的抖动范围（-x ~ x），单位秒

        misfire_grace_time: 容错时间，单位秒

        rule: 事件响应规则

        handlers: 事件处理函数列表

        temp: 是否为临时事件响应器（仅执行一次）

        expire_time: 事件响应器最终有效时间点，过期即被删除

        priority: 事件响应器优先级

        block: 是否阻止事件向更低优先级传递

        state: 默认会话状态

        **kwargs: 用于传递给定时任务的参数

    [apscheduler.triggers.cron](https://apscheduler.readthedocs.io/en/3.x/modules/triggers/cron.html#module-apscheduler.triggers.cron)
    """
    ...

@overload
def on_time(
    trigger: Literal["interval"],
    /,
    *,
    weeks: int = 0,
    days: int = 0,
    hours: int = 0,
    minutes: int = 0,
    seconds: int = 0,
    jitter: int | None = None,
    start_date: datetime | str | None = None,
    end_date: datetime | str | None = None,
    timezone: tzinfo | str | None = None,
    misfire_grace_time: int = 30,
    rule: Rule | T_RuleChecker | None = None,
    handlers: list[T_Handler | Dependent] | None = None,
    temp: bool = False,
    expire_time: datetime | timedelta | None = None,
    priority: int = 1,
    block: bool = False,
    state: State | None = None,
    **kwargs: Any,
) -> MatcherCase:
    """注册一个间隔定时事件响应器。

    在指定的间隔时间上触发，如果指定了 `start_date`, 则从 `start_date` 开始, 否则为 `datetime.now()` + 间隔时间。

    此定时事件响应器按选定的间隔安排作业周期性运行。

    ### 参数
        weeks: 执行间隔的周数

        days: 执行间隔的天数

        hours: 执行间隔的小时数

        minutes: 执行间隔的分钟数

        seconds: 执行间隔的秒数

        start_date: 定时任务开始时间

        end_date: 定时任务结束时间

        timezone: 用于日期/时间计算的时区

        jitter: 定时器执行时间的抖动范围（-x ~ x），单位秒

        misfire_grace_time: 容错时间，单位秒

        rule: 事件响应规则

        handlers: 事件处理函数列表

        temp: 是否为临时事件响应器（仅执行一次）

        expire_time: 事件响应器最终有效时间点，过期即被删除

        priority: 事件响应器优先级

        block: 是否阻止事件向更低优先级传递

        state: 默认会话状态

    [apscheduler.triggers.interval](https://apscheduler.readthedocs.io/en/3.x/modules/triggers/interval.html#module-apscheduler.triggers.interval)
    """
    ...

@overload
def on_time(
    trigger: Literal["date"],
    /,
    *,
    run_date: str | datetime | None = None,
    timezone: tzinfo | str | None = None,
    misfire_grace_time: int = 30,
    rule: Rule | T_RuleChecker | None = None,
    handlers: list[T_Handler | Dependent] | None = None,
    temp: bool = False,
    expire_time: datetime | timedelta | None = None,
    priority: int = 1,
    block: bool = False,
    state: State | None = None,
    **kwargs: Any,
) -> MatcherCase:
    """注册一个日期定时事件响应器。

    在指定日期时间触发一次。如果 `run_date` 留空，则使用当前时间。

    ### 参数
        run_date: 运行作业的日期/时间

        timezone: 用于日期/时间计算的时区

        misfire_grace_time: 容错时间，单位秒

        rule: 事件响应规则

        handlers: 事件处理函数列表

        temp: 是否为临时事件响应器（仅执行一次）

        expire_time: 事件响应器最终有效时间点，过期即被删除

        priority: 事件响应器优先级

        block: 是否阻止事件向更低优先级传递

        state: 默认会话状态

    [apscheduler.triggers.date](https://apscheduler.readthedocs.io/en/3.x/modules/triggers/date.html#module-apscheduler.triggers.date)
    """
    ...

class CommandGroup(BaseCommandGroup):
    basecmd: tuple[str, ...] = ...
    prefix_aliases: bool = ...
    def __init__(
        self,
        cmd: str | tuple[str, ...],
        prefix_aliases: bool = False,
        rule: Rule | T_RuleChecker | None = None,
        permission: Permission | T_PermissionChecker | None = None,
        handlers: list[T_Handler | Dependent] | None = None,
        temp: bool = False,
        expire_time: datetime | timedelta | None = None,
        priority: int = 1,
        block: bool = False,
        state: State | None = None,
        to_me: bool = False,
        reply: bool = False,
        argot: bool = False,
    ) -> None: ...
    def command(
        self,
        *cmds: str | tuple[str, ...],
        force_whitespace: str | bool | None = None,
        rule: Rule | T_RuleChecker | None = None,
        permission: Permission | T_PermissionChecker | None = None,
        handlers: list[T_Handler | Dependent] | None = None,
        temp: bool = False,
        expire_time: datetime | timedelta | None = None,
        priority: int = 1,
        block: bool = True,
        state: State | None = None,
        to_me: bool = False,
        reply: bool = False,
        argot: bool = False,
    ) -> MatcherCase: ...
    def shell_command(
        self,
        *cmds: str | tuple[str, ...],
        parser: ArgumentParser | None = None,
        rule: Rule | T_RuleChecker | None = None,
        permission: Permission | T_PermissionChecker | None = None,
        handlers: list[T_Handler | Dependent] | None = None,
        temp: bool = False,
        expire_time: datetime | timedelta | None = None,
        priority: int = 1,
        block: bool = True,
        state: State | None = None,
        to_me: bool = False,
        reply: bool = False,
        argot: bool = False,
    ) -> MatcherCase: ...

class MatcherGroup(BaseMatcherGroup):
    def __init__(
        self,
        *,
        type: str = "",
        rule: Rule | T_RuleChecker | None = None,
        permission: Permission | T_PermissionChecker | None = None,
        handlers: list[T_Handler | Dependent] | None = None,
        temp: bool = False,
        expire_time: datetime | timedelta | None = None,
        priority: int = 1,
        block: bool = False,
        state: State | None = None,
        to_me: bool = False,
        reply: bool = False,
        argot: bool = False,
    ) -> None: ...
    def on(
        self,
        type: str = "",
        /,
        *,
        rule: Rule | T_RuleChecker | None = None,
        permission: Permission | T_PermissionChecker | None = None,
        handlers: list[T_Handler | Dependent] | None = None,
        temp: bool = False,
        expire_time: datetime | timedelta | None = None,
        priority: int = 1,
        block: bool = False,
        state: State | None = None,
    ) -> MatcherCase: ...
    def on_type(
        self,
        *types: type[Event],
        rule: Rule | T_RuleChecker | None = None,
        permission: Permission | T_PermissionChecker | None = None,
        handlers: list[T_Handler | Dependent] | None = None,
        temp: bool = False,
        expire_time: datetime | timedelta | None = None,
        priority: int = 1,
        block: bool = True,
        state: State | None = None,
    ) -> MatcherCase: ...
    def on_metaevent(
        self,
        *,
        rule: Rule | T_RuleChecker | None = None,
        handlers: list[T_Handler | Dependent] | None = None,
        temp: bool = False,
        expire_time: datetime | timedelta | None = None,
        priority: int = 1,
        block: bool = False,
        state: State | None = None,
    ) -> MatcherCase: ...
    def on_message(
        self,
        *,
        rule: Rule | T_RuleChecker | None = None,
        permission: Permission | T_PermissionChecker | None = None,
        handlers: list[T_Handler | Dependent] | None = None,
        temp: bool = False,
        expire_time: datetime | timedelta | None = None,
        priority: int = 1,
        block: bool = False,
        state: State | None = None,
        to_me: bool = False,
        reply: bool = False,
        argot: bool = False,
    ) -> MatcherCase: ...
    def on_notice(
        self,
        *,
        rule: Rule | T_RuleChecker | None = None,
        handlers: list[T_Handler | Dependent] | None = None,
        temp: bool = False,
        expire_time: datetime | timedelta | None = None,
        priority: int = 1,
        block: bool = False,
        state: State | None = None,
    ) -> MatcherCase: ...
    def on_request(
        self,
        *,
        rule: Rule | T_RuleChecker | None = None,
        handlers: list[T_Handler | Dependent] | None = None,
        temp: bool = False,
        expire_time: datetime | timedelta | None = None,
        priority: int = 1,
        block: bool = False,
        state: State | None = None,
    ) -> MatcherCase: ...
    def on_command(
        self,
        *cmds: str | tuple[str, ...],
        force_whitespace: str | bool | None = None,
        rule: Rule | T_RuleChecker | None = None,
        permission: Permission | T_PermissionChecker | None = None,
        handlers: list[T_Handler | Dependent] | None = None,
        temp: bool = False,
        expire_time: datetime | timedelta | None = None,
        priority: int = 1,
        block: bool = True,
        state: State | None = None,
        to_me: bool = False,
        reply: bool = False,
        argot: bool = False,
    ) -> MatcherCase: ...
    def on_shell_command(
        self,
        *cmds: str | tuple[str, ...],
        parser: ArgumentParser | None = None,
        rule: Rule | T_RuleChecker | None = None,
        permission: Permission | T_PermissionChecker | None = None,
        handlers: list[T_Handler | Dependent] | None = None,
        temp: bool = False,
        expire_time: datetime | timedelta | None = None,
        priority: int = 1,
        block: bool = True,
        state: State | None = None,
        to_me: bool = False,
        reply: bool = False,
        argot: bool = False,
    ) -> MatcherCase: ...
    def on_startswith(
        self,
        *msgs: str,
        ignorecase: bool = False,
        rule: Rule | T_RuleChecker | None = None,
        permission: Permission | T_PermissionChecker | None = None,
        handlers: list[T_Handler | Dependent] | None = None,
        temp: bool = False,
        expire_time: datetime | timedelta | None = None,
        priority: int = 1,
        block: bool = True,
        state: State | None = None,
        to_me: bool = False,
        reply: bool = False,
        argot: bool = False,
    ) -> MatcherCase: ...
    def on_endswith(
        self,
        *msgs: str,
        ignorecase: bool = False,
        rule: Rule | T_RuleChecker | None = None,
        permission: Permission | T_PermissionChecker | None = None,
        handlers: list[T_Handler | Dependent] | None = None,
        temp: bool = False,
        expire_time: datetime | timedelta | None = None,
        priority: int = 1,
        block: bool = True,
        state: State | None = None,
        to_me: bool = False,
        reply: bool = False,
        argot: bool = False,
    ) -> MatcherCase: ...
    def on_fullmatch(
        self,
        *msgs: str,
        ignorecase: bool = False,
        rule: Rule | T_RuleChecker | None = None,
        permission: Permission | T_PermissionChecker | None = None,
        handlers: list[T_Handler | Dependent] | None = None,
        temp: bool = False,
        expire_time: datetime | timedelta | None = None,
        priority: int = 1,
        block: bool = True,
        state: State | None = None,
        to_me: bool = False,
        reply: bool = False,
        argot: bool = False,
    ) -> MatcherCase: ...
    def on_keyword(
        self,
        *keywords: str,
        rule: Rule | T_RuleChecker | None = None,
        permission: Permission | T_PermissionChecker | None = None,
        handlers: list[T_Handler | Dependent] | None = None,
        temp: bool = False,
        expire_time: datetime | timedelta | None = None,
        priority: int = 1,
        block: bool = True,
        state: State | None = None,
        to_me: bool = False,
        reply: bool = False,
        argot: bool = False,
    ) -> MatcherCase: ...
    def on_regex(
        self,
        pattern: str,
        /,
        *,
        flags: int | re.RegexFlag = 0,
        rule: Rule | T_RuleChecker | None = None,
        permission: Permission | T_PermissionChecker | None = None,
        handlers: list[T_Handler | Dependent] | None = None,
        temp: bool = False,
        expire_time: datetime | timedelta | None = None,
        priority: int = 1,
        block: bool = True,
        state: State | None = None,
        to_me: bool = False,
        reply: bool = False,
        argot: bool = False,
    ) -> MatcherCase: ...
    def on_prefix(
        self,
        *msgs: str,
        ignorecase: bool = False,
        rule: Rule | T_RuleChecker | None = None,
        permission: Permission | T_PermissionChecker | None = None,
        handlers: list[T_Handler | Dependent] | None = None,
        temp: bool = False,
        expire_time: datetime | timedelta | None = None,
        priority: int = 1,
        block: bool = True,
        state: State | None = None,
        to_me: bool = False,
        reply: bool = False,
        argot: bool = False,
    ) -> MatcherCase: ...
    def on_suffix(
        self,
        *msgs: str,
        ignorecase: bool = False,
        rule: Rule | T_RuleChecker | None = None,
        permission: Permission | T_PermissionChecker | None = None,
        handlers: list[T_Handler | Dependent] | None = None,
        temp: bool = False,
        expire_time: datetime | timedelta | None = None,
        priority: int = 1,
        block: bool = True,
        state: State | None = None,
        to_me: bool = False,
        reply: bool = False,
        argot: bool = False,
    ) -> MatcherCase: ...
    @overload
    def on_time(
        self,
        trigger: Literal["cron"],
        /,
        *,
        year: int | str | None = None,
        month: int | str | None = None,
        day: int | str | None = None,
        week: int | str | None = None,
        day_of_week: int | str | None = None,
        hour: int | str | None = None,
        minute: int | str | None = None,
        second: int | str | None = None,
        jitter: int | None = None,
        start_date: datetime | str | None = None,
        end_date: datetime | str | None = None,
        timezone: tzinfo | str | None = None,
        misfire_grace_time: int = 30,
        rule: Rule | T_RuleChecker | None = None,
        handlers: list[T_Handler | Dependent] | None = None,
        temp: bool = False,
        expire_time: datetime | timedelta | None = None,
        priority: int = 1,
        block: bool = False,
        state: State | None = None,
        **kwargs: Any,
    ) -> MatcherCase:
        """注册一个 cron 定时事件响应器。

        在当前时间与所有指定的时间约束匹配时触发，与 UNIX cron 调度程序的工作方式类似。

        与 crontab 表达式不同，可以省略不需要的字段。

        大于显式定义的最低有效字段的字段默认为*，而较小字段默认为其最小值，除了默认为*的 `week` 和 `day_of_week`。

        例如，`day=1, minute=20`等于`year='*', month='*', day=1, week='*', day_of_week='*', hour='*'', minute=20, second=0`。

        然后，此定时事件响应器将在每年每月的第一天执行，每小时20分钟。

        ### 表达式类型

        | 表达式 | 时间段 | 描述 |
        |:-----:|:----:|:----:|
        | * |  任何 | 每个时间段触发 |
        | */a | 任何 | 从最小值开始, 每隔 a 个时间段触发 |
        | a-b | 任何 | 在 a-b 范围内的每个时间段触发（a 必须小于 b） |
        | a-b/c | 任何 | 在 a-b 范围内每隔 c 个时间段触发 |
        | xth y | day | 第 x 个星期 y 触发 |
        | last x | day | 月份最后一个星期 x 触发 |
        | last | day | 月份最后一天触发 |
        | x,y,z | 任何 | 可以将以上表达式任意组合 |

        ### 参数
            year: 4位数字的年份

            month: 1-12月

            day: 1-31日

            week: 1-53周

            day_of_week: 一周中的第几天，工作日的数字或名称（0-6或 mon、 tue、 ws、 thu、 fri、 sat、 sun），第一个工作日总是星期一

            hour: 0-23小时

            minute: 0-59分钟

            second: 0-59秒

            start_date: 定时任务开始时间

            end_date: 定时任务结束时间

            timezone: 用于日期/时间计算的时区

            jitter: 定时器执行时间的抖动范围（-x ~ x），单位秒

            misfire_grace_time: 容错时间，单位秒

            rule: 事件响应规则

            handlers: 事件处理函数列表

            temp: 是否为临时事件响应器（仅执行一次）

            expire_time: 事件响应器最终有效时间点，过期即被删除

            priority: 事件响应器优先级

            block: 是否阻止事件向更低优先级传递

            state: 默认会话状态

            **kwargs: 用于传递给定时任务的参数

        [apscheduler.triggers.cron](https://apscheduler.readthedocs.io/en/3.x/modules/triggers/cron.html#module-apscheduler.triggers.cron)
        """
        ...
    @overload
    def on_time(
        self,
        trigger: Literal["interval"],
        /,
        *,
        weeks: int = 0,
        days: int = 0,
        hours: int = 0,
        minutes: int = 0,
        seconds: int = 0,
        jitter: int | None = None,
        start_date: datetime | str | None = None,
        end_date: datetime | str | None = None,
        timezone: tzinfo | str | None = None,
        misfire_grace_time: int = 30,
        rule: Rule | T_RuleChecker | None = None,
        handlers: list[T_Handler | Dependent] | None = None,
        temp: bool = False,
        expire_time: datetime | timedelta | None = None,
        priority: int = 1,
        block: bool = False,
        state: State | None = None,
        **kwargs: Any,
    ) -> MatcherCase:
        """注册一个间隔定时事件响应器。

        在指定的间隔时间上触发，如果指定了 `start_date`, 则从 `start_date` 开始, 否则为 `datetime.now()` + 间隔时间。

        此定时事件响应器按选定的间隔安排作业周期性运行。

        ### 参数
            weeks: 执行间隔的周数

            days: 执行间隔的天数

            hours: 执行间隔的小时数

            minutes: 执行间隔的分钟数

            seconds: 执行间隔的秒数

            start_date: 定时任务开始时间

            end_date: 定时任务结束时间

            timezone: 用于日期/时间计算的时区

            jitter: 定时器执行时间的抖动范围（-x ~ x），单位秒

            misfire_grace_time: 容错时间，单位秒

            rule: 事件响应规则

            handlers: 事件处理函数列表

            temp: 是否为临时事件响应器（仅执行一次）

            expire_time: 事件响应器最终有效时间点，过期即被删除

            priority: 事件响应器优先级

            block: 是否阻止事件向更低优先级传递

            state: 默认会话状态

        [apscheduler.triggers.interval](https://apscheduler.readthedocs.io/en/3.x/modules/triggers/interval.html#module-apscheduler.triggers.interval)
        """
        ...
    @overload
    def on_time(
        self,
        trigger: Literal["date"],
        /,
        *,
        run_date: str | datetime | None = None,
        timezone: tzinfo | str | None = None,
        misfire_grace_time: int = 30,
        rule: Rule | T_RuleChecker | None = None,
        handlers: list[T_Handler | Dependent] | None = None,
        temp: bool = False,
        expire_time: datetime | timedelta | None = None,
        priority: int = 1,
        block: bool = False,
        state: State | None = None,
        **kwargs: Any,
    ) -> MatcherCase:
        """注册一个日期定时事件响应器。

        在指定日期时间触发一次。如果 `run_date` 留空，则使用当前时间。

        ### 参数
            run_date: 运行作业的日期/时间

            timezone: 用于日期/时间计算的时区

            misfire_grace_time: 容错时间，单位秒

            rule: 事件响应规则

            handlers: 事件处理函数列表

            temp: 是否为临时事件响应器（仅执行一次）

            expire_time: 事件响应器最终有效时间点，过期即被删除

            priority: 事件响应器优先级

            block: 是否阻止事件向更低优先级传递

            state: 默认会话状态

        [apscheduler.triggers.date](https://apscheduler.readthedocs.io/en/3.x/modules/triggers/date.html#module-apscheduler.triggers.date)
        """
        ...
