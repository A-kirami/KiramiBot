"""本模块定义了权限系统的基本数据结构, 包括角色和策略"""

import asyncio
from collections import defaultdict
from typing import ClassVar

from mango import Document, Field
from typing_extensions import Self

from kirami.config import bot_config
from kirami.hook import on_startup

from .subject import Subject


class BaseAccess(Document):
    name: str = Field(primary_key=True)
    """权限名称"""
    remark: str = ""
    """权限备注"""

    def __hash__(self) -> int:
        return hash(self.name)

    async def sync(self) -> None:
        """从数据库同步"""
        if access := await self.get(self.name):
            await self.update(**access.dict())


class Role(BaseAccess):
    weight: int
    """角色权重"""
    assigned: defaultdict[Subject, set[str]] = Field(
        default_factory=lambda: defaultdict(set), init=False
    )
    """分配此角色的用户, 键表示范围, 值表示用户id"""

    roles: ClassVar[dict[str, Self]] = {}
    """角色列表"""

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

    def check(self, role: str | Self) -> bool:
        """检查角色是否满足要求。

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

    async def assign_user(self, user_id: str, subject: Subject | None = None) -> None:
        """分配用户角色。

        ### 参数
            user_id: 用户 ID

            subject: 范围主体，为 None 时表示全局范围
        """
        subject = subject or Subject("global", "*")
        self.assigned[subject].add(user_id)
        await self.save()

    async def revoke_user(self, user_id: str, subject: Subject | None = None) -> None:
        """撤销用户角色。

        ### 参数
            user_id: 用户 ID

            subject: 范围主体，为 None 时撤销所有范围的角色
        """
        if subject and user_id in self.assigned[subject]:
            self.assigned[subject].remove(user_id)
        else:
            for subject in self.assigned:
                self.assigned[subject].discard(user_id)
        await self.save()

    @classmethod
    def query_user(cls, user_id: str, *subjects: Subject) -> set[Self]:
        """查询用户角色。

        ### 参数
            user_id: 用户 ID

            *subjects: 范围主体

        ### 返回
            用户角色集合
        """
        user_roles = {
            role
            for role in cls.roles.values()
            if any(user_id in role.assigned[subject] for subject in subjects)
        }
        if user_id in bot_config.superusers:
            user_roles.add(cls.roles["superuser"])
        return user_roles

    @classmethod
    def get_user_role(cls, user_id: str, *subjects: Subject) -> Self | None:
        """获取用户最大权限角色。

        ### 参数
            user_id: 用户 ID

            *subjects: 范围主体

        ### 返回
            用户最大权限角色，若无则返回 None
        """
        return max(cls.query_user(user_id, *subjects), default=None)


class Policy(BaseAccess):
    allow: set[str] = Field(default_factory=set)
    """授权访问"""
    applied: set[Subject] = Field(default_factory=set, init=False)
    """应用此策略的主体"""

    policies: ClassVar[dict[str, Self]] = {}
    """策略列表"""

    def __hash__(self) -> int:
        return super().__hash__()

    @classmethod
    def create_policy(cls, name: str, allow: set[str] | None, remark: str = "") -> Self:
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

    async def apply_policy(self, subject: Subject) -> None:
        """应用策略。

        ### 参数
            subject: 应用主体
        """
        self.applied.add(subject)

    async def unapply_policy(self, subject: Subject) -> None:
        """取消策略。

        ### 参数
            subject: 应用主体
        """
        self.applied.remove(subject)

    async def add_allow(self, *allow: str) -> None:
        """添加授权访问。

        ### 参数
            *allow: 授权访问
        """
        self.allow |= set(allow)

    async def remove_allow(self, *allow: str) -> None:
        """移除授权访问。

        ### 参数
            *allow: 授权访问
        """
        self.allow -= set(allow)

    @classmethod
    def get_policies(cls, *subjects: Subject) -> set[Self]:
        """获取主体应用的策略。

        ### 参数
            *subjects: 范围主体

        ### 返回
            主体策略集合
        """
        return {
            policy
            for policy in cls.policies.values()
            if any(subject in policy.applied for subject in subjects)
        }


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
