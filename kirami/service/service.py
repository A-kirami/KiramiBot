"""本模块定义了服务与功能配置"""

import asyncio
from enum import IntEnum, auto
from typing import Any, ClassVar, Literal

from bidict import bidict
from mango import Document, Field
from nonebot.matcher import Matcher
from nonebot.plugin import Plugin
from pydantic import BaseModel, PrivateAttr, validator
from pydantic.fields import ModelField
from typing_extensions import Self

from .limiter import LimitScope
from .subject import Subject


class State(IntEnum):
    """运行状态枚举"""

    NORMAL = auto()
    """正常，所有人都可使用"""
    SHUTDOWN = auto()
    """停用，所有人都无法使用，可能是因为滥用或无法修复的问题"""
    MAINT = auto()
    """维护，所有人都无法使用，可能是需要维护或正在修复问题"""
    DEVELOP = auto()
    """开发，仅超级管理员或测试用户可以使用"""
    EXCEPTION = auto()
    """异常，表示可能会出现问题，但是不影响使用"""
    FAULT = auto()
    """故障，表示已经无法正常使用，需要修复"""


class RoleConfig(BaseModel):
    user: str = "normal"
    manager: str = "admin"


class LimitConfig(BaseModel):
    type: LimitScope = LimitScope.LOCAL
    """默认为局部限制"""
    prompt: str | None = None
    """限制状态提示"""


class CooldownConfig(LimitConfig):
    time: int
    """冷却时间，单位为秒"""


class QuotaConfig(LimitConfig):
    limit: int
    """配置数量"""
    reset: int | str = 0
    """重置时间"""


LIMIT_KEY = {CooldownConfig: "time", QuotaConfig: "limit"}


class MixinConfig(Document):
    enabled: bool = True
    """默认启用状态"""

    position: int | None = None
    """帮助列表中排序位置"""

    visible: bool = True
    """是否在帮助菜单可见"""

    role: RoleConfig = Field(default_factory=RoleConfig)
    """
    角色权限。

    可选范围:
    - `user`: 使用所需最低权限角色，默认为成员权限
    - `manager`: 管理所需最低权限角色，默认为管理员权限
    """

    scope: Literal["group", "private", "all"] = "all"
    """
    消息作用域，决定事件的响应范围。

    可选范围:
    - `group`: 只响应群聊消息
    - `private`: 只响应私聊消息
    - `all`: 响应私聊和群聊消息
    """

    cooldown: CooldownConfig | None = None
    """
    每次使用后的冷却时间，不指定范围则默认为`局部冷却时间`。

    可选范围:
    - `global`: 全局冷却时间，所有群组和用户的公共冷却时间
    - `local`: 局部冷却时间，群组内的单个成员的独有冷却时间
    - `group`: 群组冷却时间，群组内所有成员的公共冷却时间
    - `user`: 用户冷却时间，单个用户的独有冷却时间
    """

    quota: QuotaConfig | None = None
    """
    每日可使用的次数，不指定范围则默认为`局部可用次数`。

    可选范围:
    - `global`: 全局可用次数，所有群组和用户的公共可用次数
    - `local`: 局部可用次数，群组内的单个成员的独有可用次数
    - `group`: 群组可用次数，群组内所有成员的公共可用次数
    - `user`: 用户可用次数，单个用户的独有可用次数
    """

    state: State = State.NORMAL
    """运行状态"""

    status: dict[Subject, bool] = Field(default_factory=dict)
    """主体状态列表"""

    @validator("cooldown", "quota", pre=True)
    def validate_limiter(
        cls, value: int | dict[str, Any] | None, field: ModelField
    ) -> Any:
        if value is None:
            return None
        if isinstance(value, int):
            return field.type_(**{LIMIT_KEY[field.type_]: value})
        return field.type_(**value)

    async def enable(self, subject: Subject) -> None:
        """启用服务或功能。

        ### 参数
            subject: 主体
        """
        self.status[subject] = True
        await self.save()

    async def disable(self, subject: Subject) -> None:
        """禁用服务或功能。

        ### 参数
            subject: 主体
        """
        self.status[subject] = False
        await self.save()

    def check_enabled(self, *subjects: Subject) -> bool:
        """检查服务或功能是否启用。

        ### 参数
            *subjects: 主体
        """
        return all(self.status.get(subject, self.enabled) for subject in subjects)

    def get_enabled_subjects(self, *subjects: Subject) -> set[Subject]:
        """获取启用的主体列表。

        ### 参数
            *subjects: 主体

        ### 返回
            启用的主体集合
        """
        return {
            subject for subject in subjects if self.status.get(subject, self.enabled)
        }

    def get_disabled_subjects(self, *subjects: Subject) -> set[Subject]:
        """获取禁用的主体列表。

        ### 参数
            *subjects: 主体

        ### 返回
            禁用的主体集合
        """
        return set(subjects) - self.get_enabled_subjects(*subjects)


