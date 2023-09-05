"""本模块定义了权限系统的基本数据结构, 包括角色和策略"""

import asyncio
from abc import ABC, abstractmethod
from typing import ClassVar

from mango import Document, Field
from typing_extensions import Self

from kirami.config import bot_config
from kirami.hook import on_startup

from .subject import Subject


class BaseAccess(Document, ABC):
    name: str = Field(primary_key=True)
    """权限名称"""
    remark: str = ""
    """权限备注"""

    def __hash__(self) -> int:
        return hash(self.name)

    @abstractmethod
    async def sync(self) -> None:
        """从数据库同步"""
        raise NotImplementedError

    class Meta:
        bson_encoders = {frozenset: list}


class Role(BaseAccess):
    weight: int
    """角色权重"""
    assigned: set[frozenset[Subject]] = Field(default_factory=set, init=False)
    """已分配此角色的主体的集合"""

    roles: ClassVar[dict[str, Self]] = {}
    """所有角色的字典"""

    def __hash__(self) -> int:
        return super().__hash__()

    def __eq__(self, other: str | Self) -> bool:
        if isinstance(other, str):
            other = self.roles[other]
        return self.name == other.name

    def __ne__(self, other: str | Self) -> bool:
        if isinstance(other, str):
            other = self.roles[other]
        return self.name != other.name

    def __lt__(self, other: str | Self) -> bool:
        if isinstance(other, str):
            other = self.roles[other]
        return self.weight < other.weight

    def __gt__(self, other: str | Self) -> bool:
        if isinstance(other, str):
            other = self.roles[other]
        return self.weight > other.weight

    def __le__(self, other: str | Self) -> bool:
        if isinstance(other, str):
            other = self.roles[other]
        return self.weight <= other.weight

    def __ge__(self, other: str | Self) -> bool:
        if isinstance(other, str):
            other = self.roles[other]
        return self.weight >= other.weight

    async def sync(self) -> None:
        if role := await self.get(self.name):
            self.assigned = role.assigned
            await self.save()

    def check(self, role: str | Self) -> bool:
        """检查当前角色的权重是否大于等于给定角色的权重。

        ### 参数
            role: 角色名称或角色对象
        """
        return self >= role

    @classmethod
    def create(cls, name: str, weight: int, remark: str = "") -> Self:
        """创建角色。

        ### 参数
            name: 角色名称

            weight: 角色权重

            remark: 角色备注
        """
        cls.roles[name] = cls(name=name, weight=weight, remark=remark)
        return cls.roles[name]

    async def delete(self) -> None:
        """删除角色"""
        self.roles.pop(self.name, None)
        await super().delete()

    async def assign_role(self, *subjects: Subject) -> None:
        """分配角色到指定主体。

        ### 参数
            *subjects: 分配角色的主体对象
        """
        self.assigned.add(frozenset(subjects))
        await self.save()

    async def revoke_role(self, *subjects: Subject) -> None:
        """撤销指定主体的角色。

        ### 参数
            *subjects: 撤销角色的主体对象
        """
        self.assigned.discard(frozenset(subjects))
        await self.save()

    @classmethod
    def get_all_role(cls, *subjects: Subject) -> set[Self]:
        """获取指定主体拥有的全部角色。

        ### 参数
            *subjects: 指定主体对象
        """
        user_roles = {
            role
            for role in cls.roles.values()
            if any(asssub.issubset(subjects) for asssub in role.assigned)
        }
        if any(
            subject.type == "user" and subject.id in bot_config.superusers
            for subject in subjects
        ):
            user_roles.add(cls.roles["superuser"])
        return user_roles

    @classmethod
    def get_role(cls, *subjects: Subject) -> Self | None:
        """获取指定主体的最大权重角色。

        ### 参数
            *subjects: 指定主体对象
        """
        return max(cls.get_all_role(*subjects), default=None)


class Policy(BaseAccess):
    allow: set[str] = Field(default_factory=set)
    """授权访问的内容集合"""
    applied: set[frozenset[Subject]] = Field(default_factory=set, init=False)
    """已应用此策略的主体集合"""

    policies: ClassVar[dict[str, Self]] = {}
    """所有策略的字典"""

    def __hash__(self) -> int:
        return super().__hash__()

    async def sync(self) -> None:
        if policy := await self.get(self.name):
            self.allow = policy.allow
            self.applied = policy.applied
            await self.save()

    def check(self, allow: str) -> bool:
        """检查授权访问是否在策略的授权访问集合中。

        ### 参数
            allow: 授权访问内容
        """
        return allow in self.allow

    @classmethod
    def create(cls, name: str, allow: set[str] | None, remark: str = "") -> Self:
        """创建策略。

        ### 参数
            name: 策略名称

            allow: 授权访问

            remark: 策略备注
        """
        cls.policies[name] = cls(name=name, allow=allow or set(), remark=remark)
        return cls.policies[name]

    async def delete(self) -> None:
        """删除策略"""
        self.policies.pop(self.name, None)
        await super().delete()

    async def apply_policy(self, *subject: Subject) -> None:
        """应用策略到指定主体。

        ### 参数
            *subject: 应用策略的主体对象
        """
        self.applied.add(frozenset(subject))
        await self.save()

    async def unapply_policy(self, *subject: Subject) -> None:
        """取消指定主体的策略。

        ### 参数
            *subject: 取消策略的主体对象
        """
        self.applied.discard(frozenset(subject))
        await self.save()

    async def add_allow(self, *allow: str) -> None:
        """添加策略的授权访问内容。

        ### 参数
            *allow: 添加的授权访问内容
        """
        self.allow |= set(allow)
        await self.save()

    async def remove_allow(self, *allow: str) -> None:
        """移除策略的授权访问内容。

        ### 参数
            *allow: 移除的授权访问内容
        """
        self.allow -= set(allow)
        await self.save()

    @classmethod
    def get_policies(cls, *subjects: Subject) -> set[Self]:
        """获取指定主体的全部应用策略。

        ### 参数
            *subjects: 指定主体对象
        """
        return {
            policy
            for policy in cls.policies.values()
            if any(appsub.issubset(subjects) for appsub in policy.applied)
        }

    @classmethod
    def get_allowed(cls, *subjects: Subject) -> set[str]:
        """获取指定主体的全部授权访问内容。

        如果指定主体没有应用策略，则返回 `default_policy_allow` 配置内容。

        ### 参数
            *subjects: 主体范围
        """
        if policies := cls.get_policies(*subjects):
            return {allow for policy in policies for allow in policy.allow}
        return bot_config.default_policy_allow


Role.roles |= {
    "normal": Role(name="normal", weight=1, remark="普通用户"),
    "admin": Role(name="admin", weight=9, remark="管理员"),
    "owner": Role(name="owner", weight=99, remark="群主"),
    "superuser": Role(name="superuser", weight=999, remark="超级用户"),
}

Policy.policies |= {
    "whitelist": Policy(name="whitelist", allow={"*"}, remark="白名单"),
    "blacklist": Policy(name="blacklist", allow=set(), remark="黑名单"),
}


@on_startup
async def init_access_control() -> None:
    tasks = [access.sync() for access in (Role.roles | Policy.policies).values()]
    await asyncio.gather(*tasks)
