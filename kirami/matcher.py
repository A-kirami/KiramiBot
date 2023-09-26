"""本模块对原生事件响应器进行定制，并提供一些常用事件响应器的注册工具"""

import asyncio
import re
import time
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Literal, NoReturn, TypeVar

from nonebot import get_bots
from nonebot.adapters import Bot, Event
from nonebot.dependencies import Dependent
from nonebot.matcher import Matcher as BaseMatcher
from nonebot.matcher import current_bot
from nonebot.message import handle_event
from nonebot.permission import Permission
from nonebot.plugin import CommandGroup as BaseCommandGroup
from nonebot.plugin import MatcherGroup as BaseMatcherGroup
from nonebot.plugin.on import get_matcher_module, get_matcher_plugin, store_matcher
from nonebot.rule import (
    ArgumentParser,
    Rule,
    ToMeRule,
    command,
    endswith,
    fullmatch,
    is_type,
    keyword,
    regex,
    shell_command,
    startswith,
)
from nonebot.typing import (
    T_Handler,
    T_PermissionChecker,
    T_RuleChecker,
)

from kirami.database import Argot
from kirami.event import TimerNoticeEvent
from kirami.message import (
    Message,
    MessageSegment,
    MessageTemplate,
)
from kirami.rule import ArgotRule, ReplyRule, TimerRule, prefix, suffix
from kirami.state import State
from kirami.utils import scheduler

T = TypeVar("T")

_param_rules = {
    "to_me": ToMeRule,
    "reply": ReplyRule,
    "argot": ArgotRule,
}


def _extend_rule(rule: Rule | T_RuleChecker | None, **kwargs) -> Rule:
    rule &= Rule()
    for key in _param_rules:
        if kwargs.get(key, None):
            rule &= Rule(_param_rules[key]())
    return rule


class Matcher(BaseMatcher):
    state: State

    @classmethod
    def destroy(cls) -> None:
        for checker in cls.rule.checkers:
            if isinstance(checker.call, TimerRule):
                scheduler.remove_job(checker.call.timer_id)
        super().destroy()

    @classmethod
    async def send(
        cls,
        message: str | Message | MessageSegment | MessageTemplate,
        **kwargs: Any,
    ) -> Any:
        """发送一条消息给当前交互用户。

        ### 参数
            message: 消息内容

            at_sender: at 发送者

            reply_message: 回复原消息

            recall_time: 指定时间后撤回消息

            argot_content: 消息暗语内容

            **kwargs: 用于传递给 API 的参数
        """
        info = await super().send(message, **kwargs)
        if argot := kwargs.pop("argot_content", None):
            await Argot(msg_id=info["message_id"], content=argot).save()
        if recall_time := kwargs.pop("recall_time", None):
            bot = current_bot.get()
            loop = asyncio.get_running_loop()
            loop.call_later(
                recall_time,
                lambda: loop.create_task(bot.delete_msg(message_id=info["message_id"])),
            )
        return info

    @classmethod
    async def finish(
        cls,
        message: str | Message | MessageSegment | MessageTemplate | None = None,
        **kwargs,
    ) -> NoReturn:
        """发送一条消息给当前交互用户并结束当前事件响应器。

        ### 参数
            message: 消息内容

            at_sender: at 发送者

            reply_message: 回复原消息

            recall_time: 指定时间后撤回消息

            argot_content: 消息暗语内容

            **kwargs: 用于传递给 API 的参数
        """
        await super().finish(message, **kwargs)

    def get_argot(self, key: str | None = None, default: T | None = None) -> Any | T:
        """获取指定的 `argot` 内容

        如果没有找到对应的内容，返回 `default` 值
        """
        return self.state.argot.get(key, default) if key else self.state.argot


class MatcherCase:
    """事件响应器容器类，用于包装事件响应器，以使其支持简写形式"""

    def __init__(self, matcher: type[Matcher]) -> None:
        """将 `Matcher` 包装为 `MatcherCase`"""
        self.matcher = matcher
        """被包装的事件响应器"""

    def __call__(self, func: T_Handler | None = None) -> T_Handler | Matcher:
        if func:
            self.matcher.append_handler(func)
            return func
        return self.matcher()

    def __getattr__(self, name: str, /) -> Any:
        return getattr(self.matcher, name)

    def __setattr__(self, name: str, value: Any, /) -> None:
        if name == "matcher":
            super().__setattr__(name, value)
        else:
            setattr(self.matcher, name, value)


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
    _depth: int = 0,
) -> MatcherCase:
    """注册一个基础事件响应器，可自定义类型。

    ### 参数
        type: 事件响应器类型

        rule: 事件响应规则

        permission: 事件响应权限

        handlers: 事件处理函数列表

        temp: 是否为临时事件响应器（仅执行一次）

        expire_time: 事件响应器最终有效时间点，过期即被删除

        priority: 事件响应器优先级

        block: 是否阻止事件向更低优先级传递

        state: 默认会话状态
    """
    matcher = Matcher.new(
        type,
        Rule() & rule,
        Permission() | permission,
        temp=temp,
        expire_time=expire_time,
        priority=priority,
        block=block,
        handlers=handlers,
        plugin=get_matcher_plugin(_depth + 1),
        module=get_matcher_module(_depth + 1),
        default_state=state,
    )
    if not state:
        matcher._default_state = State()
    store_matcher(matcher)
    return MatcherCase(matcher)


