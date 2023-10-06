"""本模块主要定义了 KiramiBot 启动所需类和函数，供 bot 入口文件调用

## 快捷导入

为方便使用，本模块从子模块导入了部分内容，以下内容可以直接通过本模块导入:

- `on`
- `on_type`
- `on_metaevent`
- `on_message`
- `on_notice`
- `on_request`
- `on_command`
- `on_shell_command`
- `on_startswith`
- `on_endswith`
- `on_fullmatch`
- `on_keyword`
- `on_regex`
- `on_prefix`
- `on_suffix`
- `on_time`
- `CommandGroup`
- `Matchergroup`
"""

from kirami import patch  # isort:skip  # noqa: F401

import importlib
from pathlib import Path
from typing import Any, ClassVar, Literal, TypeVar, overload

import nonebot
from nonebot.adapters import Adapter, Bot
from nonebot.drivers import ASGIMixin, Driver
from nonebot.plugin.manager import PluginManager, _managers
from nonebot.plugin.model import Plugin
from nonebot.utils import path_to_module_name

from kirami import hook
from kirami.config import bot_config, kirami_config, plugin_config
from kirami.log import Columns, Panel, Text, console
from kirami.log import logger as logger
from kirami.server import Server
from kirami.version import __metadata__ as __metadata__
from kirami.version import __version__ as __version__

A = TypeVar("A", bound=Adapter)


def get_driver() -> Driver:
    """获取全局`Driver` 实例。

    ### 异常
        ValueError: 全局 `nonebot.drivers.Driver` 对象尚未初始化（`kirami.KiramiBot` 尚未实例化）
    """
    if KiramiBot.driver is None:
        raise ValueError("KiramiBot has not been initialized.")
    return KiramiBot.driver


@overload
def get_adapter(name: str) -> Adapter:
    """
    ### 参数
        name: 适配器名称

    ### 返回
        指定名称的 `nonebot.adapters.Adapter` 对象
    """


@overload
def get_adapter(name: type[A]) -> A:
    """
    ### 参数
        name: 适配器类型

    ### 返回
        指定类型的 `nonebot.adapters.Adapter` 对象
    """


def get_adapter(name: str | type[Adapter]) -> Adapter:
    """获取已注册的 `nonebot.adapters.Adapter` 实例。

    ### 异常
        ValueError: 指定的 `nonebot.adapters.Adapter` 未注册

        ValueError: 全局 `nonebot.drivers.Driver` 对象尚未初始化
            （`kirami.KiramiBot` 尚未实例化）
    """
    adapters = get_adapters()
    target = name if isinstance(name, str) else name.get_name()
    if target not in adapters:
        raise ValueError(f"Adapter {target} not registered.")
    return adapters[target]


def get_adapters() -> dict[str, Adapter]:
    """获取所有已注册的 `nonebot.adapters.Adapter` 实例。

    ### 返回
        所有 `nonebot.adapters.Adapter` 实例字典

    ### 异常
        ValueError: 全局 `nonebot.drivers.Driver` 对象尚未初始化
            （`kirami.KiramiBot` 尚未实例化）
    """
    return get_driver()._adapters.copy()


def get_app() -> Any:
    """获取全局 `nonebot.drivers.ASGIMixin` 对应的 Server App 对象。

    ### 异常
        AssertionError: 全局 Driver 对象不是 `nonebot.drivers.ASGIMixin` 类型

        ValueError: 全局 `nonebot.drivers.Driver` 对象尚未初始化（`kirami.KiramiBot` 尚未实例化）
    """
    driver = get_driver()
    if not isinstance(driver, ASGIMixin):
        raise TypeError("app object is only available for asgi driver")
    return driver.server_app


def get_asgi() -> Any:
    """获取全局 `nonebot.drivers.ASGIMixin` 对应的 [ASGI](https://asgi.readthedocs.io/) 对象。

    ### 异常
        AssertionError: 全局 Driver 对象不是 `nonebot.drivers.ASGIMixin` 类型

        ValueError: 全局 `nonebot.drivers.Driver` 对象尚未初始化（`kirami.KiramiBot` 尚未实例化）
    """
    driver = get_driver()
    if not isinstance(driver, ASGIMixin):
        raise TypeError("asgi object is only available for asgi driver")
    return driver.asgi


@overload
def get_bot(self_id: str | None = None, raise_error: Literal[True] = True) -> Bot:
    ...


@overload
def get_bot(
    self_id: str | None = None, raise_error: Literal[False] = False
) -> Bot | None:
    ...


def get_bot(self_id: str | None = None, raise_error: bool = True) -> Bot | None:
    """获取一个连接到 KiramiBot 的 `Bot` 对象。

    当提供 `self_id` 时，此函数是 `get_bots()[self_id]` 的简写；
    当不提供时，返回一个 `nonebot.adapters.Bot`。

    ### 参数
        self_id: 用来识别 `nonebot.adapters.Bot` 的 `nonebot.adapters.Bot.self_id` 属性

        raise_error: 当找不到对应 `self_id` 的 `nonebot.adapters.Bot` 时是否抛出异常

    ### 异常
        KeyError: 对应 `self_id` 的 `Bot` 不存在

        ValueError: 没有传入 `self_id` 且没有 `Bot` 可用

        ValueError: 全局 `nonebot.drivers.Driver` 对象尚未初始化（`kirami.KiramiBot` 尚未实例化）
    """
    bots = get_bots()
    if self_id is not None:
        return bots[self_id] if raise_error else bots.get(self_id)

    for bot in bots.values():
        return bot

    if raise_error:
        raise ValueError("There are no bots to get.")
    return None


