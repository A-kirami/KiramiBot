"""本模块提供了多种资源管理工具"""

import os
import random
import secrets
import tempfile
from abc import ABC, abstractmethod
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, ClassVar

from flowery import Imager
from typing_extensions import Self

from kirami.config import AUDIO_DIR, FONT_DIR, IMAGE_DIR, RES_DIR, VIDEO_DIR
from kirami.exception import ResourceError, WriteFileError
from kirami.message import MessageSegment


class BaseResource:
    __root__: ClassVar[Path] = RES_DIR
    """资源根目录"""
    __format__: ClassVar[set[str]] = set()
    """支持的文件格式"""

    __slots__ = ("_path",)

    def __init__(self, path: str | Path | Self) -> None:
        self._path = path.path if isinstance(path, BaseResource) else Path(path)
        if not self._path.is_absolute():
            self._path = self.__root__ / self._path

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(path={self.path})"

    def __truediv__(self, other: str | Path) -> Self:
        return self.__class__(self.path / other)

    def __iter__(self) -> Generator[Self, None, None]:
        for path in self.path.iterdir():
            if not self.__format__ or path.suffix in self.__format__:
                yield self.__class__(path)

    def __getitem__(self, format: str) -> Generator[Self, None, None]:
        format_ = format.lower().removeprefix(".")
        for res in self:
            if res.suffix == format_:
                yield res

    @property
    def path(self) -> Path:
        """资源路径"""
        return self._path

    @property
    def name(self) -> str:
        """资源名称"""
        return self._path.name

    @property
    def suffix(self) -> str:
        """资源后缀名"""
        return self._path.suffix

    @property
    def stem(self) -> str:
        """资源名称(无后缀)"""
        return self._path.stem

    def is_file(self) -> bool:
        """此资源是否为常规文件"""
        return self.path.is_file()

    def is_dir(self) -> bool:
        """此资源是否为目录"""
        return self.path.is_dir()

    def exists(self) -> bool:
        """该资源是否存在"""
        return self.path.exists()

    def as_uri(self) -> str:
        """将路径返回为文件 URI"""
        return self.path.as_uri()

    def search(
        self, pattern: str, recursion: bool = False
    ) -> Generator[Self, None, None]:
        """搜索所有匹配的资源。

        ### 参数
            pattern: 搜索模式

            recursion: 是否递归搜索

        ### 生成
            匹配的资源
        """
        searcher = self.path.rglob if recursion else self.path.glob
        for path in searcher(pattern):
            yield self.__class__(path)

    def choice(self) -> Self:
        """随机抽取一个资源"""
        return secrets.choice(list(self))

    def random(self, num: int = 1) -> list[Self]:
        """随机抽取指定数量的资源。

        ### 参数
            num: 抽取数量，默认为1

        ### 返回
            抽取的资源列表
        """
        return random.sample(list(self), num)

    def save(self, file: str | bytes) -> None:
        """保存文件。

        ### 参数
            file: 要保存的文件

        ### 异常
            WriteFileError: 资源不是有效的文件路径
        """
        if self.is_dir():
            raise WriteFileError(f"资源不是有效的文件路径: {self.path}")
        if isinstance(file, str):
            self.path.write_text(file, encoding="utf-8")
        else:
            self.path.write_bytes(file)

    def delete(self) -> None:
        """删除资源"""
        self.path.unlink()

    def move(self, target: str | Path) -> None:
        """移动资源。

        ### 参数
            target: 目标路径
        """
        self._path = self.path.rename(target)

    def rename(self, name: str) -> None:
        """重命名资源。

        ### 参数
            name: 新名称
        """
        self._path = self.path.rename(self.path.parent / name)

    @classmethod
    def add_format(cls, format: str) -> None:
        """添加支持的资源类型。

        ### 参数
            format: 资源类型后缀名
        """
        format_ = format.lower().removeprefix(".")
        cls.__format__.add(f".{format_}")


class MessageMixin(ABC):
    @abstractmethod
    def message(self) -> MessageSegment:
        """将资源文件转换为 `MessageSegment` 对象"""
        raise NotImplementedError