def on_type(
    *types: type[Event],
    rule: Rule | T_RuleChecker | None = None,
    _depth: int = 0,
    **kwargs,
) -> MatcherCase:
    """注册一个事件响应器，并且当事件为指定类型时响应。

    ### 参数
        *types: 事件类型

        rule: 事件响应规则

        permission: 事件响应权限

        handlers: 事件处理函数列表

        temp: 是否为临时事件响应器（仅执行一次）

        expire_time: 事件响应器最终有效时间点，过期即被删除

        priority: 事件响应器优先级

        block: 是否阻止事件向更低优先级传递

        state: 默认会话状态
    """
    return on(rule=is_type(*types) & rule, **kwargs, _depth=_depth + 1)


def on_metaevent(*, _depth: int = 0, **kwargs) -> MatcherCase:
    """注册一个元事件响应器。

    ### 参数
        rule: 事件响应规则

        handlers: 事件处理函数列表

        temp: 是否为临时事件响应器（仅执行一次）

        expire_time: 事件响应器最终有效时间点，过期即被删除

        priority: 事件响应器优先级

        block: 是否阻止事件向更低优先级传递

        state: 默认会话状态
    """
    return on("meta_event", **kwargs, _depth=_depth + 1)


def on_message(
    *, rule: Rule | T_RuleChecker | None = None, _depth: int = 0, **kwargs
) -> MatcherCase:
    """注册一个消息事件响应器。

    ### 参数
        rule: 事件响应规则

        permission: 事件响应权限

        handlers: 事件处理函数列表

        temp: 是否为临时事件响应器（仅执行一次）

        expire_time: 事件响应器最终有效时间点，过期即被删除

        priority: 事件响应器优先级

        block: 是否阻止事件向更低优先级传递

        state: 默认会话状态

        to_me: 是否仅响应与自身有关的消息

        reply: 是否仅响应回复消息

        argot: 是否仅响应暗语消息，当 `argot` 为 `True` 时，`priority` 会被强制设置为 `0`
    """
    if "argot" in kwargs:
        kwargs["priority"] = 0
    return on(
        "message",
        rule=_extend_rule(rule, **kwargs),
        **{k: v for k, v in kwargs.items() if k not in _param_rules},
        _depth=_depth + 1,
    )


def on_notice(*, _depth: int = 0, **kwargs) -> MatcherCase:
    """注册一个通知事件响应器。

    ### 参数
        rule: 事件响应规则

        handlers: 事件处理函数列表

        temp: 是否为临时事件响应器（仅执行一次）

        expire_time: 事件响应器最终有效时间点，过期即被删除

        priority: 事件响应器优先级

        block: 是否阻止事件向更低优先级传递

        state: 默认会话状态
    """
    return on("notice", **kwargs, _depth=_depth + 1)


def on_request(*, _depth: int = 0, **kwargs) -> MatcherCase:
    """注册一个请求事件响应器。

    ### 参数
        rule: 事件响应规则

        handlers: 事件处理函数列表

        temp: 是否为临时事件响应器（仅执行一次）

        expire_time: 事件响应器最终有效时间点，过期即被删除

        priority: 事件响应器优先级

        block: 是否阻止事件向更低优先级传递

        state: 默认会话状态
    """
    return on("request", **kwargs, _depth=_depth + 1)


def on_command(
    *cmds: str | tuple[str, ...],
    force_whitespace: str | bool | None = None,
    rule: Rule | T_RuleChecker | None = None,
    _depth: int = 0,
    **kwargs,
) -> MatcherCase:
    """注册一个消息事件响应器，并且当消息以指定命令开头时响应。

    ### 参数
        *cmds: 指定命令内容

        force_whitespace: 是否强制命令后必须有指定空白符

        rule: 事件响应规则

        permission: 事件响应权限

        handlers: 事件处理函数列表

        temp: 是否为临时事件响应器（仅执行一次）

        expire_time: 事件响应器最终有效时间点，过期即被删除

        priority: 事件响应器优先级

        block: 是否阻止事件向更低优先级传递

        state: 默认会话状态

        to_me: 是否仅响应与自身有关的消息

        reply: 是否仅响应回复消息

        argot: 是否仅响应暗语消息，当 `argot` 为 `True` 时，`priority` 会被强制设置为 `0`
    """
    kwargs.setdefault("block", True)
    return on_message(
        rule=command(*cmds, force_whitespace=force_whitespace) & rule,
        **kwargs,
        _depth=_depth + 1,
    )


