"""本模块定义了网络服务器"""

import inspect
from enum import Enum
from typing import Any, ClassVar

import nonebot
from fastapi import APIRouter
from fastapi.middleware.cors import CORSMiddleware
from yarl import URL

from kirami.config import bot_config, server_config
from kirami.log import logger

BASE_URL = URL(f"http://{bot_config.host}:{bot_config.port}")


class Server:
    _routers: ClassVar[dict[str, APIRouter]] = {}

    @classmethod
    def init(cls) -> None:
        """初始化服务器"""
        app = cls.get_app()
        if cls._routers:
            # 添加 API 路由对象
            for prefix, router in cls._routers.items():
                app.include_router(router)
                logger.opt(colors=True).debug(
                    f'API Router "<e>{prefix}</e>" registered.'
                )

            # 添加 CORS 跨域中间件
            if server_config.allow_cors:
                app.add_middleware(
                    CORSMiddleware, **server_config.dict(exclude={"allow_cors"})
                )

            cls._routers.clear()

        if bot_config.debug:
            config = nonebot.get_driver().config
            logger.debug(
                f"API Docs Url is {BASE_URL.with_path(config.fastapi_docs_url)}"
            )

    @classmethod
    def get_app(cls) -> Any:
        """获取全局 Server App 对象"""
        return nonebot.get_app()

    @classmethod
    def get_router(
        cls, route: str | None = None, tags: list[str | Enum] | None = None, **kwargs
    ) -> APIRouter:
        """获取 API 路由对象。

        ### 参数
            route: 路由前缀，不填写则自动获取模块名。默认为 None

            tags: 路由标签，不填写则与前缀相同。默认为 None

            **kwargs: APIRouter 参数

        ### 返回
            API 路由对象
        """

        if route is None:
            prefix = inspect.currentframe().f_back.f_globals["__name__"].split(".")[-1]  # type: ignore
        else:
            prefix = route.strip("/")

        if tags is None:
            tags = [prefix]

        router = APIRouter(prefix=f"/{prefix}", tags=tags, **kwargs)

        cls._routers[router.prefix] = router

        return router
