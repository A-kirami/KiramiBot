"""本模块用于定义 API 路由"""

from kirami.version import __version__

from .server import Server

api = Server.get_router("api", tags=["API"])


@api.get("/version", summary="获取版本信息")
def get_version() -> dict:
    """
    获取版本信息
    """
    return {
        "version": __version__,
    }
