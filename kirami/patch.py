"""本模块用于修改 NoneBot 以满足定制需求"""

# ruff: noqa: F811, PLR0913

# ==============================================================================

import inspect
from types import ModuleType
from typing import Any

from nonebot.dependencies import CustomConfig, Param
from nonebot.dependencies.utils import check_field_type
from nonebot.internal.params import StateParam
from nonebot.log import logger
from nonebot.plugin import _current_plugin_chain
from nonebot.plugin.model import Plugin
from nonebot.typing import T_State
from nonebot.utils import generic_check_issubclass
from pydantic.fields import ModelField, Required

from kirami.typing import State


@classmethod
def check_param(
    cls: type[StateParam],
    param: inspect.Parameter,
    _allow_types: tuple[type[Param], ...],
) -> StateParam | None:
    """允许自定义类型 `State` 通过依赖注入检查"""
    # param type is T_State
    if param.annotation is T_State:
        return cls(Required)
    # param type is State or subclass of State or None
    if generic_check_issubclass(param.annotation, State):
        checker: ModelField | None = None
        if param.annotation is not State:
            checker = ModelField(
                name=param.name,
                type_=param.annotation,
                class_validators=None,
                model_config=CustomConfig,
                default=None,
                required=True,
            )
        return cls(Required, checker=checker)
    # legacy: param is named "state" and has no type annotation
    if param.annotation == param.empty and param.name == "state":
        return cls(Required)
    return None


async def check(self: StateParam, state: State, **_kwargs: Any) -> Any:
    if checker := self.extra.get("checker", None):
        check_field_type(checker, state)


StateParam._check_param = check_param  # type: ignore
StateParam._check = check

# ==============================================================================

import importlib
import time

from nonebot.log import logger
from nonebot.plugin.manager import PluginManager
from nonebot.plugin.model import Plugin
from nonebot.utils import path_to_module_name


def load_plugin(self: PluginManager, name: str) -> Plugin | None:
    """在 NoneBot 加载插件后进行服务化处理"""
    try:
        start_time = time.time()

        if name in self.plugins:
            module = importlib.import_module(name)
        elif name in self._third_party_plugin_names:
            module = importlib.import_module(self._third_party_plugin_names[name])
        elif name in self._searched_plugin_names:
            module = importlib.import_module(
                path_to_module_name(self._searched_plugin_names[name])
            )
        else:
            raise RuntimeError(  # noqa: TRY301
                f"Plugin not found: {name}! Check your plugin name"
            )

        if (plugin := getattr(module, "__plugin__", None)) is None or not isinstance(
            plugin, Plugin
        ):
            raise RuntimeError(  # noqa: TRY301
                f"Module {module.__name__} is not loaded as a plugin! "
                "Make sure not to import it before loading."
            )
        full_name = getattr(plugin, "full_name")
        logger.opt(colors=True).success(f'✨ Loading "<y>{full_name}</y>" complete.')

        end_time = time.time()
        load_time = (end_time - start_time) * 1000
        logger.opt(colors=True).debug(
            f'💠 Service "<y>{full_name}</y>" ready. Load time: {load_time:.2f} ms.'
        )
    except Exception as e:
        logger.opt(colors=True, exception=e).error(
            f'🌠 Loading "<r>{name}</r>" failed: <r>{e}</r>'
        )
    else:
        return plugin


PluginManager.load_plugin = load_plugin

# ==============================================================================

from nonebot.plugin.model import Plugin


@property
def full_name(self: Plugin) -> str:
    """插件完整索引标识，包含所有父插件的标识符"""
    if parent := self.parent_plugin:
        return getattr(parent, "full_name") + "." + self.name
    return self.name


setattr(Plugin, "full_name", full_name)

# ==============================================================================

from importlib.machinery import SourceFileLoader
from types import ModuleType

from nonebot.plugin import _current_plugin_chain, _managers, _new_plugin, _revert_plugin
from nonebot.plugin.manager import PluginLoader
from nonebot.plugin.model import PluginMetadata

from kirami.service.manager import ServiceManager, load_subplugin


def exec_module(self: PluginLoader, module: ModuleType) -> None:
    """支持从配置中加载子插件"""
    if self.loaded:
        return

    # create plugin before executing
    plugin = _new_plugin(self.name, module, self.manager)
    setattr(module, "__plugin__", plugin)

    # detect parent plugin before entering current plugin context
    parent_plugins = _current_plugin_chain.get()
    for pre_plugin in reversed(parent_plugins):
        if _managers.index(pre_plugin.manager) < _managers.index(self.manager):
            plugin.parent_plugin = pre_plugin
            pre_plugin.sub_plugins.add(plugin)
            break

    # enter plugin context
    _plugin_token = _current_plugin_chain.set((*parent_plugins, plugin))

    try:
        try:
            super(SourceFileLoader, self).exec_module(module)
        except Exception:
            _revert_plugin(plugin)
            raise

        # Move: get plugin metadata
        metadata: PluginMetadata | None = getattr(module, "__plugin_meta__", None)
        plugin.metadata = metadata

        # Add: create service
        ServiceManager.load_service(plugin)

        # Add: load subplugin
        load_subplugin(plugin)
    finally:
        # leave plugin context
        _current_plugin_chain.reset(_plugin_token)


PluginLoader.exec_module = exec_module

# ==============================================================================

from nonebot.internal.adapter.event import Event


def get_plaintext(self: Event) -> str:
    """去除纯文本首尾空白字符"""
    return self.get_message().extract_plain_text().strip()


Event.get_plaintext = get_plaintext

# ==============================================================================

from nonebot.internal.params import ArgParam

from kirami.matcher import Matcher


async def _solve(self: ArgParam, matcher: Matcher, **_kwargs: Any) -> Any:
    """支持 State、Argot 内容提取"""
    key: str = self.extra["key"]
    if self.extra["type"] == "state":
        return matcher.state.get(key)
    if self.extra["type"] == "argot":
        return matcher.get_argot(key)
    message = matcher.get_arg(key)
    if message is None:
        return message
    if self.extra["type"] == "message":
        return message
    if self.extra["type"] == "str":
        return str(message)
    return message.extract_plain_text()


ArgParam._solve = _solve  # type: ignore
