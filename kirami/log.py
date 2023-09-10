"""本模块调整了日志的显示效果，并将其保存到本地文件"""

import builtins
import logging
import re
from collections.abc import Callable
from functools import wraps
from typing import TYPE_CHECKING, Any, ClassVar, Literal, TypeAlias, get_args

import loguru
import nonebot
import rich
from loguru._file_sink import FileSink
from loguru._handler import Message
from loguru._logger import Core, Logger
from nonebot.log import LoguruHandler as LoguruHandler
from rich.columns import Columns as Columns
from rich.console import Console
from rich.logging import RichHandler
from rich.markdown import Markdown as Markdown
from rich.markup import escape
from rich.panel import Panel as Panel
from rich.progress import Progress as Progress
from rich.table import Table as Table
from rich.text import Text as Text
from rich.theme import Theme
from rich.traceback import install

from kirami.config import LOG_DIR, bot_config, log_config

if TYPE_CHECKING:
    from loguru import Logger as LoggerType
    from loguru import Record

# ruff: noqa: ANN001

logger: "LoggerType" = loguru.logger
"""KiramiBot 日志记录器对象"""

LevelName: TypeAlias = Literal[
    "TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"
]

suppress = () if bot_config.debug else (nonebot,)

install(width=None, suppress=suppress, show_locals=bot_config.debug)

builtins.print = rich.print

for lv in Core().levels.values():
    logging.addLevelName(lv.no, lv.name)


color_dict = {
    "k": "black",
    "e": "blue",
    "c": "cyan",
    "g": "green",
    "m": "magenta",
    "r": "red",
    "w": "white",
    "y": "yellow",
}

style_dict = {
    "b": "bold",
    "d": "dim",
    "n": "normal",
    "i": "italic",
    "u": "underline",
    "s": "strike",
    "v": "reverse",
    "l": "blink",
    "h": "hide",
}


def tag_convert(match: re.Match[str]) -> str:
    """loguru 标签转写 rich 标签"""

    def get_color(color: str) -> str:
        if color.isnumeric():
            return f"color({color})"
        return f"rgb({color})" if "," in color else color

    markup: str = match[0]
    tag: str = match[1]
    is_forecolor = tag.islower()
    tag = tag.lower()
    is_brightcolor = tag.startswith("light")
    tag = tag.removeprefix("light-")

    if len(tag) == 2:  # noqa: PLR2004
        tag = tag[:-1]

    match tag.split(" "):
        case [abbr] if abbr in color_dict:
            color = color_dict.get(abbr, "")
            if is_brightcolor:
                color = f"bright_{color}"
            _type = color if is_forecolor else f"on {color}"
        case [abbr] if abbr in style_dict:
            _type = style_dict.get(abbr, "")
        case ["fg", color]:
            _type = get_color(color)
        case ["bg", color]:
            _type = f"on {get_color(color)}"
        case _:
            _type = tag

    return markup.replace("<", "[").replace(">", "]").replace(match[1], _type)


def handle_log(func) -> Callable[..., None]:
    """将 loguru 的样式标记转换为 rich 的样式标记"""

    @wraps(func)
    def wrapper(
        self,
        level,
        from_decorator,
        options,
        message,
        args,
        kwargs,
    ) -> None:
        (exception, depth, record, lazy, colors, *_, extra) = options
        if colors:
            extra["colorize"] = True
            message = re.compile(r"(?<!\\)</?((?:[fb]g\s)?[^<>\s]*)>").sub(
                tag_convert, message
            )
        else:
            message = escape(message)
        options = (exception, depth + 1, record, lazy, False, *_, extra)
        return func(
            self,
            level,
            from_decorator,
            options,
            message,
            args,
            kwargs,
        )

    return wrapper


Logger._log = handle_log(Logger._log)


def handle_write(func) -> Callable[..., None]:
    """清洗日志中的 rich 样式标记"""

    @wraps(func)
    def wrapper(self, message) -> None:
        record = message.record
        extra = record.get("extra", {})
        if extra.get("colorize"):
            message = Message(re.sub(r"(\\*)(\[[a-z#/@][^[]*?])", "", message))
            message.record = record
        return func(self, message)

    return wrapper


FileSink.write = handle_write(FileSink.write)


custom_theme = Theme(
    {
        "log.time": "cyan",
        "logging.level.debug": "blue",
        "logging.level.info": "",
        "logging.level.warning": "yellow",
        "logging.level.success": "bright_green",
        "logging.level.trace": "bright_black",
    },
)

console = Console(theme=custom_theme)

handler = RichHandler(
    console=console,
    show_path=False,
    omit_repeated_times=False,
    markup=True,
    rich_tracebacks=True,
    tracebacks_show_locals=bot_config.debug,
    tracebacks_suppress=suppress,
    log_time_format="%m-%d %H:%M:%S",
)


class LogFilter:
    level: ClassVar[LevelName | int] = (
        "DEBUG" if bot_config.debug else bot_config.log_level
    )

    def __call__(self, record: "Record") -> bool:
        level = record["extra"].get("filter_level") or self.level
        levelno = level if isinstance(level, int) else logger.level(level).no
        return record["level"].no >= levelno


LOG_CONFIG = {
    "rotation": "00:00",
    "enqueue": True,
    "encoding": "utf-8",
    "retention": f"{log_config.log_expire_timeout} days",
}


def file_handler(levels: LevelName | tuple[LevelName, ...]) -> list[dict[str, Any]]:
    if not isinstance(levels, tuple):
        level_names = get_args(LevelName)
        minimum = level_names.index(levels)
        levels = level_names[minimum:]
    return [
        {
            "sink": LOG_DIR / level.lower() / "{time:YYYY-MM-DD}.log",
            "level": level,
            **LOG_CONFIG,
        }
        for level in levels
    ]


logger.remove()
logger.configure(
    handlers=[
        {
            "sink": handler,
            "level": 0,
            "colorize": False,
            "diagnose": False,
            "backtrace": True,
            "filter": LogFilter(),
            "format": lambda _: "[light_slate_blue bold][link={file.path}:{line}]{name}[/][/] [dim]|[/] {message}",
        },
        *file_handler(bot_config.log_file),
    ]
)


def new_logger(
    name: str, *, filter_level: LevelName | int | None = None
) -> "LoggerType":
    """创建新的日志记录器。

    ### 参数
        name: 日志名称

        filter_level: 过滤等级，当日志等级大于过滤等级时才会显示
    """
    return logger.patch(lambda record: record.update({"name": name})).bind(
        filter_level=filter_level
    )
