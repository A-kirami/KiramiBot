"""本模块包含了 KiramiBot 运行中接收的事件类型"""

from typing import Literal, NoReturn

from nonebot.adapters.onebot.v11 import Adapter
from nonebot.adapters.onebot.v11 import Event as Event
from nonebot.adapters.onebot.v11 import FriendAddNoticeEvent as FriendAddNoticeEvent
from nonebot.adapters.onebot.v11 import (
    FriendRecallNoticeEvent as FriendRecallNoticeEvent,
)
from nonebot.adapters.onebot.v11 import FriendRequestEvent as FriendRequestEvent
from nonebot.adapters.onebot.v11 import GroupAdminNoticeEvent as GroupAdminNoticeEvent
from nonebot.adapters.onebot.v11 import GroupBanNoticeEvent as GroupBanNoticeEvent
from nonebot.adapters.onebot.v11 import (
    GroupDecreaseNoticeEvent as GroupDecreaseNoticeEvent,
)
from nonebot.adapters.onebot.v11 import (
    GroupIncreaseNoticeEvent as GroupIncreaseNoticeEvent,
)
from nonebot.adapters.onebot.v11 import GroupMessageEvent as GroupMessageEvent
from nonebot.adapters.onebot.v11 import GroupRecallNoticeEvent as GroupRecallNoticeEvent
from nonebot.adapters.onebot.v11 import GroupRequestEvent as GroupRequestEvent
from nonebot.adapters.onebot.v11 import GroupUploadNoticeEvent as GroupUploadNoticeEvent
from nonebot.adapters.onebot.v11 import HeartbeatMetaEvent as HeartbeatMetaEvent
from nonebot.adapters.onebot.v11 import HonorNotifyEvent as HonorNotifyEvent
from nonebot.adapters.onebot.v11 import LifecycleMetaEvent as LifecycleMetaEvent
from nonebot.adapters.onebot.v11 import LuckyKingNotifyEvent as LuckyKingNotifyEvent
from nonebot.adapters.onebot.v11 import MessageEvent as MessageEvent
from nonebot.adapters.onebot.v11 import MetaEvent as MetaEvent
from nonebot.adapters.onebot.v11 import NoticeEvent as NoticeEvent
from nonebot.adapters.onebot.v11 import NotifyEvent as NotifyEvent
from nonebot.adapters.onebot.v11 import PokeNotifyEvent as PokeNotifyEvent
from nonebot.adapters.onebot.v11 import PrivateMessageEvent as PrivateMessageEvent
from nonebot.adapters.onebot.v11 import RequestEvent as RequestEvent
from nonebot.exception import NoLogException


class TimerNoticeEvent(NoticeEvent):
    """定时器事件"""

    notice_type: Literal["timer"]
    timer_id: str

    def get_log_string(self) -> NoReturn:
        raise NoLogException(Adapter.get_name())
