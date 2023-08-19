"""本模块定义了限制器，用于限制用户的行为"""

import asyncio
import math
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import datetime
from datetime import time as Time
from enum import Enum
from typing import ClassVar, TypedDict, cast

from mango import Document, Field
from nonebot.adapters import MessageTemplate as MessageTemplate
from pydantic import BaseModel, validator
from pydantic import Field as PField
from typing_extensions import Self

from kirami.event import Event
from kirami.hook import on_startup
from kirami.matcher import Matcher
from kirami.utils import get_daily_datetime, human_readable_time


class LimitScope(str, Enum):
    """限制隔离范围"""

    GLOBAL = "global"
    """全局共用"""
    GROUP = "group"
    """群组内共用"""
    USER = "user"
    """用户独立"""
    LOCAL = "local"
    """群组内每个用户独立"""


TARGET = {
    LimitScope.GLOBAL: "全局",
    LimitScope.GROUP: "本群",
    LimitScope.USER: "你",
    LimitScope.LOCAL: "你",
}


def get_scope_key(event: Event, scope: LimitScope = LimitScope.LOCAL) -> str | None:
    """获取限制隔离范围键值。

    ### 参数
        event: 事件对象

        scope: 限制隔离范围
    """
    if group_id := getattr(event, "group_id", None):
        group_id = str(group_id)
    if user_id := getattr(event, "user_id", None):
        user_id = str(user_id)

    match scope:
        case LimitScope.GLOBAL:
            return scope.name
        case LimitScope.GROUP:
            return group_id or user_id
        case LimitScope.USER:
            return user_id
        case _:
            return f"{group_id}_{user_id}" if group_id else user_id


