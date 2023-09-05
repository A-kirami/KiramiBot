"""本模块定义了插件服务化逻辑与流程"""

import asyncio
import contextlib
import inspect
import locale
from collections.abc import Generator
from dataclasses import asdict
from pathlib import Path
from typing import Any, overload

import nonebot
from bidict import bidict
from nonebot.matcher import Matcher
from nonebot.plugin import Plugin

from kirami.exception import ServiceError
from kirami.hook import on_startup
from kirami.log import logger
from kirami.matcher import MatcherCase
from kirami.utils import load_data

from .service import Ability, Service


@on_startup
async def init_service() -> None:
    order_service = sorted(
        Service.sp_map.items(), key=lambda item: _sort_by_position(item[0])
    )
    Service.sp_map = bidict(order_service)
    tasks = [service.init() for service in ServiceManager.get_services()]
    await asyncio.gather(*tasks)


def load_subplugin(parent_plugin: Plugin) -> None:
    """加载子服务。

    ### 参数
        parent_plugin: 父插件
    """
    service = ServiceManager.get_correspond(parent_plugin)
    if not (plugin_file := parent_plugin.module.__file__):
        return
    parent_path = Path(plugin_file).parent
    if subplugins := service.extra.get("subplugins"):
        if isinstance(subplugins, str):
            subplugins = [subplugins]
        for subplugin in subplugins:
            nonebot.load_plugin(parent_path / subplugin)
    if subplugin_dirs := service.extra.get("subplugin_dirs"):
        if isinstance(subplugin_dirs, str):
            subplugin_dirs = [subplugin_dirs]
        nonebot.load_plugins(
            *(str((parent_path / spd).resolve()) for spd in subplugin_dirs)
        )


def _from_metadata(plugin: Plugin) -> dict[str, Any]:
    """从 `module.__plugin_meta__` 中获取服务配置。

    ### 参数
        plugin: 插件对象
    """
    metadata = plugin.metadata
    config = asdict(metadata) if metadata else {}
    config |= config.get("extra", {})
    config.setdefault("name", getattr(plugin, "full_name"))
    config.setdefault("author", "unknown")
    return config


def _from_file(plugin: Plugin) -> dict[str, Any]:
    """从 `service.toml` 中获取服务配置。

    ### 参数
        plugin: 插件对象
    """
    file_path = Path(plugin.module.__path__[0]) / "service.toml"
    return load_data(file_path)["plugin"]


def _sort_by_position(item: Service | Ability) -> tuple[int | float, str]:
    """对服务或功能进行排序。

    ### 参数
        item: 服务或功能对象
    """
    locale.setlocale(locale.LC_ALL, "")
    position = item.position if item.position is not None else float("inf")
    name_key = locale.strxfrm(item.name)
    return (position, name_key)


class ServiceManager:
    @overload
    @classmethod
    def get_correspond(cls, item: Plugin) -> Service:
        ...

    @overload
    @classmethod
    def get_correspond(cls, item: Service) -> Plugin:
        ...

    @overload
    @classmethod
    def get_correspond(cls, item: type[Matcher]) -> Ability:
        ...

    @overload
    @classmethod
    def get_correspond(cls, item: Ability) -> type[Matcher]:
        ...

    @classmethod
    def get_correspond(
        cls, item: Plugin | Service | type[Matcher] | Ability
    ) -> Plugin | Service | type[Matcher] | Ability:
        """获取对应的映射对象。

        ### 参数
            item: 插件、服务、功能或事件响应器
        """
        if isinstance(item, Plugin):
            return Service.got(item)
        if isinstance(item, Service):
            return item.plugin
        if inspect.isclass(item) and issubclass(item, Matcher):
            return Ability.got(item)
        if isinstance(item, Ability):
            return item.matcher
        raise TypeError(f"Unsupported type: {type(item)}")

    @classmethod
    def load_service(cls, plugin: Plugin) -> Service:
        """加载服务。

        ### 参数
            plugin: 插件对象

        ### 返回
            服务对象
        """
        config = _from_metadata(plugin)
        try:
            with contextlib.suppress(AttributeError, FileNotFoundError):
                config |= _from_file(plugin)
        except Exception as e:
            logger.opt(colors=True, exception=e).error(
                f"Loading \"{getattr(plugin, 'full_name')}\" configuration failed! Use default configuration."
            )
        config["id"] = f"{config['author']}.{getattr(plugin, 'full_name')}"
        service = Service(**config)
        service.bind(plugin)
        cls.load_abilities(service)
        return service

    @classmethod
    def load_abilities(cls, service: Service) -> list[Ability]:
        """加载功能。

        ### 参数
            service: 服务对象

        ### 返回
            功能列表
        """
        matchers = cls.get_correspond(service).matcher
        configs = {
            i["name"]: i for i in service.default.get("matchers", []) if "name" in i
        }
        abilities = {}
        for matcher in matchers:
            if members := inspect.getmembers(
                matcher.module,
                lambda x, m=matcher: x.matcher is m
                if isinstance(x, MatcherCase)
                else x is m,
            ):
                name, _ = members[0]
            else:
                try:
                    name = matcher.handlers[0].call.__name__
                except IndexError:
                    continue
            if name in abilities:
                raise ServiceError(
                    f"Ability name conflict! Duplicate with existing matcher name: {name}"
                )
            ability = Ability(
                id=f"{service.id}#{name}", **configs.get(name, {"name": name})  # type: ignore
            )
            ability.bind(matcher)
            abilities[name] = ability
        service._abilities = sorted(abilities.values(), key=_sort_by_position)
        return service._abilities

    @classmethod
    def get_service(cls, key: str | Plugin | Matcher | Ability) -> Service:
        """获取服务。

        ### 参数
            key: 服务名或对应的插件、功能或事件响应器对象
        """
        if isinstance(key, Plugin):
            plugin = key
        elif isinstance(key, Matcher):
            plugin = key.plugin
        elif isinstance(key, Ability):
            plugin = cls.get_correspond(key).plugin
        elif not (plugin := nonebot.get_plugin(key)):
            for service in cls.get_services():
                if key in {service.name} | service.alias:
                    plugin = cls.get_correspond(service)
                    break

        if not plugin:
            raise ServiceError("查找的服务不存在")

        return cls.get_correspond(plugin)

    @classmethod
    def get_services(cls, tag: str | None = None) -> Generator[Service, None, None]:
        """获取所有服务。

        ### 参数
            tag: 分类标签，为空则获取所有服务

        ### 生成
            服务对象
        """
        for service in Service.sp_map:
            if tag and tag in service.tags or not tag:
                yield service

    @classmethod
    def get_ability(cls, source: Service | Plugin, index: int) -> Ability:
        """获取功能。

        ### 参数
            source: 服务或插件对象

            index: 功能索引
        """
        if isinstance(source, Plugin):
            source = cls.get_correspond(source)
        return source.abilities[index - 1]

    @classmethod
    def get_abilities(cls, source: Service | Plugin) -> Generator[Ability, None, None]:
        """获取所有功能。

        ### 参数
            source: 服务或插件对象

        ### 生成
            功能对象
        """
        if isinstance(source, Plugin):
            source = cls.get_correspond(source)
        yield from source.abilities
