"""本模块包含了权限类和权限检查辅助。"""

from nonebot.adapters.onebot.v11.permission import GROUP as GROUP
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN as GROUP_ADMIN
from nonebot.adapters.onebot.v11.permission import GROUP_MEMBER as GROUP_MEMBER
from nonebot.adapters.onebot.v11.permission import GROUP_OWNER as GROUP_OWNER
from nonebot.adapters.onebot.v11.permission import PRIVATE as PRIVATE
from nonebot.adapters.onebot.v11.permission import PRIVATE_FRIEND as PRIVATE_FRIEND
from nonebot.adapters.onebot.v11.permission import PRIVATE_GROUP as PRIVATE_GROUP
from nonebot.adapters.onebot.v11.permission import PRIVATE_OTHER as PRIVATE_OTHER
from nonebot.permission import MESSAGE as MESSAGE
from nonebot.permission import METAEVENT as METAEVENT
from nonebot.permission import NOTICE as NOTICE
from nonebot.permission import REQUEST as REQUEST
from nonebot.permission import SUPERUSER as SUPERUSER
from nonebot.permission import USER as USER
from nonebot.permission import Permission as Permission
from nonebot.permission import User as User

from kirami.event import Event, GroupMessageEvent
from kirami.service import Role, Subjects


async def role_permission(role: Role) -> Permission:
    """检查用户是否满足角色要求"""

    def _role(event: Event, subjects: Subjects) -> bool:
        user_role = Role.roles["normal"]
        if isinstance(event, GroupMessageEvent):
            sender_role = event.sender.role
            sender_role = "normal" if sender_role in ("member", None) else sender_role
            user_role = Role.roles[sender_role]
        if uid := getattr(event, "user_id", None):
            user_role = Role.get_user_role(uid, *subjects) or user_role
        return user_role >= role

    return Permission(_role)
