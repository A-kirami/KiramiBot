"""本模块定义了各类常用的依赖注入参数"""

from collections.abc import AsyncGenerator
from datetime import time
from re import Match
from typing import Annotated, Any, Literal, TypeAlias, TypeVar

from httpx._types import ProxiesTypes, VerifyTypes
from nonebot.adapters import Message, MessageSegment
from nonebot.exception import ParserExit
from nonebot.internal.params import Arg as useArg
from nonebot.internal.params import ArgInner
from nonebot.internal.params import ArgPlainText as useArgPlainText
from nonebot.internal.params import ArgStr as useArgStr
from nonebot.internal.params import DependsInner as BaseDependsInner
from nonebot.params import Command as useCommand
from nonebot.params import CommandArg as useCommandArg
from nonebot.params import CommandWhitespace as useCommandWhitespace
from nonebot.params import EventMessage as useEventMessage
from nonebot.params import EventPlainText as useEventPlainText
from nonebot.params import EventType as useEventType
from nonebot.params import LastReceived as originalLastReceived
from nonebot.params import RawCommand as useRawCommand
from nonebot.params import Received as originalReceived
from nonebot.params import RegexDict as useRegexDict
from nonebot.params import RegexGroup as useRegexGroup
from nonebot.params import RegexMatched as useRegexMatched
from nonebot.params import RegexStr as useRegexStr
from nonebot.params import ShellCommandArgs as useShellCommandArgs
from nonebot.params import ShellCommandArgv as useShellCommandArgv
from nonebot.rule import Namespace
from playwright.async_api import BrowserContext, Page

from kirami.database import Group, User
from kirami.matcher import Matcher
from kirami.service.access import Role
from kirami.service.limiter import Cooldown, LimitScope, Lock, Quota, get_scope_key
from kirami.service.service import Ability
from kirami.service.subject import EventSubjects as EventSubjects
from kirami.typing import (
    AsyncClient,
    Bot,
    Event,
    GroupMessageEvent,
    MessageEvent,
    T_Handler,
)
from kirami.utils import (
    Request,
    WebWright,
    extract_at_users,
    extract_image_urls,
    extract_match,
    extract_plain_text,
)

T = TypeVar("T")


class DependsInner(BaseDependsInner):
    def __call__(
        self,
        dependency: T_Handler | None = None,
        *,
        use_cache: bool | None = None,
    ) -> Any:
        dependency = dependency or self.dependency
        use_cache = use_cache or self.use_cache
        return self.__class__(dependency, use_cache=use_cache)


def depends(dependency: T_Handler | None = None, *, use_cache: bool = True) -> Any:
    """子依赖装饰器。

    ### 参数
        dependency: 依赖函数。默认为参数的类型注释

        use_cache: 是否使用缓存。默认为 `True`

    ### 用例

        ```python
        @depends
        def depend_func() -> Any:
            return ...

        @depends(use_cache=False)
        def depend_gen_func():
            try:
                yield ...
            finally:
                ...

        async def handler(param_name: Any = depend_func, gen: Any = depend_gen_func):
            ...
        ```
    """
    return DependsInner(dependency, use_cache=use_cache)


Arg = Annotated[Message, useArg()]
"""`got` 的 Arg 参数消息"""

ArgPlainText = Annotated[str, useArgPlainText()]
"""`got` 的 Arg 参数消息文本"""

ArgStr = Annotated[str, useArgStr()]
"""`got` 的 Arg 参数消息纯文本"""

Command = Annotated[tuple[str, ...], useCommand()]
"""消息命令元组"""

CommandArg = Annotated[Message, useCommandArg()]
"""消息命令参数"""

CommandWhitespace = Annotated[str, useCommandWhitespace()]
"""消息命令与参数之间的空白"""

EventMessage = Annotated[Message, useEventMessage()]
"""事件消息参数"""

EventPlainText = Annotated[str, useEventPlainText()]
"""事件纯文本消息参数"""