def get_bots() -> dict[str, Bot]:
    """获取所有连接到 KiramiBot 的 `nonebot.adapters.Bot` 对象。

    ### 返回
        一个以 `nonebot.adapters.Bot.self_id` 为键，`nonebot.adapters.Bot` 对象为值的字典

    ### 异常
        ValueError: 全局 `nonebot.drivers.Driver` 对象尚未初始化（`kirami.KiramiBot` 尚未实例化）
    """
    return get_driver().bots


class KiramiBot:
    driver: ClassVar[Driver]

    def __init__(self) -> None:
        self.show_logo()

        if bot_config.debug:
            self.print_environment()
            console.rule()

        self.init_nonebot(_mixin_config(bot_config.dict()))

        logger.success("🌟 KiramiBot is initializing...")
        logger.opt(colors=True).debug(
            f"Loaded <y><b>Config</b></y>: {kirami_config.dict()}"
        )

        self.load_plugins()

        Server.init()
        hook.install_hook()

        logger.opt(colors=True).success("🌟 <y><b>KiramiBot is Running...</b></y>")

        if bot_config.debug:
            console.rule("[blink][yellow]当前处于调试模式中, 请勿在生产环境打开[/][/]")

    def run(self, *args, **kwargs) -> None:
        """启动 KiramiBot"""
        self.driver.run(*args, **kwargs)

    def init_nonebot(self, config: dict[str, Any]) -> None:
        """初始化 NoneNot"""
        nonebot.init(**config)

        self.__class__.driver = nonebot.get_driver()
        self.load_adapters(config["adapters"])

    def load_adapters(self, adapters: set[str]) -> None:
        """加载适配器"""
        adapters = {adapter.replace("~", "nonebot.adapters.") for adapter in adapters}
        for adapter in adapters:
            module = importlib.import_module(adapter)
            self.driver.register_adapter(getattr(module, "Adapter"))

    def load_plugins(self) -> None:
        """加载插件"""
        plugins = {
            path_to_module_name(pp) if (pp := Path(p)).exists() else p
            for p in plugin_config.plugins
        }
        manager = PluginManager(plugins, plugin_config.plugin_dirs)
        plugins = manager.available_plugins
        _managers.append(manager)

        if plugin_config.whitelist:
            plugins &= plugin_config.whitelist

        if plugin_config.blacklist:
            plugins -= plugin_config.blacklist

        loaded_plugins = set(
            filter(None, (manager.load_plugin(name) for name in plugins))
        )

        self.loading_state(loaded_plugins)

    def loading_state(self, plugins: set[Plugin]) -> None:
        """打印插件加载状态"""
        if loaded_plugins := nonebot.get_loaded_plugins():
            logger.opt(colors=True).info(
                f"🌟 [magenta]Total {len(loaded_plugins)} plugin are successfully loaded.[/]"
            )

        if failed_plugins := plugins - loaded_plugins:
            logger.opt(colors=True).error(
                f"🌠 [magenta]Total {len(failed_plugins)} plugin are failed loaded.[/]: {', '.join(plugin.name for plugin in failed_plugins)}"
            )

    def show_logo(self) -> None:
        """打印 LOGO"""
        console.print(
            Columns(
                [Text(LOGO.lstrip("\n"), style="bold blue")],
                align="center",
                expand=True,
            )
        )

    def print_environment(self) -> None:
        """打印环境信息"""
        import platform

        environment_info = {
            "OS": platform.system(),
            "Arch": platform.machine(),
            "Python": platform.python_version(),
            "KiramiBot": __version__,
            "NoneBot": nonebot.__version__,
        }

        renderables = [
            Panel(
                Text(justify="center")
                .append(k, style="bold")
                .append(f"\n{v}", style="yellow"),
                expand=True,
                width=console.size.width // 6,
            )
            for k, v in environment_info.items()
        ]
        console.print(
            Columns(
                renderables,
                align="center",
                title="Environment Info",
                expand=True,
                equal=True,
            )
        )


def _mixin_config(config: dict[str, Any]) -> dict[str, Any]:
    if config["debug"]:
        config |= {
            "fastapi_openapi_url": config.get("fastapi_openapi_url", "/openapi.json"),
            "fastapi_docs_url": config.get("fastapi_docs_url", "/docs"),
            "fastapi_redoc_url": config.get("fastapi_redoc_url", "/redoc"),
        }
    config["fastapi_extra"] = {
        "title": __metadata__.name,
        "version": __metadata__.version,
        "description": __metadata__.summary,
    }

    return config


LOGO = r"""
 _    _  _                      _  ______
| |  / )(_)                    (_)(____  \         _
| | / /  _   ____  ____  ____   _  ____)  )  ___  | |_
| |< <  | | / ___)/ _  ||    \ | ||  __  (  / _ \ |  _)
| | \ \ | || |   ( ( | || | | || || |__)  )| |_| || |__
|_|  \_)|_||_|    \_||_||_|_|_||_||______/  \___/  \___)
"""

from kirami.matcher import CommandGroup as CommandGroup
from kirami.matcher import MatcherGroup as MatcherGroup
from kirami.matcher import on_command as on_command
from kirami.matcher import on_endswith as on_endswith
from kirami.matcher import on_fullmatch as on_fullmatch
from kirami.matcher import on_keyword as on_keyword
from kirami.matcher import on_message as on_message
from kirami.matcher import on_metaevent as on_metaevent
from kirami.matcher import on_notice as on_notice
from kirami.matcher import on_prefix as on_prefix
from kirami.matcher import on_regex as on_regex
from kirami.matcher import on_request as on_request
from kirami.matcher import on_shell_command as on_shell_command
from kirami.matcher import on_startswith as on_startswith
from kirami.matcher import on_suffix as on_suffix
from kirami.matcher import on_time as on_time
from kirami.matcher import on_type as on_type