class BaseConfig(Document):
    default: dict[str, Any] = Field(default_factory=dict)
    """默认配置"""

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        default = data.pop("default", {})
        if not default:
            self.default = data

    def __hash__(self) -> int:
        return hash(self.id)

    async def sync(self) -> None:
        """从数据库中同步配置"""
        if not (config := await self.get(self.id)):
            return

        await self.update(**config.dict(exclude={"id", "version", "author", "default"}))

    class Meta:
        by_alias = True


class Ability(BaseConfig, MixinConfig):
    """功能配置"""

    id: str = Field(primary_key=True)
    """唯一标识符，由插件标识符+功能名构成（eg. akirami.hello-world#hello）"""
    name: str = ""
    """功能名称"""
    command: str = ""
    """命令/指令示例"""
    description: str = ""
    """指令效果说明"""
    exception: int = 0
    """异常发生次数"""

    am_map: ClassVar[bidict[Self, type[Matcher]]] = bidict()
    """Matcher - Ability 映射表"""

    @property
    def matcher(self) -> type[Matcher]:
        """事件响应器"""
        return self.am_map[self]

    @property
    def service(self) -> "Service":
        """所属服务"""
        if plugin := self.matcher.plugin:
            return Service.got(plugin)
        raise ValueError("未找到对应的服务")

    @property
    def index(self) -> int:
        """功能序号"""
        return self.service.abilities.index(self) + 1

    def bind(self, matcher: type[Matcher]) -> None:
        """绑定事件响应器。

        ### 参数
            matcher: 事件响应器
        """
        self.am_map[self] = matcher

    @classmethod
    def got(cls, matcher: type[Matcher] | Matcher) -> Self:
        """获取对应的功能。

        ### 参数
            matcher: 事件响应器
        """
        if isinstance(matcher, Matcher):
            return cls.am_map.inverse[matcher.__class__]
        return cls.am_map.inverse[matcher]


class Service(BaseConfig, MixinConfig):
    """服务配置"""

    id: str = Field(primary_key=True)
    """唯一标识符，由插件作者+插件名构成（eg. akirami.hello-world）"""
    name: str
    """服务名称"""
    alias: set[str] = Field(default_factory=set)
    """服务别名"""
    summary: str = ""
    """插件摘要，简短说明，用于展示在服务列表中"""
    description: str = ""
    """插件描述，详细介绍，用于展示在详细帮助界面。如果没有提供，则默认使用 summary"""
    usage: str = ""
    """使用方法"""
    version: str = "0.0.0"
    """插件版本"""
    author: str = "unknown"
    """插件作者"""
    tags: set[str] = Field(default_factory=set)
    """服务分类标签，在批量操作服务时使用，以及在服务列表中显示"""
    extra: dict[str, Any] = Field(default_factory=dict)
    """额外配置"""

    _abilities: list[Ability] = PrivateAttr(default_factory=list)

    sp_map: ClassVar[bidict[Self, Plugin]] = bidict()
    """Service - Plugin 映射表"""

    @validator("id")
    def validate_id(cls, value: str) -> str:
        return value.lower().replace("_", "-")

    @validator("author")
    def validate_author(cls, value: str) -> str:
        if " " in value or "." in value:
            raise ValueError("作者名不得包含空格或点符号")
        return value

    @property
    def plugin(self) -> Plugin:
        """插件"""
        return self.sp_map[self]

    @property
    def abilities(self) -> list[Ability]:
        """功能组"""
        return self._abilities

    def bind(self, plugin: Plugin) -> None:
        """绑定插件。

        ### 参数
            plugin: 插件对象
        """
        self.sp_map[self] = plugin

    @classmethod
    def got(cls, plugin: Plugin) -> Self:
        """获取对应的服务。

        ### 参数
            plugin: 插件对象
        """
        return cls.sp_map.inverse[plugin]

    async def init(self) -> None:
        """加载配置"""
        tasks = [ability.sync() for ability in self.abilities]
        await asyncio.gather(self.sync(), *tasks)