EventType = Annotated[str, useEventType()]
"""事件类型参数"""

RawCommand = Annotated[str, useRawCommand()]
"""消息命令文本"""

RegexDict = Annotated[dict[str, Any], useRegexDict()]
"""正则匹配结果 group 字典"""

RegexGroup = Annotated[tuple[Any, ...], useRegexGroup()]
"""正则匹配结果 group 元组"""

RegexMatched = Annotated[Match[str], useRegexMatched()]
"""正则匹配结果"""

RegexStr = Annotated[str, useRegexStr()]
"""正则匹配结果文本"""

ShellCommandArgs = Annotated[Namespace, useShellCommandArgs()]
"""shell 命令解析后的参数字典"""

ShellCommandExit = Annotated[ParserExit, useShellCommandArgs()]
"""shell 命令解析失败的异常"""

ShellCommandArgv = Annotated[list[str | MessageSegment], useShellCommandArgv()]
"""shell 命令原始参数列表"""


def useReceived(id: str | None = None, default: Any = None) -> Any:
    """`receive` 事件参数"""
    return originalReceived(id, default)


def useLastReceived(default: Any = None) -> Any:
    """`last_receive` 事件参数"""
    return originalLastReceived(default)


LastReceived = Annotated[Event, useLastReceived()]
"""`last_receive` 事件参数"""


@depends
def useToMe(event: Event) -> bool:
    """事件是否与机器人有关"""
    return event.is_tome()


ToMe: TypeAlias = Annotated[bool, useToMe()]
"""事件是否与机器人有关"""


@depends
def useReplyMe(event: MessageEvent) -> bool:
    """是否回复了机器人的消息"""
    return bool(event.reply)


ReplyMe: TypeAlias = Annotated[bool, useReplyMe()]
"""是否回复了机器人的消息"""


@depends
async def useUserData(event: Event) -> User | None:
    """获取用户数据文档模型"""
    if uid := getattr(event, "user_id"):
        return await User.get_or_create(User.id == uid)
    return None


UserData: TypeAlias = Annotated[User, useUserData()]
"""用户数据文档模型"""


@depends
async def useGroupData(event: Event) -> Group | None:
    """获取群数据文档模型"""
    if gid := getattr(event, "group_id"):
        return await Group.get_or_create(Group.id == gid)
    return None


GroupData: TypeAlias = Annotated[User, useGroupData()]
"""群数据文档模型"""


def useImageURLs(prompt: str | None = None, from_reply: bool = False) -> list[str]:
    """提取消息中图片链接。

    ### 参数
        prompt: 当不存在图片链接时发送给用户的错误消息，默认不发送

        from_reply: 是否从回复中提取，默认为 `False`
    """

    @depends
    async def image_urls(event: MessageEvent, matcher: Matcher) -> list[str]:
        return await extract_match(
            extract_image_urls, event, matcher, prompt, from_reply
        )

    return image_urls


ImageURLs = Annotated[list[str], useImageURLs()]
"""消息中图片链接"""


def useAtUsers(prompt: str | None = None, from_reply: bool = False) -> list[str]:
    """获取消息中提及的用户。

    ### 参数
        prompt: 当不存在提及用户时发送给用户的错误消息，默认不发送

        from_reply: 是否从回复中提取，默认为 `False`
    """

    @depends
    async def at_users(event: MessageEvent, matcher: Matcher) -> list[str]:
        return await extract_match(extract_at_users, event, matcher, prompt, from_reply)

    return at_users


AtUsers = Annotated[list[str], useAtUsers()]
"""消息中提及的用户"""


def usePlainText(prompt: str | None = None, from_reply: bool = False) -> str:
    """提取消息内纯文本消息。

    ### 参数
        prompt: 当不存在纯文本消息时发送给用户的错误消息，默认不发送

        from_reply: 是否从回复中提取，默认为 `False`
    """

    @depends
    async def plain_text(event: MessageEvent, matcher: Matcher) -> str:
        return await extract_match(
            extract_plain_text, event, matcher, prompt, from_reply
        )

    return plain_text


