from collections.abc import Iterable
from pathlib import Path
from typing import NamedTuple
from urllib.parse import urlparse

import filetype
from loguru import logger
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    Task,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
from rich.table import Table

from .request import Request


class File(NamedTuple):
    """文件信息"""

    path: Path
    """路径"""
    name: str
    """文件名"""
    extension: str
    """文件扩展名"""
    size: int
    """文件大小"""


class DownloadProgress(Progress):
    """下载进度条"""

    STATUS_DL = TextColumn("[blue]Downloading...")
    STATUS_FIN = TextColumn("[green]Complete!")
    STATUS_ROW = (
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%", justify="center"),
        TimeRemainingColumn(compact=True),
    )
    PROG_ROW = (DownloadColumn(binary_units=True), BarColumn(), TransferSpeedColumn())

    def make_tasks_table(self, tasks: Iterable[Task]) -> Table:
        table = Table.grid(padding=(0, 1), expand=self.expand)
        for task in tasks:
            if task.visible:
                status = self.STATUS_FIN if task.finished else self.STATUS_DL
                itable = Table.grid(padding=(0, 1), expand=self.expand)
                itable.add_row(*(column(task) for column in [status, *self.STATUS_ROW]))
                itable.add_row(*(column(task) for column in self.PROG_ROW))
                table.add_row(Panel(itable, title=task.description, title_align="left"))
        return table


class Downloader:
    @classmethod
    async def download_file(
        cls,
        url: str,
        path: str | Path,
        *,
        file_name: str | None = None,
        file_type: str | None = None,
        chunk_size: int | None = None,
        **kwargs,
    ) -> File:
        """下载文件并保存到本地。

        ### 参数
            url: 文件的下载链接

            path: 文件的保存路径，可以是文件夹或者文件路径。如果是文件夹，则自动获取文件名，如果是文件路径，则使用指定的文件名

            file_name: 文件名。不指定则自动获取文件名，优先从 `path` 中获取，如果 `path` 中没有文件名，则从 `url` 中获取

            file_type: 文件类型。不指定则自动识别文件类型，优先从 `path` 中获取，如果 `path` 中没有文件类型，则从 `url` 中获取

            chunk_size: 指定文件下载的分块大小，不指定则不进行分块下载，如果文件大小大于 3M，则自动使用分块下载

            **kwargs: 传递给 `request.Request.stream` 的参数

        ### 返回
            `File` 对象
        """
        path = Path(path)
        if path.suffix:
            file_name = file_name or path.stem
            path = path.parent

        url_file = Path(urlparse(url).path)
        if url_file.suffix:
            file_name = file_name or url_file.stem

        if not file_name:
            raise ValueError("没有找到文件名")

        path.mkdir(parents=True, exist_ok=True)

        async with Request.stream("GET", url, **kwargs) as response:
            file_extension = file_type or path.suffix or url_file.suffix
            if content_type := filetype.get_type(response.headers["Content-Type"]):
                file_extension = file_extension or content_type.extension
            if not file_extension:
                raise ValueError(f"{url} 无法确定文件类型")
            file_extension = file_extension.split(".")[-1]

            file_size = int(response.headers["Content-Length"])
            if file_size > 1024**2 * 3 and not chunk_size:
                chunk_size = 1024 * 4

            file = f"{file_name}.{file_extension}"
            file_path = path / file

            logger.debug(f'开始下载 "{file}", 下载地址: {url}')

            with file_path.open("wb") as f, DownloadProgress() as progress:
                download_task = progress.add_task(file, total=file_size)
                async for data in response.aiter_bytes(chunk_size):
                    f.write(data)
                    progress.update(
                        download_task, completed=response.num_bytes_downloaded
                    )

            logger.debug(f'"{file}" 下载完成, 保存路径: {file_path.absolute()}')

        return File(file_path, file_name, file_extension, file_size)
