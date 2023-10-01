import asyncio
import inspect
import json
from collections.abc import Callable, Coroutine
from datetime import datetime, time, timedelta, tzinfo
from functools import wraps
from io import BytesIO
from pathlib import Path
from typing import Any, Literal, ParamSpec, TypeVar, overload

import arrow
import yaml
from arrow import Arrow
from flowery import Imager
from httpx import Response
from httpx._types import QueryParamTypes, RequestData
from nonebot.adapters.onebot.v11.utils import escape as escape
from nonebot.adapters.onebot.v11.utils import unescape as unescape
from PIL import Image as PILImg
from tenacity import AsyncRetrying, RetryError, stop_after_attempt

from kirami.config import BOT_DIR, RES_DIR
from kirami.exception import (
    FileNotExistError,
    FileTypeError,
    NetworkError,
    ReadFileError,
)

from .renderer import Renderer
from .request import Request
from .webwright import WebWright

try:  # pragma: py-gte-311
    import tomllib  # pyright: ignore[reportMissingImports]
except ModuleNotFoundError:  # pragma: py-lt-311
    import tomli as tomllib

R = TypeVar("R")
"""返回值泛型。"""

P = ParamSpec("P")
"""参数泛型"""


def get_path(file: str | Path, *, depth: int = 0) -> Path:
    """获取文件或目录的绝对路径。

    ### 参数
        file: 文件或目录路径，如果为相对路径，则相对于当前调用者所在文件(即 `__file__`)的父目录

        depth: 调用栈深度。默认为 0，即当前函数调用栈的深度
    """
    if Path(file).is_absolute():
        path = Path(file)
    else:
        path = Path(inspect.stack()[depth + 1].filename).parent / file

    return path.resolve()


def load_data(file: str | Path) -> dict[str, Any]:
    """读取文件数据。

    支持的文件格式有：`json`、`yaml`、`toml`。

    ### 参数
        file: 文件路径，如果为相对路径，则相对于当前文件的父目录

    ### 返回
        解析后的数据

    ### 异常
        FileNotExistError: 文件不存在

        FileTypeError: 文件格式不支持

        ReadFileError: 文件内容为空
    """
    data_path = get_path(file, depth=1)
    if not data_path.exists():
        raise FileNotExistError(f"找不到文件: {data_path}")

    data = data_path.read_text(encoding="utf-8")
    file_type = data_path.suffix.removeprefix(".")
    if file_type == "json":
        file_data = json.loads(data)
    elif file_type in ("yml", "yaml"):
        file_data = yaml.safe_load(data)
    elif file_type == "toml":
        file_data = tomllib.loads(data)
    else:
        raise FileTypeError(f"不支持的文件类型: {file_type}, 只能是 json、yaml 或 toml")

    if file_data is None:
        raise ReadFileError(f"文件内容为空: {data_path}")

    return file_data


def new_dir(path: str | Path, root: str | Path = BOT_DIR) -> Path:
    """创建一个新的目录。

    ### 参数
        path: 新目录的路径

        root: 相对于新目录的根目录。默认为 bot 根目录

    ### 返回
        新目录的绝对路径
    """
    root = Path(root)

    if root.is_file():
        raise RuntimeError("root 应该是一个目录, 而不是一个文件")

    dir_ = root / path
    dir_.mkdir(parents=True, exist_ok=True)

    return dir_.resolve()


def is_file_path(path: str | Path) -> bool:
    """判断是否是一个有效的文件路径。

    ### 参数
        path: 文件路径
    """
    try:
        return Path(path).is_file()
    except OSError:
        return False


def str_of_size(size: int) -> str:
    """将字节大小转换为带单位的字符串。

    ### 参数
        size: 字节大小

    ### 异常
        ValueError: 参数 `size` 小于0
    """
    if size < 0:
        raise ValueError("size 不能小于0")
    if size < 1024:  # noqa: PLR2004
        return f"{size:.2f} B"
    if size < 1024**2:
        return f"{size / 1024:.2f} KB"
    if size < 1024**3:
        return f"{size / 1024 ** 2:.2f} MB"
    if size < 1024**4:
        return f"{size / 1024 ** 3:.2f} GB"
    if size < 1024**5:
        return f"{size / 1024 ** 4:.2f} TB"
    return f"{size / 1024 ** 5:.2f} PB"