PlainText = Annotated[str, usePlainText()]
"""消息内纯文本消息"""


def useClientSession(
    verify: VerifyTypes = True,
    http2: bool = False,
    proxies: ProxiesTypes | None = None,
    **kwargs,
) -> AsyncClient:
    """获取网络连接会话对象"""

    @depends
    async def client_session() -> AsyncGenerator[AsyncClient, None]:
        async with Request.client_session(
            verify=verify, http2=http2, proxies=proxies, **kwargs
        ) as session:
            yield session

    return client_session


ClientSession = Annotated[AsyncClient, useClientSession()]
"""网络连接会话对象"""


def useStateData(key: str | None = None) -> Any:
    """提取会话状态内容"""
    return ArgInner(key, type="state")  # type: ignore


StateData = Annotated[T, useStateData()]
"""会话状态内容"""


def useArgot(key: str | None = None) -> Any:
    """提取暗语的内容"""
    return ArgInner(key, type="argot")  # type: ignore


Argot = Annotated[T, useArgot()]
"""暗语内容"""


def useWebContext(**kwargs) -> BrowserContext:
    """创建浏览器上下文"""

    @depends
    async def web_context() -> AsyncGenerator[BrowserContext, None]:
        async with WebWright.new_context(**kwargs) as context:
            yield context

    return web_context


WebContext: TypeAlias = Annotated[BrowserContext, useWebContext()]
"""浏览器上下文"""


def useWebPage(**kwargs) -> Page:
    """创建浏览器页面"""

    @depends
    async def web_page() -> AsyncGenerator[Page, None]:
        async with WebWright.new_page(**kwargs) as page:
            yield page

    return web_page


WebPage: TypeAlias = Annotated[Page, useWebPage()]
"""浏览器页面"""


def useUserName() -> str:
    """获取用户名，如果为群事件则获取群名片"""

    @depends
    async def user_name(bot: Bot, event: Event) -> str:
        if isinstance(event, MessageEvent):
            return event.sender.card or event.sender.nickname or ""
        if not (uid := getattr(event, "user_id", None)):
            return ""
        if gid := getattr(event, "group_id", None):
            info = await bot.get_group_member_info(group_id=gid, user_id=uid)
            return info["card"] or info["nickname"]
        info = await bot.get_stranger_info(user_id=uid)
        return info["nickname"]

    return user_name


UserName = Annotated[str, useUserName()]
"""用户名、群名片或用户昵称"""


avatar_spec = {"small": 40, "medium": 140, "large": 640}


def useUserAvatar(size: Literal["small", "medium", "large"] = "large") -> str:
    """获取用户头像链接"""

    @depends
    def user_avatar(event: Event) -> str | None:
        if uid := getattr(event, "user_id", None):
            return f"https://q1.qlogo.cn/g?b=qq&nk={uid}&s={avatar_spec[size]}"
        return None

    return user_avatar


UserAvatar = Annotated[str, useUserAvatar()]
"""用户头像链接"""


def useGroupAvatar(size: Literal["small", "medium", "large"] = "large") -> str:
    """获取群头像链接"""

    @depends
    def group_avatar(event: Event) -> str | None:
        if gid := getattr(event, "group_id", None):
            return f"https://p.qlogo.cn/gh/{gid}/{gid}/{avatar_spec[size]}"
        return None

    return group_avatar


GroupAvatar = Annotated[str, useGroupAvatar()]
"""获取头像链接"""


