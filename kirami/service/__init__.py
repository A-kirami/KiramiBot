"""
服务控制
====

将一组功能组合成一个服务，并对服务进行控制。

本模块定义了服务的基本概念，包括服务、功能、主体、角色、策略等。
"""

from .access import Policy as Policy
from .access import Role as Role
from .controller import register_checker as register_checker
from .limiter import Cooldown as Cooldown
from .limiter import CooldownInfo as CooldownInfo
from .limiter import LimitScope as LimitScope
from .limiter import Lock as Lock
from .limiter import LockInfo as LockInfo
from .limiter import Quota as Quota
from .limiter import QuotaInfo as QuotaInfo
from .limiter import get_scope_key as get_scope_key
from .manager import ServiceManager as ServiceManager
from .service import Ability as Ability
from .service import Service as Service
from .subject import EventSubjects as EventSubjects
from .subject import Subject as Subject
from .subject import register_extractor as register_extractor