def singleton(cls: Callable[P, R]) -> Callable[P, R]:
    """单例模式装饰器"""
    _instance: dict[Callable[P, R], Any] = {}

    @wraps(cls)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        if cls not in _instance:
            _instance[cls] = cls(*args, **kwargs)
        return _instance[cls]

    return wrapper


def awaitable(func: Callable[P, R]) -> Callable[P, Coroutine[Any, Any, R]]:
    """同步转异步装饰器"""

    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        return await asyncio.to_thread(func, *args, **kwargs)

    return wrapper


async def get_pic(
    url: str,
    size: tuple[int, int] | int | None = None,
    convert: Literal["RGBA", "RGB", "L"] = "RGBA",
    **kwargs,
) -> Imager:
    """从网络获取图片，格式化为指定尺寸的指定图像模式。

    ### 参数
        url：图片链接

        size：调整尺寸大小

        convert：转换图像模式

        **kwargs：传递给 `Request.get` 的关键字参数
    """
    resp = await Request.get(url, stream=True, **kwargs)
    if resp.is_error:
        raise NetworkError("获取图片失败")
    pic = Imager.open(BytesIO(resp.content))
    if convert:
        pic = pic.convert(convert)
    if size:
        pic = pic.resize(size, PILImg.LANCZOS)
    return pic


async def tpl2img(
    tpl: str | Path,
    *,
    data: dict[str, Any] | None = None,
    base_path: str | Path | None = None,
    width: int = 480,
    device_scale_factor: int | float = 1,
    **kwargs,
) -> bytes:
    """将 jinja2 模板转换为图片。

    ### 参数
        tpl: 模板字符串或文件路径

        data: 模板渲染所需的数据

        base_path: 模板文件中的相对路径的根目录

        width: 图片宽度

        device_scale_factor: 设备缩放因子

        **kwargs: 传递给 `html2pic` 的关键字参数

    ### 返回
        图片的二进制数据
    """
    html = await Renderer.template(tpl, **(data or {}))
    if not base_path and isinstance(tpl, Path):
        base_path = Path(tpl).parent
    return await html2pic(
        html, base_path, width=width, device_scale_factor=device_scale_factor, **kwargs
    )


async def md2img(
    md: str | Path,
    *,
    theme: Literal["light", "dark"] = "light",
    highlight: str | None = "auto",
    extra: str = "",
    base_path: str | Path | None = None,
    width: int = 480,
    device_scale_factor: int | float = 1,
    **kwargs,
) -> bytes:
    """将 markdown 转换为图片。

    ### 参数
        md: markdown 字符串或文件路径

        theme: 主题，可选值为 "light" 或 "dark"，默认为 "light"

        highlight: 代码高亮主题，可选值为 "auto" 或 pygments 支持的主题，默认为 "auto"

        extra: 额外的 head 标签内容，可以是 meta 标签、link 标签、script 标签、style 标签等

        base_path: markdown 文件中的相对路径的根目录

        width: 图片宽度

        device_scale_factor: 设备缩放因子

        **kwargs: 传递给 `html2pic` 的关键字参数

    ### 返回
        图片的二进制数据
    """
    html = await Renderer.markdown(md, theme, highlight, extra)
    if not base_path and isinstance(md, Path):
        base_path = Path(md).parent
    return await html2pic(
        html, base_path, width=width, device_scale_factor=device_scale_factor, **kwargs
    )


async def html2pic(
    html: str,
    /,
    base_path: str | Path | None = None,
    *,
    width: int = 1280,
    wait_until: Literal[
        "commit", "domcontentloaded", "load", "networkidle"
    ] = "networkidle",
    wait: int | float = 0,
    device_scale_factor: int | float = 1,
    locator: str | None = None,
    **kwargs,
) -> bytes:
    """将网页转换为图片。

    ### 参数
        html: 网页文本

        base_path: 网页中的相对路径的根目录

        width: 网页宽度，单位为像素

        wait_until: 等待网页加载的事件，可选值为 "commit"、"domcontentloaded"、"load"、"networkidle"

        wait: 等待网页加载的时间，单位为毫秒

        device_scale_factor: 设备缩放因子

        locator: 网页中的元素定位器，如果指定了该参数，则只截取该元素的图像

        **kwargs: 传递给 `playwright.async_api.Page.screenshot` 的关键字参数

    ### 返回
        图片的二进制数据
    """
    base_path = Path(base_path) if base_path else RES_DIR
    async with WebWright.new_page(
        viewport={"width": width, "height": 1}, device_scale_factor=device_scale_factor
    ) as page:
        await page.goto(base_path.absolute().as_uri())
        await page.set_content(html, wait_until=wait_until)
        await page.wait_for_timeout(wait)
        if locator:
            return await page.locator(locator).screenshot(**kwargs)
        return await page.screenshot(full_page=True, **kwargs)