def on_shell_command(
    *cmds: str | tuple[str, ...],
    parser: ArgumentParser | None = None,
    rule: Rule | T_RuleChecker | None = None,
    _depth: int = 0,
    **kwargs,
) -> MatcherCase:
    """注册一个支持 `shell_like` 解析参数的命令消息事件响应器。

    与普通的 `on_command` 不同的是，在添加 `parser` 参数时, 响应器会自动处理消息。

    并将用户输入的原始参数列表保存在 `state.shell_argv`, `parser` 处理的参数保存在 `state.shell_args` 中

    ### 参数
        *cmds: 指定命令内容

        parser: `kirami.rule.ArgumentParser` 对象

        rule: 事件响应规则

        permission: 事件响应权限

        handlers: 事件处理函数列表

        temp: 是否为临时事件响应器（仅执行一次）

        expire_time: 事件响应器最终有效时间点，过期即被删除

        priority: 事件响应器优先级

        block: 是否阻止事件向更低优先级传递

        state: 默认会话状态

        to_me: 是否仅响应与自身有关的消息

        reply: 是否仅响应回复消息

        argot: 是否仅响应暗语消息，当 `argot` 为 `True` 时，`priority` 会被强制设置为 `0`
    """
    kwargs.setdefault("block", True)
    return on_message(
        rule=shell_command(*cmds, parser=parser) & rule,
        **kwargs,
        _depth=_depth + 1,
    )


def on_startswith(
    *msgs: str,
    ignorecase: bool = False,
    rule: Rule | T_RuleChecker | None = None,
    _depth: int = 0,
    **kwargs,
) -> MatcherCase:
    """注册一个消息事件响应器，并且当消息的**文本部分**以指定内容开头时响应。

    ### 参数
        *msgs: 指定消息开头内容

        ignorecase: 是否忽略大小写

        rule: 事件响应规则

        permission: 事件响应权限

        handlers: 事件处理函数列表

        temp: 是否为临时事件响应器（仅执行一次）

        expire_time: 事件响应器最终有效时间点，过期即被删除

        priority: 事件响应器优先级

        block: 是否阻止事件向更低优先级传递

        state: 默认会话状态

        to_me: 是否仅响应与自身有关的消息

        reply: 是否仅响应回复消息

        argot: 是否仅响应暗语消息，当 `argot` 为 `True` 时，`priority` 会被强制设置为 `0`
    """
    kwargs.setdefault("block", True)
    return on_message(
        rule=startswith(msgs, ignorecase) & rule, **kwargs, _depth=_depth + 1
    )


def on_endswith(
    *msgs: str,
    ignorecase: bool = False,
    rule: Rule | T_RuleChecker | None = None,
    _depth: int = 0,
    **kwargs,
) -> MatcherCase:
    """注册一个消息事件响应器，并且当消息的**文本部分**以指定内容结尾时响应。

    ### 参数
        *msgs: 指定消息结尾内容

        ignorecase: 是否忽略大小写

        rule: 事件响应规则

        permission: 事件响应权限

        handlers: 事件处理函数列表

        temp: 是否为临时事件响应器（仅执行一次）

        expire_time: 事件响应器最终有效时间点，过期即被删除

        priority: 事件响应器优先级

        block: 是否阻止事件向更低优先级传递

        state: 默认会话状态

        to_me: 是否仅响应与自身有关的消息

        reply: 是否仅响应回复消息

        argot: 是否仅响应暗语消息，当 `argot` 为 `True` 时，`priority` 会被强制设置为 `0`
    """
    kwargs.setdefault("block", True)
    return on_message(
        rule=endswith(msgs, ignorecase) & rule, **kwargs, _depth=_depth + 1
    )


def on_fullmatch(
    *msgs: str,
    ignorecase: bool = False,
    rule: Rule | T_RuleChecker | None = None,
    _depth: int = 0,
    **kwargs,
) -> MatcherCase:
    """注册一个消息事件响应器，并且当消息的**文本部分**与指定内容完全一致时响应。

    ### 参数
        *msgs: 指定消息全匹配内容

        ignorecase: 是否忽略大小写

        rule: 事件响应规则

        permission: 事件响应权限

        handlers: 事件处理函数列表

        temp: 是否为临时事件响应器（仅执行一次）

        expire_time: 事件响应器最终有效时间点，过期即被删除

        priority: 事件响应器优先级

        block: 是否阻止事件向更低优先级传递

        state: 默认会话状态

        to_me: 是否仅响应与自身有关的消息

        reply: 是否仅响应回复消息

        argot: 是否仅响应暗语消息，当 `argot` 为 `True` 时，`priority` 会被强制设置为 `0`
    """
    kwargs.setdefault("block", True)
    return on_message(
        rule=fullmatch(msgs, ignorecase) & rule, **kwargs, _depth=_depth + 1
    )