class Limiter(BaseModel, ABC):
    scope: LimitScope = PField(default=LimitScope.LOCAL)
    """限制隔离范围"""
    prompt: str | None = PField(default=None)
    """限制状态提示"""

    @abstractmethod
    def check(self, key: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def get_info(self, key: str) -> TypedDict:
        raise NotImplementedError

    def get_prompt(self, key: str, **kwargs) -> str | None:
        """获取限制提示。

        ### 参数
            key: 限制器键值

            **kwargs: prompt 格式化参数
        """
        if self.prompt is None:
            return None
        return self.prompt.format(**self.get_info(key), **kwargs)


class PersistLimiter(Document, Limiter, ABC):
    name: str = Field(primary_key=True)
    """限制器名称"""

    _instances: ClassVar[set[Self]] = set()
    _synced: ClassVar[bool] = False

    def __init__(self, **data) -> None:
        super().__init__(**data)
        if not self._synced:
            self._instances.add(self)

    def __hash__(self) -> int:
        return hash(self.name)

    @abstractmethod
    async def sync(self) -> None:
        """从数据库中同步配置"""
        raise NotImplementedError


class CooldownInfo(TypedDict):
    target: str
    """冷却对象"""
    duration: int | float
    """默认冷却时间"""
    remain_time: int
    """剩余冷却时间"""
    human_remain_time: str
    """剩余冷却时间(人类可读)"""


class Cooldown(PersistLimiter):
    duration: int | float = Field(default=15)
    """默认冷却时间"""
    expire: defaultdict[str, float] = Field(
        default_factory=lambda: defaultdict(float), init=False
    )
    """冷却到期时间"""

    async def start(self, key: str, duration: int | float = 0) -> None:
        """进入冷却时间。

        ### 参数
            key: 冷却键值

            duration: 冷却时间，若为 0 则使用默认冷却时间
        """
        self.expire[key] = time.time() + (duration or self.duration)
        await self.save()

    def check(self, key: str) -> bool:
        """检查是否冷却中。

        ### 参数
            key: 冷却键值
        """
        return time.time() >= self.expire[key]

    def get_remain_time(self, key: str) -> int:
        """获取剩余冷却时间。

        ### 参数
            key: 冷却键值
        """
        return math.ceil(self.expire[key] - time.time())

    def get_info(self, key: str) -> CooldownInfo:
        """获取冷却信息。

        ### 参数
            key: 冷却键值
        """
        remain_time = self.get_remain_time(key)
        return {
            "target": TARGET[self.scope],
            "duration": self.duration,
            "remain_time": remain_time,
            "human_remain_time": human_readable_time(remain_time),
        }

    async def sync(self) -> None:
        if cooldown := await self.get(self.name):
            self.expire = cooldown.expire
            await self.save()


class QuotaInfo(TypedDict):
    target: str
    """配额对象"""
    limit: int
    """每日配额数量"""
    accum: int
    """累计消耗配额"""
    remain_amount: int
    """剩余配额"""


class Quota(PersistLimiter):
    limit: int = Field(default=3)
    """每日配额数量"""
    accum: defaultdict[str, int] = Field(
        default_factory=lambda: defaultdict(int), init=False
    )
    """累计消耗配额"""
    reset_time: int | str | Time = Field(default_factory=Time, exclude=True)
    """重置时间"""
    reset_at: datetime | None = Field(default=None, expire=0, init=False)
    """下次重置时间"""

    @validator("reset_time", pre=True)
    def parse_time(cls, value: int | str | Time) -> Time:
        if isinstance(value, int):
            return Time(hour=value)

        if isinstance(value, str):
            parts = value.split(":")
            if len(parts) > 4:  # noqa: PLR2004
                raise ValueError("Invalid time format")

            return Time(*map(int, parts))  # type: ignore

        return value

    async def consume(self, key: str, amount: int = 1) -> None:
        """消耗配额。

        ### 参数
            key: 配额键值

            amount: 消耗数量，默认为 1
        """
        self.accum[key] += amount
        if self.reset_at is None:
            self.reset_at = get_daily_datetime(cast(Time, self.reset_time))
        await self.save()

    def check(self, key: str) -> bool:
        """检查是否有剩余配额。

        ### 参数
            key: 配额键值
        """
        return self.accum[key] < self.limit

    def get_accum(self, key: str) -> int:
        """获取已消耗的配额。

        ### 参数
            key: 配额键值
        """
        return self.accum[key]

    def get_info(self, key: str) -> QuotaInfo:
        """获取配额信息。

        ### 参数
            key: 配额键值
        """
        return {
            "target": TARGET[self.scope],
            "limit": self.limit,
            "accum": self.get_accum(key),
            "remain_amount": self.limit - self.get_accum(key),
        }

    async def reset(self, key: str) -> None:
        """重置配额。

        ### 参数
            key: 配额键值
        """
        self.accum[key] = 0
        await self.save()

    async def reset_all(self) -> None:
        """重置所有配额"""
        self.accum = defaultdict(int)
        await self.save()

    async def sync(self) -> None:
        if quota := await self.get(self.name):
            self.accum = quota.accum
            await self.save()


class LockInfo(TypedDict):
    target: str
    """锁定对象"""
    max_count: int
    """最大锁定数量"""
    count: int
    """已锁定数量"""
    remain_count: int
    """剩余锁定数量"""


class Lock(Limiter):
    matcher: type[Matcher]
    """事件响应器"""
    max_count: int = PField(default=1)
    """最大锁定数量"""
    tasks: defaultdict[str, int] = PField(
        default_factory=lambda: defaultdict(int), init=False
    )
    """运行中的任务"""
    _locked_matchers: ClassVar[dict[str, Self]] = {}
    """事件锁定器"""

    @classmethod
    def get(cls, id: str) -> Self | None:
        """获取事件锁定器。

        ### 参数
            id: 事件响应器 ID
        """
        return cls._locked_matchers.get(id)

    @classmethod
    def set(cls, id: str, lock: Self) -> None:
        """保存事件锁定器。

        ### 参数
            id: 事件响应器 ID

            lock: 事件锁定器
        """
        cls._locked_matchers[id] = lock

    def claim(self, key: str) -> None:
        """锁定事件。

        ### 参数
            key: 锁定键值
        """
        self.tasks[key] += 1

    def unclaim(self, key: str) -> None:
        """释放事件。

        ### 参数
            key: 锁定键值
        """
        self.tasks[key] -= 1

    def check(self, key: str) -> bool:
        """检查是否已到锁定上限。

        ### 参数
            key: 锁定键值
        """
        return self.get_count(key) < self.max_count

    def get_count(self, key: str) -> int:
        """获取已锁定数量。

        ### 参数
            key: 锁定键值
        """
        return self.tasks[key]

    def get_info(self, key: str) -> LockInfo:
        """获取锁定信息。

        ### 参数
            key: 锁定键值
        """
        return {
            "target": TARGET[self.scope],
            "max_count": self.max_count,
            "count": self.get_count(key),
            "remain_count": self.max_count - self.get_count(key),
        }


@on_startup
async def sync_limiter() -> None:
    tasks = [limiter.sync() for limiter in PersistLimiter._instances]
    await asyncio.gather(*tasks)
    PersistLimiter._synced = True