class OpenMixin(ABC):
    @abstractmethod
    def open(self) -> Any:
        """打开资源文件"""
        raise NotImplementedError


class Image(BaseResource, OpenMixin, MessageMixin):
    __root__: ClassVar[Path] = IMAGE_DIR
    __format__: ClassVar[set[str]] = {
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".webp",
        ".avif",
        ".svg",
    }

    def open(self) -> Imager:
        try:
            return Imager.open(self.path)
        except Exception as e:
            raise ResourceError(f"无法打开图片: {self.path}") from e

    def message(self, *args, **kwargs) -> MessageSegment:
        return MessageSegment.image(self.path, *args, **kwargs)


class Font(BaseResource):
    __root__: ClassVar[Path] = FONT_DIR
    __format__: ClassVar[set[str]] = {
        ".ttf",
        ".ttc",
        ".otf",
        ".otc",
        ".woff",
        ".woff2",
    }


class Audio(BaseResource, MessageMixin):
    __root__: ClassVar[Path] = AUDIO_DIR
    __format__: ClassVar[set[str]] = {
        ".wav",
        ".flac",
        ".ape",
        ".alac",
        ".mp3",
        ".aac",
        ".ogg",
    }

    def message(self, *args, **kwargs) -> MessageSegment:
        return MessageSegment.record(self.path, *args, **kwargs)


class Video(BaseResource, MessageMixin):
    __root__: ClassVar[Path] = VIDEO_DIR
    __format__: ClassVar[set[str]] = {
        ".avi",
        ".wmv",
        ".mpeg",
        ".mp4",
        ".m4v",
        ".mov",
        ".mkv",
        ".flv",
        ".f4v",
        ".webm",
    }

    def message(self, *args, **kwargs) -> MessageSegment:
        return MessageSegment.video(self.path, *args, **kwargs)


class Resource(BaseResource):
    @staticmethod
    def audio(path: str | Path | Audio) -> Audio:
        """音频资源。

        ### 参数
            path: 资源路径
        """
        return Audio(path)

    @staticmethod
    def font(path: str | Path | Font) -> Font:
        """字体资源。

        ### 参数
            path: 资源路径
        """
        return Font(path)

    @staticmethod
    def image(path: str | Path | Image) -> Image:
        """图像资源。

        ### 参数
            path: 资源路径
        """
        return Image(path)

    @staticmethod
    def video(path: str | Path | Video) -> Video:
        """视频资源。

        ### 参数
            path: 资源路径
        """
        return Video(path)

    @classmethod
    @contextmanager
    def tempfile(
        cls, suffix: str | None = None, prefix: str | None = None, text: bool = False
    ) -> Generator[Self, None, None]:
        """创建临时文件。

        ### 参数
            suffix: 后缀名。如果 suffix 不是 None 则文件名将以该后缀结尾，是 None 则没有后缀

            prefix: 前缀名。如果 prefix 不是 None，则文件名将以该前缀开头，是 None 则使用默认前缀。默认前缀是 `gettempprefix()` 或 `gettempprefixb()` 函数的返回值（自动调用合适的函数）

            text: 是否文本文件。如果 text 为 True，文件会以文本模式打开，否则以二进制模式打开

        ### 生成
            临时文件
        """
        fp, path = tempfile.mkstemp(suffix=suffix, prefix=prefix, text=text)
        os.close(fp)
        file = cls(path)
        try:
            yield file
        finally:
            file.delete()

    @classmethod
    @contextmanager
    def tempdir(
        cls, suffix: str | None = None, prefix: str | None = None
    ) -> Generator[Self, None, None]:
        """创建临时目录。

        ### 参数
            suffix: 后缀名。如果 suffix 不是 None 则文件名将以该后缀结尾，是 None 则没有后缀

            prefix: 前缀名。如果 prefix 不是 None，则文件名将以该前缀开头，是 None 则使用默认前缀。默认前缀是 `gettempprefix()` 或 `gettempprefixb()` 函数的返回值（自动调用合适的函数）

        ### 生成
            临时目录
        """
        with tempfile.TemporaryDirectory(
            suffix=suffix, prefix=prefix, ignore_cleanup_errors=True
        ) as tmpdir:
            yield cls(tmpdir)