def on_keyword(
    *keywords: str,
    rule: Rule | T_RuleChecker | None = None,
    _depth: int = 0,
    **kwargs,
) -> MatcherCase:
    """注册一个消息事件响应器，并且当消息纯文本部分包含关键词时响应。

    ### 参数
        *keywords: 包含关键词

        rule: 事件响应规则

        permission: 事件响应权限

        handlers: 事件处理函数列表

        temp: 是否为临时事件响应器（仅执行一次）

        expire_time: 事件响应器最终有效时间点，过期即被删除

        priority: 事件响应器优先级

        block: 是否阻止事件向更低优先级传递

        state: 默认会话状态

        to_me: 是否仅响应与自身有关的消息

        reply: 是否仅响应回复消息

        argot: 是否仅响应暗语消息，当 `argot` 为 `True` 时，`priority` 会被强制设置为 `0`
    """
    kwargs.setdefault("block", True)
    return on_message(rule=keyword(*keywords) & rule, **kwargs, _depth=_depth + 1)


def on_regex(
    pattern: str,
    /,
    *,
    flags: int | re.RegexFlag = 0,
    rule: Rule | T_RuleChecker | None = None,
    _depth: int = 0,
    **kwargs,
) -> MatcherCase:
    """注册一个消息事件响应器，并且当消息匹配正则表达式时响应。

    ### 参数
        pattern: 正则表达式

        flags: 正则匹配标志

        rule: 事件响应规则

        permission: 事件响应权限

        handlers: 事件处理函数列表

        temp: 是否为临时事件响应器（仅执行一次）

        expire_time: 事件响应器最终有效时间点，过期即被删除

        priority: 事件响应器优先级

        block: 是否阻止事件向更低优先级传递

        state: 默认会话状态

        to_me: 是否仅响应与自身有关的消息

        reply: 是否仅响应回复消息

        argot: 是否仅响应暗语消息，当 `argot` 为 `True` 时，`priority` 会被强制设置为 `0`
    """
    kwargs.setdefault("block", True)
    return on_message(rule=regex(pattern, flags) & rule, **kwargs, _depth=_depth + 1)


def on_prefix(
    *msgs: str,
    ignorecase: bool = False,
    rule: Rule | T_RuleChecker | None = None,
    _depth: int = 0,
    **kwargs,
) -> MatcherCase:
    """注册一个消息事件响应器，并且当消息的**文本部分**以指定内容开头时响应。

    与普通的 `on_startswith` 不同的是，`on_prefix` 会将前缀从消息中去除。

    ### 参数
        *msgs: 指定消息开头内容

        ignorecase: 是否忽略大小写

        rule: 事件响应规则

        permission: 事件响应权限

        handlers: 事件处理函数列表

        temp: 是否为临时事件响应器（仅执行一次）

        expire_time: 事件响应器最终有效时间点，过期即被删除

        priority: 事件响应器优先级

        block: 是否阻止事件向更低优先级传递

        state: 默认会话状态

        to_me: 是否仅响应与自身有关的消息

        reply: 是否仅响应回复消息

        argot: 是否仅响应暗语消息，当 `argot` 为 `True` 时，`priority` 会被强制设置为 `0`
    """
    kwargs.setdefault("block", True)
    return on_message(rule=prefix(msgs, ignorecase) & rule, **kwargs, _depth=_depth + 1)


def on_suffix(
    *msgs: str,
    ignorecase: bool = False,
    rule: Rule | T_RuleChecker | None = None,
    _depth: int = 0,
    **kwargs,
) -> MatcherCase:
    """注册一个消息事件响应器，并且当消息的**文本部分**以指定内容结尾时响应。

    与普通的 `on_endswith` 不同的是，`on_suffix` 会将后缀从消息中去除。

    ### 参数
        *msgs: 指定消息结尾内容

        ignorecase: 是否忽略大小写

        rule: 事件响应规则

        permission: 事件响应权限

        handlers: 事件处理函数列表

        temp: 是否为临时事件响应器（仅执行一次）

        expire_time: 事件响应器最终有效时间点，过期即被删除

        priority: 事件响应器优先级

        block: 是否阻止事件向更低优先级传递

        state: 默认会话状态

        to_me: 是否仅响应与自身有关的消息

        reply: 是否仅响应回复消息

        argot: 是否仅响应暗语消息，当 `argot` 为 `True` 时，`priority` 会被强制设置为 `0`
    """
    kwargs.setdefault("block", True)
    return on_message(rule=suffix(msgs, ignorecase) & rule, **kwargs, _depth=_depth + 1)