def useCooldown(
    cd_time: int,
    *,
    prompt: str | None = None,
    scope: LimitScope = LimitScope.LOCAL,
    **kwargs: Any,
) -> Cooldown:
    """使用冷却时间限制"""

    @depends
    async def check_cooldown(
        matcher: Matcher, event: Event
    ) -> AsyncGenerator[Cooldown, None]:
        name = f"depends:{Ability.got(matcher).id}"
        cooldown = await Cooldown.get(name) or Cooldown(
            name=name, scope=scope, prompt=prompt, duration=cd_time
        )

        if not (key := get_scope_key(event, scope)):
            return

        if not cooldown.check(key):
            await matcher.finish(
                prompt.format(**cooldown.get_info(key)) if prompt else None,
                **kwargs,
            )

        yield cooldown

        await cooldown.start(key)

    return check_cooldown


def useQuota(
    limit: int,
    *,
    prompt: str | None = None,
    scope: LimitScope = LimitScope.LOCAL,
    reset_time: int | str | time | None = None,
    **kwargs: Any,
) -> Quota:
    """使用配额次数限制"""

    @depends
    async def check_quota(
        matcher: Matcher, event: Event
    ) -> AsyncGenerator[Quota, None]:
        name = f"depends:{Ability.got(matcher).id}"
        quota = await Quota.get(name) or Quota(
            name=name,
            scope=scope,
            prompt=prompt,
            limit=limit,
            reset_time=reset_time or time(),
        )

        if not (key := get_scope_key(event, scope)):
            return

        if not quota.check(key):
            await matcher.finish(
                prompt.format(**quota.get_info(key)) if prompt else None,
                **kwargs,
            )

        yield quota

        await quota.consume(key)

    return check_quota


def useLock(
    max_count: int = 1,
    *,
    prompt: str | None = None,
    scope: LimitScope = LimitScope.LOCAL,
    **kwargs: Any,
) -> None:
    """使用事件锁定限制"""

    @depends
    async def check_lock(matcher: Matcher, event: Event) -> AsyncGenerator[Lock, None]:
        name = f"depends:{Ability.got(matcher).id}"
        if not (lock := Lock.get(name)):
            lock = Lock(
                matcher=matcher.__class__,
                scope=scope,
                prompt=prompt,
                max_count=max_count,
            )
            Lock.set(name, lock)

        if not (key := get_scope_key(event, scope)):
            return

        if not lock.check(key):
            await matcher.finish(
                prompt.format(**lock.get_info(key)) if prompt else None,
                **kwargs,
            )

        lock.claim(key)

        try:
            yield lock
        finally:
            lock.unclaim(key)

    return check_lock


def useConfirm(*keywords: str) -> bool:
    """检查消息是否表示确认"""

    keywords = keywords or ("确认", "确定", "是", "yes", "y")

    @depends
    async def dependency(message: EventPlainText) -> bool:
        return any(kw == message for kw in keywords)

    return dependency


Confirm: TypeAlias = Annotated[bool, useConfirm()]


def useCancel(*keywords: str) -> bool:
    """检查消息是否表示取消"""

    keywords = keywords or ("取消", "退出", "否", "no", "n")

    @depends
    async def dependency(message: EventPlainText) -> bool:
        return any(kw == message for kw in keywords)

    return dependency


Cancel: TypeAlias = Annotated[bool, useCancel()]


def handleCancel(*keywords: str, prompt: str | None = None) -> None:
    """检查消息是否表示取消，并结束事件处理"""

    @depends
    async def dependency(matcher: Matcher, cancel: bool = useCancel(*keywords)) -> None:
        if cancel:
            await matcher.finish(prompt)

    return dependency


@depends
def useUserRole(event: Event, subjects: EventSubjects) -> Role:
    role = Role.roles["normal"]
    if isinstance(event, GroupMessageEvent):
        sender_role = event.sender.role
        sender_role = "normal" if sender_role in ("member", None) else sender_role
        role = Role.roles[sender_role]
    if hasattr(event, "user_id"):
        role = Role.get_role(*subjects) or role
    return role


UserRole: TypeAlias = Annotated[Role, useUserRole()]
