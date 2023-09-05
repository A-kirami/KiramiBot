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

from kirami.depends import UserRole
from kirami.service import Role


def role_permission(role: str | Role) -> Permission:
    """检查用户是否满足角色要求"""

    def _role(user_role: UserRole) -> bool:
        return user_role.check(role)

    return Permission(_role)