def on_time(
    trigger: Literal["cron", "interval", "date"],
    /,
    *,
    rule: Rule | T_RuleChecker | None = None,
    handlers: list[T_Handler | Dependent] | None = None,
    temp: bool = False,
    expire_time: datetime | timedelta | None = None,
    priority: int = 1,
    block: bool = False,
    state: State | None = None,
    _depth: int = 0,
    **kwargs: Any,
) -> MatcherCase:
    """注册一个通知事件响应器，并且当时间到达指定时间时响应。

    ### 参数
        trigger: 触发器类型，可选值为 `cron`、`interval`、`date`

        rule: 事件响应规则

        handlers: 事件处理函数列表

        temp: 是否为临时事件响应器（仅执行一次）

        expire_time: 事件响应器最终有效时间点，过期即被删除

        priority: 事件响应器优先级

        block: 是否阻止事件向更低优先级传递

        state: 默认会话状态

        **kwargs: 定时触发器参数
    """
    matcher = on_notice(
        rule=rule,
        handlers=handlers,
        temp=temp,
        expire_time=expire_time,
        priority=priority,
        block=block,
        state=state,
        _depth=_depth + 1,
    )

    timer_id = str(hash(matcher))

    matcher.rule &= Rule(TimerRule(timer_id, {"trigger": trigger} | kwargs))  # type: ignore

    async def timer_notice() -> None:
        async def circular(bot: Bot) -> None:
            timer_event = TimerNoticeEvent(
                time=int(time.time()),
                self_id=int(bot.self_id),
                post_type="notice",
                notice_type="timer",
                timer_id=timer_id,
            )
            await handle_event(bot, timer_event)

        tasks = [circular(bot) for bot in get_bots().values()]
        await asyncio.gather(*tasks)

    scheduler.add_job(timer_notice, trigger=trigger, id=timer_id, **kwargs)

    return matcher


class CommandGroup(BaseCommandGroup):
    """命令组，用于声明一组有相同名称前缀的命令。

    ### 参数
        cmd: 指定命令内容

        prefix_aliases: 是否影响命令别名，给命令别名加前缀

        rule: 事件响应规则

        permission: 事件响应权限

        handlers: 事件处理函数列表

        temp: 是否为临时事件响应器（仅执行一次）

        expire_time: 事件响应器最终有效时间点，过期即被删除

        priority: 事件响应器优先级

        block: 是否阻止事件向更低优先级传递

        state: 默认会话状态

        to_me: 是否仅响应与自身有关的消息

        reply: 是否仅响应回复消息

        argot: 是否仅响应暗语消息，当 `argot` 为 `True` 时，`priority` 会被强制设置为 `0`
    """

    if TYPE_CHECKING:
        matchers: list[MatcherCase]

    def __init__(self, cmd: str | tuple[str, ...], **kwargs) -> None:
        super().__init__(cmd, **kwargs)

    def command(self, *cmds: str | tuple[str, ...], **kwargs) -> MatcherCase:
        """注册一个新的命令。

        新参数将会覆盖命令组默认值。

        ### 参数
            *cmds: 指定命令内容

            force_whitespace: 是否强制命令后必须有指定空白符

            rule: 事件响应规则

            permission: 事件响应权限

            handlers: 事件处理函数列表

            temp: 是否为临时事件响应器（仅执行一次）

            expire_time: 事件响应器最终有效时间点，过期即被删除

            priority: 事件响应器优先级

            block: 是否阻止事件向更低优先级传递

            state: 默认会话状态

            to_me: 是否仅响应与自身有关的消息

            reply: 是否仅响应回复消息

            argot: 是否仅响应暗语消息，当 `argot` 为 `True` 时，`priority` 会被强制设置为 `0`
        """
        commands = self.basecmd + cmds
        if self.prefix_aliases and (aliases := kwargs.get("aliases")):
            kwargs["aliases"] = {
                self.basecmd + ((alias,) if isinstance(alias, str) else alias)
                for alias in aliases
            }
        matcher = on_command(*commands, **self._get_final_kwargs(kwargs))
        self.matchers.append(matcher)
        return matcher

    def shell_command(self, *cmds: str | tuple[str, ...], **kwargs) -> MatcherCase:
        """注册一个新的 `shell_like` 命令。新参数将会覆盖命令组默认值。

        ### 参数
            *cmds: 指定命令内容

            parser: `kirami.rule.ArgumentParser` 对象

            rule: 事件响应规则

            permission: 事件响应权限

            handlers: 事件处理函数列表

            temp: 是否为临时事件响应器（仅执行一次）

            expire_time: 事件响应器最终有效时间点，过期即被删除

            priority: 事件响应器优先级

            block: 是否阻止事件向更低优先级传递

            state: 默认会话状态

            to_me: 是否仅响应与自身有关的消息

            reply: 是否仅响应回复消息

            argot: 是否仅响应暗语消息，当 `argot` 为 `True` 时，`priority` 会被强制设置为 `0`
        """
        commands = self.basecmd + cmds
        if self.prefix_aliases and (aliases := kwargs.get("aliases")):
            kwargs["aliases"] = {
                self.basecmd + ((alias,) if isinstance(alias, str) else alias)
                for alias in aliases
            }
        matcher = on_shell_command(*commands, **self._get_final_kwargs(kwargs))
        self.matchers.append(matcher)
        return matcher


