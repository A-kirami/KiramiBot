"""本模块定义了服务控制器, 用于控制服务的运行"""

import asyncio
from contextlib import AsyncExitStack
from typing import Annotated, Any

from nonebot.dependencies import Dependent
from nonebot.exception import SkippedException
from nonebot.message import RUN_PREPCS_PARAMS
from nonebot.typing import _DependentCallable
from nonebot.utils import run_coro_with_catch

from kirami.depends import UserRole, depends
from kirami.exception import IgnoredException
from kirami.hook import before_run
from kirami.log import logger
from kirami.matcher import Matcher
from kirami.typing import Bot, Event, MessageEvent, State

from .access import Policy
from .limiter import Cooldown, Quota, get_scope_key
from .manager import ServiceManager
from .service import Ability, Service
from .subject import EventSubjects

_checkers: set[Dependent[Any]] = set()


@before_run
async def service_controller(
    matcher: Matcher,
    bot: Bot,
    event: Event,
    state: State,
) -> None:
    async with AsyncExitStack() as stack:
        coros = [
            run_coro_with_catch(
                checker(
                    matcher=matcher,
                    bot=bot,
                    event=event,
                    state=state,
                    stack=stack,
                    dependency_cache={},
                ),
                (SkippedException,),
            )
            for checker in _checkers
        ]
        with matcher.ensure_context(bot, event):
            try:
                await asyncio.gather(*coros)
            except IgnoredException as e:
                logger.opt(colors=True).debug(
                    f"{matcher} 服务检查未通过: {e.reason}",
                )
                raise
            except Exception as e:
                logger.opt(colors=True, exception=e).error(
                    "<r><bg #f8bbd0>服务控制器检查时出现意外错误, 运行已取消</bg #f8bbd0></r>",
                )
                raise


T_ServiceChecker = _DependentCallable[Any]


def register_checker(checker: T_ServiceChecker) -> None:
    """注册服务检查器"""
    _checkers.add(
        Dependent[bool].parse(
            call=checker,
            allow_types=RUN_PREPCS_PARAMS,
        )
    )


@depends
def useService(matcher: Matcher) -> Service:
    return ServiceManager.get_service(matcher)


D_Service = Annotated[Service, useService()]


@depends
def useAbility(matcher: Matcher) -> Ability | None:
    return None if not matcher.priority and matcher.temp else Ability.got(matcher)


D_Ability = Annotated[Ability, useAbility()]


@register_checker
async def event_scope_checker(
    event: MessageEvent, service: D_Service, ability: D_Ability
) -> None:
    """事件作用域检查"""

    async def check_scope(source: Service | Ability, message_type: str) -> None:
        if source.scope != "all" and message_type != source.scope:
            raise IgnoredException("事件作用域不一致")

    sources = [service, ability]
    tasks = [check_scope(source, event.message_type) for source in sources]
    await asyncio.gather(*tasks)


@register_checker
async def enabled_checker(
    service: D_Service, ability: D_Ability, subjects: EventSubjects
) -> None:
    """服务开关检查"""
    if dissbj := ability.get_disabled_subjects(*subjects):
        dissbj_str = ", ".join(repr(s) for s in dissbj)
        raise IgnoredException(f'功能"{service.name}#{ability.name}"未启用: {dissbj_str}')
    if dissbj := service.get_disabled_subjects(*subjects):
        dissbj_str = ", ".join(repr(s) for s in dissbj)
        raise IgnoredException(f'服务"{service.name}"未启用: {dissbj_str}')


@register_checker
async def role_checker(service: D_Service, ability: D_Ability, role: UserRole) -> None:
    """角色检查"""
    if role.check(ability.role.user):
        return
    if role.check(service.role.user):
        return
    raise IgnoredException(f"用户角色权限不足, 服务或功能至少需要{role.name}, 当前为{role.name}")


@register_checker
async def policy_checker(
    service: D_Service, ability: D_Ability, subjects: EventSubjects
) -> None:
    """策略检查"""
    allowed = Policy.get_allowed(*subjects)
    if "*" in allowed:
        return
    if ability.id in allowed:
        return
    if service.id in allowed:
        return
    raise IgnoredException(f"主体策略没有访问服务或功能的许可: {', '.join(repr(s) for s in subjects)}")


@register_checker
async def cooldown_checker(
    matcher: Matcher, event: Event, service: D_Service, ability: D_Ability
) -> None:
    """冷却时间检查"""

    async def check_cooldown(source: Service | Ability) -> None:
        """检查冷却时间是否已过"""
        cd_cfg = source.cooldown
        if not cd_cfg:
            return
        cooldown = await Cooldown.get(source.id) or Cooldown(
            name=source.id,
            scope=cd_cfg.type,
            prompt=cd_cfg.prompt,
            duration=cd_cfg.time,
        )
        if not (key := get_scope_key(event, cd_cfg.type)):
            return
        if cooldown.check(key):
            await cooldown.start(key)
            return
        if prompt := cooldown.get_prompt(key):
            await matcher.send(prompt)
        raise IgnoredException("服务或功能正在冷却中")

    sources = [service, ability]
    tasks = [check_cooldown(source) for source in sources]
    await asyncio.gather(*tasks)


@register_checker
async def quota_checker(
    matcher: Matcher, event: Event, service: D_Service, ability: D_Ability
) -> None:
    """使用次数检查"""

    async def check_quota(source: Service | Ability) -> None:
        """检查使用次数是否已达上限"""
        qt_cfg = source.quota
        if not qt_cfg:
            return
        quota = await Quota.get(source.id) or Quota(
            name=source.id,
            scope=qt_cfg.type,
            prompt=qt_cfg.prompt,
            limit=qt_cfg.limit,
            reset_time=qt_cfg.reset,
        )
        if not (key := get_scope_key(event, qt_cfg.type)):
            return
        if quota.check(key):
            await quota.consume(key)
            return
        if prompt := quota.get_prompt(key):
            await matcher.send(prompt)
        raise IgnoredException("服务或功能的配额已达上限")

    sources = [service, ability]
    tasks = [check_quota(source) for source in sources]
    await asyncio.gather(*tasks)
