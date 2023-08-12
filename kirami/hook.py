"""本模块提供了生命周期钩子，用于在特定时机执行函数"""

from collections import defaultdict
from collections.abc import Callable
from functools import wraps
from typing import Any, ParamSpec, TypeVar, cast

from nonebot import get_driver
from nonebot.adapters import Bot
from nonebot.message import (
    event_postprocessor,
    event_preprocessor,
    run_postprocessor,
    run_preprocessor,
)
from nonebot.typing import (
    T_BotConnectionHook,
    T_BotDisconnectionHook,
    T_CalledAPIHook,
    T_CallingAPIHook,
    T_EventPostProcessor,
    T_EventPreProcessor,
    T_RunPostProcessor,
    T_RunPreProcessor,
)

R = TypeVar("R")

P = ParamSpec("P")

AnyCallable = Callable[..., Any]

_backlog_hooks = defaultdict(list)

_hook_installed = False


def backlog_hook(hook: Callable[P, R]) -> Callable[P, R]:
    """在初始化之前暂存钩子"""

    @wraps(hook)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        if _hook_installed:
            return hook(*args, **kwargs)
        try:
            _backlog_hooks[hook].append(args[0])
            return cast(R, args[0])
        except IndexError:
            return hook(*args, **kwargs)

    return wrapper


def install_hook() -> None:
    """将暂存的钩子安装"""
    for hook, funcs in _backlog_hooks.items():
        while funcs:
            func = funcs.pop(0)
            hook(func)
    global _hook_installed  # noqa: PLW0603
    _hook_installed = True


@backlog_hook
def on_startup(func: AnyCallable | None = None, pre: bool = False) -> AnyCallable:
    """在 `KramiBot` 启动时有序执行"""
    if func is None:
        return lambda f: on_startup(f, pre=pre)
    if pre:
        _backlog_hooks[on_startup.__wrapped__].insert(0, func)
        return func
    return get_driver().on_startup(func)


@backlog_hook
def on_shutdown(func: AnyCallable) -> AnyCallable:
    """在 `KramiBot` 停止时有序执行"""
    return get_driver().on_shutdown(func)


@backlog_hook
def on_connect(func: T_BotConnectionHook) -> T_BotConnectionHook:
    """在 bot 成功连接到 `KramiBot` 时执行。

    钩子函数参数:

    - bot: (依赖注入) 当前连接上的 Bot 对象
    """
    return get_driver().on_bot_connect(func)


@backlog_hook
def on_disconnect(func: T_BotDisconnectionHook) -> T_BotDisconnectionHook:
    """在 bot 与 `KramiBot` 连接断开时执行。

    钩子函数参数:

    - bot: (依赖注入) 当前连接上的 Bot 对象
    """
    return get_driver().on_bot_disconnect(func)


def before_api(func: T_CallingAPIHook) -> T_CallingAPIHook:
    """在调用 API 之前执行。

    钩子函数参数:

    - bot: 当前 bot 对象
    - api: 调用的 api 名称
    - data: api 调用的参数字典
    """
    return Bot.on_calling_api(func)


def after_api(func: T_CalledAPIHook) -> T_CalledAPIHook:
    """在调用 API 之后执行。

    钩子函数参数:

    - bot: 当前 bot 对象
    - exception: 调用 api 时发生的错误
    - api: 调用的 api 名称
    - data: api 调用的参数字典
    - result: api 调用的返回
    """
    return Bot.on_called_api(func)


def before_event(func: T_EventPreProcessor) -> T_EventPreProcessor:
    """在分发事件之前执行。

    钩子函数参数:

    - bot: (依赖注入) 当前连接上的 Bot 对象
    - event: (依赖注入) 事件对象
    - state: (依赖注入) 会话状态
    """
    return event_preprocessor(func)


def after_event(func: T_EventPostProcessor) -> T_EventPostProcessor:
    """在分发事件之后执行。

    钩子函数参数:

    - bot: (依赖注入) 当前连接上的 Bot 对象
    - event: (依赖注入) 事件对象
    - state: (依赖注入) 会话状态
    """
    return event_postprocessor(func)


def before_run(func: T_RunPreProcessor) -> T_RunPreProcessor:
    """在事件响应器运行之前执行。

    钩子函数参数:

    - bot: (依赖注入) 当前连接上的 Bot 对象
    - event: (依赖注入) 事件对象
    - matcher: (依赖注入) 匹配到的事件响应器
    - state: (依赖注入) 会话状态
    """
    return run_preprocessor(func)


def after_run(func: T_RunPostProcessor) -> T_RunPostProcessor:
    """在事件响应器运行之后执行。

    钩子函数参数:

    - bot: (依赖注入) 当前连接上的 Bot 对象
    - event: (依赖注入) 事件对象
    - matcher: (依赖注入) 匹配到的事件响应器
    - state: (依赖注入) 会话状态
    - exception: (依赖注入) 事件响应器运行中产生的异常
    """
    return run_postprocessor(func)
