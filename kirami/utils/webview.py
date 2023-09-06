import secrets
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar

from fastapi import HTTPException
from fastapi.staticfiles import StaticFiles
from yarl import URL

from kirami.server import BASE_URL, Server

from .utils import get_path

if TYPE_CHECKING:
    from fastapi import FastAPI


class WebView:
    base: ClassVar[str] = "/webview"
    data: ClassVar[dict[str, Any]] = {}

    def __init__(self, path: str, mount: str | Path) -> None:
        """创建网页视图。

        ### 参数
            path: 视图路径

            mount: 挂载的视图文件夹路径。如果是相对路径，则相对于当前目录
        """
        if not path or not path.startswith("/"):
            raise ValueError("Routed paths must start with '/'")

        self.route = self.base + path
        app: "FastAPI" = Server.get_app()
        app.mount(
            self.route,
            StaticFiles(directory=get_path(mount, depth=1), html=True),
            path.removeprefix("/"),
        )

    def render(self, path: str, **kwargs) -> URL:
        """渲染视图。

        ### 参数
            path: 视图路径

            **kwargs: 传递给视图的数据

        ### 返回
            带有数据的视图链接
        """
        data_id = self.generate_id()
        self.data[data_id] = kwargs
        data_url = self.get_data_url(data_id)
        view_url = self.get_view_url(path)
        return view_url.with_query(data_url=str(data_url))

    def get_view_url(self, path: str) -> URL:
        """获取视图链接。

        ### 参数
            path: 视图路径
        """
        if not path or not path.startswith("/"):
            raise ValueError("Routed paths must start with '/'")
        return BASE_URL.with_path(self.route + path)

    @classmethod
    def get_data_url(cls, data_id: str) -> URL:
        """获取数据链接。

        ### 参数
            data_id: 数据标识符
        """
        return BASE_URL / "viewdata" / data_id

    @staticmethod
    def generate_id() -> str:
        """生成标识符"""
        return secrets.token_urlsafe(16)


app = Server.get_router("/viewdata", tags=["webview"])


@app.get("/{data_id}")
async def get_data(data_id: str) -> dict[str, Any]:
    """获取视图数据"""
    if data := WebView.data.pop(data_id, None):
        return data
    raise HTTPException(status_code=404, detail="Data not found")
