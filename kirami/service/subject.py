"""本模块定义了主体及提取函数"""

import asyncio
from collections.abc import Callable, Generator
from contextlib import AsyncExitStack
from typing import Annotated

from nonebot.dependencies import Dependent
from nonebot.exception import SkippedException
from nonebot.message import EVENT_PCS_PARAMS
from nonebot.params import Depends
from nonebot.typing import _DependentCallable
from nonebot.utils import run_coro_with_catch
from typing_extensions import Self

from kirami.log import logger
from kirami.typing import Bot, Event, GroupMessageEvent, MessageEvent


class Subject(str):
    __slots__ = ("type", "id")

    type: str
    """主体类型"""
    id: str
    """主体标识符，*表示所有"""

    def __new__(cls, type: str = "*", id: str | int = "*") -> Self:
        obj = super().__new__(cls, f"{type}:{id}")
        obj.type = type
        obj.id = str(id)
        return obj

    def __repr__(self) -> str:
        return f"Subject({super().__repr__()})"

    def __hash__(self) -> int:
        return super().__hash__()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Subject):
            raise TypeError(f"Subject can only compare with Subject, not {type(other)}")
        return (
            self.type == "*"
            or other.type in {self.type, "*"}
            and (self.id == "*" or other.id in {self.id, "*"})
        )

    @classmethod
    def __get_validators__(cls) -> Generator[Callable[..., Self], None, None]:
        yield cls.validate

    @classmethod
    def validate(cls, value: str) -> Self:
        if not isinstance(value, str):
            raise TypeError("string required")
        type, _, id = value.partition(":")
        return cls(type, id)


T_SubjectExtractor = _DependentCallable[Subject]

_extractors: set[Dependent[Subject]] = set()


def register_extractor(extractor: T_SubjectExtractor) -> T_SubjectExtractor:
    """注册主体提取器"""
    _extractors.add(
        Dependent[Subject].parse(
            call=extractor,
            allow_types=EVENT_PCS_PARAMS,
        )
    )
    return extractor


async def extractor_subjects(bot: Bot, event: Event) -> set[Subject]:
    async with AsyncExitStack() as stack:
        coros = [
            run_coro_with_catch(
                extractor(
                    bot=bot,
                    event=event,
                    stack=stack,
                    dependency_cache={},
                ),
                (SkippedException,),
            )
            for extractor in _extractors
        ]
        try:
            subjects = await asyncio.gather(*coros)
        except Exception as e:
            logger.opt(colors=True, exception=e).error(
                "<r><bg #f8bbd0>提取主体时出现意外错误</bg #f8bbd0></r>",
            )
            raise
        else:
            return {subject for subject in subjects if subject}
    raise RuntimeError("unreachable")


EventSubjects = Annotated[set[Subject], Depends(extractor_subjects)]
"""事件主体集合"""


@register_extractor
def extract_bot(bot: Bot) -> Subject:
    return Subject("bot", bot.self_id)


@register_extractor
def extract_user(event: MessageEvent) -> Subject:
    return Subject("user", event.user_id)


@register_extractor
def extract_group(event: GroupMessageEvent) -> Subject:
    return Subject("group", event.group_id)