@overload
async def get_api_data(
    url: str,
    params: QueryParamTypes | None = None,
    data: RequestData | None = None,
    retry: int = 3,
    to_json: Literal[True] = True,
    **kwargs,
) -> Any:
    ...


@overload
async def get_api_data(
    url: str,
    params: QueryParamTypes | None = None,
    data: RequestData | None = None,
    retry: int = 3,
    to_json: Literal[False] = False,
    **kwargs,
) -> Response:
    ...


async def get_api_data(
    url: str,
    params: QueryParamTypes | None = None,
    data: RequestData | None = None,
    retry: int = 3,
    to_json: bool = True,
    **kwargs,
) -> Response | Any:
    """请求 API 获取数据。

    ### 参数
        url: API 地址

        params: get 请求参数

        data: post 请求数据

        retry: 重试次数

        to_json: 是否将结果转换为 json

    ### 返回
        API 请求结果

    ### 异常
        NetworkError: API 请求失败
    """
    try:
        async for attempt in AsyncRetrying(stop=stop_after_attempt(retry)):
            with attempt:
                if data:
                    result = await Request.post(url, data=data, params=params, **kwargs)
                else:
                    result = await Request.get(url, params=params, **kwargs)
                if result.is_error:
                    raise NetworkError(f"{result.status_code}")

                return result.json() if to_json else result
    except RetryError as e:
        raise NetworkError("API 请求失败") from e


def human_readable_time(seconds: int) -> str:
    """将给定的秒数转换为易读的时间格式。

    ### 参数
        seconds: 要转换的秒数

    ### 返回
        转换后的时间字符串，格式为 "X小时Y分Z秒"
    """
    seconds = max(seconds, 0)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)

    time_string = ""

    if hours:
        time_string += f"{hours}小时"
    if minutes:
        time_string += f"{minutes}分"
    if seconds or not time_string:
        time_string += f"{seconds}秒"

    return time_string


def get_shift_now(
    year: int = 0,
    month: int = 0,
    day: int = 0,
    hour: int = 0,
    minute: int = 0,
    second: int = 0,
    **kwargs: Any,
) -> datetime:
    """从当前时间推移一定时间

    ### 参数
        year: 推移的年数

        month: 推移的月数

        day: 推移的天数

        hour: 推移的小时数

        minute: 推移的分钟数

        second: 推移的秒数

        **kwargs: 其他关键字参数，参考 `arrow.arrow.Arrow.shift` 的参数

    ### 返回
        推移后的 `datetime` 对象
    """
    now = arrow.now()
    shift_date = now.shift(
        years=year,
        months=month,
        days=day,
        hours=hour,
        minutes=minute,
        seconds=second,
        **kwargs,
    )
    return shift_date.datetime


def get_daily_datetime(datetime_time: time) -> datetime:
    """返回今天指定时间的 `datetime` 对象，如果当前时间已经过了指定时间，则返回明天的 `datetime` 对象。

    ### 参数
        datetime_time: 指定的时间，类型为 `datetime.time` 对象

    ### 返回
        今天或明天的指定时间 `datetime` 对象
    """
    current_datetime = datetime.now()
    daily_datetime = datetime.combine(current_datetime, datetime_time)

    if current_datetime > daily_datetime:
        daily_datetime = datetime.combine(
            current_datetime + timedelta(days=1), datetime_time
        )

    return daily_datetime.astimezone()


def get_humanize_time(
    time: Arrow | datetime | str | float, tzinfo: tzinfo | None = None, **kwargs
) -> str:
    """将时间转换为易读的时间格式。

    ### 参数
        time: 要转换的时间

        tzinfo: 时区信息

        **kwargs: 其他关键字参数，参考 `arrow.arrow.Arrow.shift` 的参数
    """
    raw_time = arrow.get(time, tzinfo=tzinfo) if tzinfo else arrow.get(time)
    current_time = arrow.now(tz=tzinfo)
    shift_time = {key: -abs(value) for key, value in kwargs.items()} or {"days": -1}
    threshold_time = current_time.shift(**shift_time)
    if raw_time < threshold_time:
        return raw_time.format("YYYY-MM-DD HH:mm:ss")
    return raw_time.humanize(locale="zh-CN")
