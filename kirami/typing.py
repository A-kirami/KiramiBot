"""本模块集合了 KiramiBot 开发中的一些常用类型"""

from argparse import Namespace as Namespace

from flowery.typing import PILImage as PILImage
from httpx import AsyncClient as AsyncClient
from nonebot.adapters import MessageTemplate as MessageTemplate
from nonebot.adapters.onebot.v11 import Bot as Bot
from nonebot.exception import ParserExit as ParserExit
from nonebot.permission import Permission as Permission
from nonebot.plugin import PluginMetadata as PluginMetadata
from nonebot.typing import T_Handler as T_Handler
from nonebot.typing import T_PermissionChecker as T_PermissionChecker
from nonebot.typing import T_RuleChecker as T_RuleChecker

from kirami.event import *  # noqa: F403 # type: ignore
from kirami.matcher import Matcher as Matcher
from kirami.message import Message as Message
from kirami.message import MessageSegment as MessageSegment
from kirami.state import State as State