class MatcherGroup(BaseMatcherGroup):
    if TYPE_CHECKING:
        matchers: list[MatcherCase]

    def on(self, **kwargs) -> MatcherCase:
        """注册一个基础事件响应器，可自定义类型。

        ### 参数
            type: 事件响应器类型

            rule: 事件响应规则

            permission: 事件响应权限

            handlers: 事件处理函数列表

            temp: 是否为临时事件响应器（仅执行一次）

            expire_time: 事件响应器最终有效时间点，过期即被删除

            priority: 事件响应器优先级

            block: 是否阻止事件向更低优先级传递

            state: 默认会话状态
        """
        matcher = on(**self._get_final_kwargs(kwargs))
        self.matchers.append(matcher)
        return matcher

    def on_type(self, *types: type[Event], **kwargs) -> MatcherCase:
        """注册一个事件响应器，并且当事件为指定类型时响应。

        ### 参数
            *types: 事件类型

            rule: 事件响应规则

            permission: 事件响应权限

            handlers: 事件处理函数列表

            temp: 是否为临时事件响应器（仅执行一次）

            expire_time: 事件响应器最终有效时间点，过期即被删除

            priority: 事件响应器优先级

            block: 是否阻止事件向更低优先级传递

            state: 默认会话状态
        """
        final_kwargs = self._get_final_kwargs(kwargs, exclude={"type"})
        matcher = on_type(*types, **final_kwargs)
        self.matchers.append(matcher)
        return matcher

    def on_metaevent(self, **kwargs) -> MatcherCase:
        """注册一个元事件响应器。

        ### 参数
            rule: 事件响应规则

            handlers: 事件处理函数列表

            temp: 是否为临时事件响应器（仅执行一次）

            expire_time: 事件响应器最终有效时间点，过期即被删除

            priority: 事件响应器优先级

            block: 是否阻止事件向更低优先级传递

            state: 默认会话状态
        """
        final_kwargs = self._get_final_kwargs(kwargs, exclude={"type", "permission"})
        matcher = on_metaevent(**final_kwargs)
        self.matchers.append(matcher)
        return matcher

    def on_message(self, **kwargs) -> MatcherCase:
        """注册一个消息事件响应器。

        ### 参数
            rule: 事件响应规则

            permission: 事件响应权限

            handlers: 事件处理函数列表

            temp: 是否为临时事件响应器（仅执行一次）

            expire_time: 事件响应器最终有效时间点，过期即被删除

            priority: 事件响应器优先级

            block: 是否阻止事件向更低优先级传递

            state: 默认会话状态

            to_me: 是否仅响应与自身有关的消息

            reply: 是否仅响应回复消息

            argot: 是否仅响应暗语消息，当 `argot` 为 `True` 时，`priority` 会被强制设置为 `0`
        """
        final_kwargs = self._get_final_kwargs(kwargs, exclude={"type"})
        matcher = on_message(**final_kwargs)
        self.matchers.append(matcher)
        return matcher

    def on_notice(self, **kwargs) -> MatcherCase:
        """注册一个通知事件响应器。

        ### 参数
            rule: 事件响应规则

            handlers: 事件处理函数列表

            temp: 是否为临时事件响应器（仅执行一次）

            expire_time: 事件响应器最终有效时间点，过期即被删除

            priority: 事件响应器优先级

            block: 是否阻止事件向更低优先级传递

            state: 默认会话状态
        """
        final_kwargs = self._get_final_kwargs(kwargs, exclude={"type", "permission"})
        matcher = on_notice(**final_kwargs)
        self.matchers.append(matcher)
        return matcher

    def on_request(self, **kwargs) -> MatcherCase:
        """注册一个请求事件响应器。

        ### 参数
            rule: 事件响应规则

            handlers: 事件处理函数列表

            temp: 是否为临时事件响应器（仅执行一次）

            expire_time: 事件响应器最终有效时间点，过期即被删除

            priority: 事件响应器优先级

            block: 是否阻止事件向更低优先级传递

            state: 默认会话状态
        """
        final_kwargs = self._get_final_kwargs(kwargs, exclude={"type", "permission"})
        matcher = on_request(**final_kwargs)
        self.matchers.append(matcher)
        return matcher

    def on_command(self, *cmds: str | tuple[str, ...], **kwargs) -> MatcherCase:
        """注册一个消息事件响应器，并且当消息以指定命令开头时响应。

        ### 参数
            *cmds: 指定命令内容

            force_whitespace: 是否强制命令后必须有指定空白符

            rule: 事件响应规则

            permission: 事件响应权限

            handlers: 事件处理函数列表

            temp: 是否为临时事件响应器（仅执行一次）

            expire_time: 事件响应器最终有效时间点，过期即被删除

            priority: 事件响应器优先级

            block: 是否阻止事件向更低优先级传递

            state: 默认会话状态

            to_me: 是否仅响应与自身有关的消息

            reply: 是否仅响应回复消息

            argot: 是否仅响应暗语消息，当 `argot` 为 `True` 时，`priority` 会被强制设置为 `0`
        """
        final_kwargs = self._get_final_kwargs(kwargs, exclude={"type"})
        matcher = on_command(*cmds, **final_kwargs)
        self.matchers.append(matcher)
        return matcher

    def on_shell_command(self, *cmds: str | tuple[str, ...], **kwargs) -> MatcherCase:
        """注册一个支持 `shell_like` 解析参数的命令消息事件响应器。

        与普通的 `on_command` 不同的是，在添加 `parser` 参数时, 响应器会自动处理消息。

        并将用户输入的原始参数列表保存在 `state.shell_argv`, `parser` 处理的参数保存在 `state.shell_args` 中

        ### 参数
            *cmds: 指定命令内容

            parser: `kirami.rule.ArgumentParser` 对象

            rule: 事件响应规则

            permission: 事件响应权限

            handlers: 事件处理函数列表

            temp: 是否为临时事件响应器（仅执行一次）

            expire_time: 事件响应器最终有效时间点，过期即被删除

            priority: 事件响应器优先级

            block: 是否阻止事件向更低优先级传递

            state: 默认会话状态

            to_me: 是否仅响应与自身有关的消息

            reply: 是否仅响应回复消息

            argot: 是否仅响应暗语消息，当 `argot` 为 `True` 时，`priority` 会被强制设置为 `0`
        """
        final_kwargs = self._get_final_kwargs(kwargs, exclude={"type"})
        matcher = on_shell_command(*cmds, **final_kwargs)
        self.matchers.append(matcher)
        return matcher

    def on_startswith(self, *msgs: str, **kwargs) -> MatcherCase:
        """注册一个消息事件响应器，并且当消息的**文本部分**以指定内容开头时响应。

        ### 参数
            *msgs: 指定消息开头内容

            ignorecase: 是否忽略大小写

            rule: 事件响应规则

            permission: 事件响应权限

            handlers: 事件处理函数列表

            temp: 是否为临时事件响应器（仅执行一次）

            expire_time: 事件响应器最终有效时间点，过期即被删除

            priority: 事件响应器优先级

            block: 是否阻止事件向更低优先级传递

            state: 默认会话状态

            to_me: 是否仅响应与自身有关的消息

            reply: 是否仅响应回复消息

            argot: 是否仅响应暗语消息，当 `argot` 为 `True` 时，`priority` 会被强制设置为 `0`
        """
        final_kwargs = self._get_final_kwargs(kwargs, exclude={"type"})
        matcher = on_startswith(*msgs, **final_kwargs)
        self.matchers.append(matcher)
        return matcher

    def on_endswith(self, *msgs: str, **kwargs) -> MatcherCase:
        """注册一个消息事件响应器，并且当消息的**文本部分**以指定内容结尾时响应。

        ### 参数
            *msgs: 指定消息结尾内容

            ignorecase: 是否忽略大小写

            rule: 事件响应规则

            permission: 事件响应权限

            handlers: 事件处理函数列表

            temp: 是否为临时事件响应器（仅执行一次）

            expire_time: 事件响应器最终有效时间点，过期即被删除

            priority: 事件响应器优先级

            block: 是否阻止事件向更低优先级传递

            state: 默认会话状态

            to_me: 是否仅响应与自身有关的消息

            reply: 是否仅响应回复消息

            argot: 是否仅响应暗语消息，当 `argot` 为 `True` 时，`priority` 会被强制设置为 `0`
        """
        final_kwargs = self._get_final_kwargs(kwargs, exclude={"type"})
        matcher = on_endswith(*msgs, **final_kwargs)
        self.matchers.append(matcher)
        return matcher

    def on_fullmatch(self, *msgs: str, **kwargs) -> MatcherCase:
        """注册一个消息事件响应器，并且当消息的**文本部分**与指定内容完全一致时响应。

        ### 参数
            *msgs: 指定消息全匹配内容

            ignorecase: 是否忽略大小写

            rule: 事件响应规则

            permission: 事件响应权限

            handlers: 事件处理函数列表

            temp: 是否为临时事件响应器（仅执行一次）

            expire_time: 事件响应器最终有效时间点，过期即被删除

            priority: 事件响应器优先级

            block: 是否阻止事件向更低优先级传递

            state: 默认会话状态

            to_me: 是否仅响应与自身有关的消息

            reply: 是否仅响应回复消息

            argot: 是否仅响应暗语消息，当 `argot` 为 `True` 时，`priority` 会被强制设置为 `0`
        """
        final_kwargs = self._get_final_kwargs(kwargs, exclude={"type"})
        matcher = on_fullmatch(*msgs, **final_kwargs)
        self.matchers.append(matcher)
        return matcher

    def on_keyword(self, *keywords: str, **kwargs) -> MatcherCase:
        """注册一个消息事件响应器，并且当消息纯文本部分包含关键词时响应。

        ### 参数
            *keywords: 包含关键词

            rule: 事件响应规则

            permission: 事件响应权限

            handlers: 事件处理函数列表

            temp: 是否为临时事件响应器（仅执行一次）

            expire_time: 事件响应器最终有效时间点，过期即被删除

            priority: 事件响应器优先级

            block: 是否阻止事件向更低优先级传递

            state: 默认会话状态

            to_me: 是否仅响应与自身有关的消息

            reply: 是否仅响应回复消息

            argot: 是否仅响应暗语消息，当 `argot` 为 `True` 时，`priority` 会被强制设置为 `0`
        """
        final_kwargs = self._get_final_kwargs(kwargs, exclude={"type"})
        matcher = on_keyword(*keywords, **final_kwargs)
        self.matchers.append(matcher)
        return matcher

    def on_regex(self, pattern: str, /, **kwargs) -> MatcherCase:
        """注册一个消息事件响应器，并且当消息匹配正则表达式时响应。

        ### 参数
            pattern: 正则表达式

            flags: 正则匹配标志

            rule: 事件响应规则

            permission: 事件响应权限

            handlers: 事件处理函数列表

            temp: 是否为临时事件响应器（仅执行一次）

            expire_time: 事件响应器最终有效时间点，过期即被删除

            priority: 事件响应器优先级

            block: 是否阻止事件向更低优先级传递

            state: 默认会话状态

            to_me: 是否仅响应与自身有关的消息

            reply: 是否仅响应回复消息

            argot: 是否仅响应暗语消息，当 `argot` 为 `True` 时，`priority` 会被强制设置为 `0`
        """
        final_kwargs = self._get_final_kwargs(kwargs, exclude={"type"})
        matcher = on_regex(pattern, **final_kwargs)
        self.matchers.append(matcher)
        return matcher

    def on_prefix(self, *msgs: str, **kwargs) -> MatcherCase:
        """注册一个消息事件响应器，并且当消息的**文本部分**以指定内容开头时响应。

        与普通的 `on_startswith` 不同的是，`on_prefix` 会将前缀从消息中去除。

        ### 参数
            *msgs: 指定消息开头内容

            ignorecase: 是否忽略大小写

            rule: 事件响应规则

            permission: 事件响应权限

            handlers: 事件处理函数列表

            temp: 是否为临时事件响应器（仅执行一次）

            expire_time: 事件响应器最终有效时间点，过期即被删除

            priority: 事件响应器优先级

            block: 是否阻止事件向更低优先级传递

            state: 默认会话状态

            to_me: 是否仅响应与自身有关的消息

            reply: 是否仅响应回复消息

            argot: 是否仅响应暗语消息，当 `argot` 为 `True` 时，`priority` 会被强制设置为 `0`
        """
        final_kwargs = self._get_final_kwargs(kwargs, exclude={"type"})
        matcher = on_prefix(*msgs, **final_kwargs)
        self.matchers.append(matcher)
        return matcher

    def on_suffix(self, *msgs: str, **kwargs) -> MatcherCase:
        """注册一个消息事件响应器，并且当消息的**文本部分**以指定内容结尾时响应。

        与普通的 `on_endswith` 不同的是，`on_suffix` 会将后缀从消息中去除。

        ### 参数
            *msgs: 指定消息结尾内容

            ignorecase: 是否忽略大小写

            rule: 事件响应规则

            permission: 事件响应权限

            handlers: 事件处理函数列表

            temp: 是否为临时事件响应器（仅执行一次）

            expire_time: 事件响应器最终有效时间点，过期即被删除

            priority: 事件响应器优先级

            block: 是否阻止事件向更低优先级传递

            state: 默认会话状态

            to_me: 是否仅响应与自身有关的消息

            reply: 是否仅响应回复消息

            argot: 是否仅响应暗语消息，当 `argot` 为 `True` 时，`priority` 会被强制设置为 `0`
        """
        final_kwargs = self._get_final_kwargs(kwargs, exclude={"type"})
        matcher = on_suffix(*msgs, **final_kwargs)
        self.matchers.append(matcher)
        return matcher

    def on_time(
        self, trigger: Literal["cron", "interval", "date"], **kwargs
    ) -> MatcherCase:
        """注册一个通知事件响应器，并且当时间到达指定时间时响应。

        ### 参数
            trigger: 触发器类型，可选值为 `cron`、`interval`、`date`

            rule: 事件响应规则

            handlers: 事件处理函数列表

            temp: 是否为临时事件响应器（仅执行一次）

            expire_time: 事件响应器最终有效时间点，过期即被删除

            priority: 事件响应器优先级

            block: 是否阻止事件向更低优先级传递

            state: 默认会话状态

            **kwargs: 定时触发器参数
        """
        final_kwargs = self._get_final_kwargs(kwargs, exclude={"type"})
        matcher = on_time(trigger, **final_kwargs)
        self.matchers.append(matcher)
        return matcher
