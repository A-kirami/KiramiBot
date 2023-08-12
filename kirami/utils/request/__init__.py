"""
请求
====

将 HTTPX 封装以便更好的使用
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any, Literal

import httpx
from httpx import Response
from httpx._types import (
    CookieTypes,
    HeaderTypes,
    ProxiesTypes,
    QueryParamTypes,
    RequestContent,
    RequestData,
    RequestFiles,
    TimeoutTypes,
    URLTypes,
    VerifyTypes,
)

from kirami.config import bot_config

from .utils import add_user_agent


class Request:
    """
    ## httpx 异步请求封装

    [HTTPX官方文档](https://www.python-httpx.org/)
    """

    @classmethod
    async def get(
        cls,
        url: URLTypes,
        *,
        params: QueryParamTypes | None = None,
        headers: HeaderTypes | None = None,
        cookies: CookieTypes | None = None,
        follow_redirects: bool = True,
        timeout: TimeoutTypes | None = None,
        verify: VerifyTypes = True,
        http2: bool = False,
        proxies: ProxiesTypes | None = None,
        **kwargs,
    ) -> Response:
        """发起 GET 请求。

        ### 参数
            url: 请求地址

            params: 请求参数

            headers: 请求头

            cookies: 请求 Cookie

            follow_redirects: 是否跟随重定向

            timeout: 超时时间，单位: 秒

            verify: 是否验证 SSL 证书

            http2: 是否使用 HTTP/2

            proxies: 代理地址

            **kwargs: 传递给 `httpx.AsyncClient` 的其他参数

        ### 返回
            `httpx.Response` 对象
        """
        async with httpx.AsyncClient(
            verify=verify,
            http2=http2,
            proxies=proxies or bot_config.proxy_url,  # type: ignore
            **kwargs,
        ) as client:
            return await client.get(
                url,
                params=params,
                headers=add_user_agent(headers),
                cookies=cookies,
                follow_redirects=follow_redirects,
                timeout=timeout if timeout is not None else bot_config.http_timeout,
            )

    @classmethod
    async def post(
        cls,
        url: URLTypes,
        *,
        content: RequestContent | None = None,
        data: RequestData | None = None,
        json: RequestContent | None = None,
        files: RequestFiles | None = None,
        params: QueryParamTypes | None = None,
        headers: HeaderTypes | None = None,
        cookies: CookieTypes | None = None,
        follow_redirects: bool = True,
        timeout: TimeoutTypes | None = None,
        verify: VerifyTypes = True,
        http2: bool = False,
        proxies: ProxiesTypes | None = None,
        **kwargs,
    ) -> Response:
        """发起 POST 请求。

        ### 参数
            url: 请求地址

            content: 请求内容

            data: 请求数据

            json: 请求 JSON

            files: 请求文件

            params: 请求参数

            headers: 请求头

            cookies: 请求 Cookie

            follow_redirects: 是否跟随重定向

            timeout: 超时时间，单位: 秒

            verify: 是否验证 SSL 证书

            http2: 是否使用 HTTP/2

            proxies: 代理地址

            **kwargs: 传递给 `httpx.AsyncClient` 的其他参数

        ### 返回
            `httpx.Response` 对象
        """
        async with httpx.AsyncClient(
            verify=verify,
            http2=http2,
            proxies=proxies or bot_config.proxy_url,  # type: ignore
            **kwargs,
        ) as client:
            return await client.post(
                url,
                content=content,
                data=data,
                files=files,
                json=json,
                params=params,
                headers=add_user_agent(headers),
                cookies=cookies,
                follow_redirects=follow_redirects,
                timeout=timeout if timeout is not None else bot_config.http_timeout,
            )

    @classmethod
    async def put(
        cls,
        url: URLTypes,
        *,
        content: RequestContent | None = None,
        data: RequestData | None = None,
        files: RequestFiles | None = None,
        json: Any = None,
        params: QueryParamTypes | None = None,
        headers: HeaderTypes | None = None,
        cookies: CookieTypes | None = None,
        follow_redirects: bool = True,
        timeout: TimeoutTypes | None = None,
        verify: VerifyTypes = True,
        http2: bool = False,
        proxies: ProxiesTypes | None = None,
        **kwargs,
    ) -> Response:
        """发起 PUT 请求。

        ### 参数
            url: 请求地址

            content: 请求内容

            data: 请求数据

            files: 请求文件

            json: 请求 JSON

            params: 请求参数

            headers: 请求头

            cookies: 请求 Cookie

            follow_redirects: 是否跟随重定向

            timeout: 超时时间，单位: 秒

            verify: 是否验证 SSL 证书

            http2: 是否使用 HTTP/2

            proxies: 代理地址

            **kwargs: 传递给 `httpx.AsyncClient` 的其他参数

        ### 返回
            `httpx.Response` 对象
        """
        async with httpx.AsyncClient(
            verify=verify,
            http2=http2,
            proxies=proxies or bot_config.proxy_url,  # type: ignore
            **kwargs,
        ) as client:
            return await client.put(
                url,
                content=content,
                data=data,
                files=files,
                json=json,
                params=params,
                headers=add_user_agent(headers),
                cookies=cookies,
                follow_redirects=follow_redirects,
                timeout=timeout if timeout is not None else bot_config.http_timeout,
            )

    @classmethod
    async def delete(
        cls,
        url: URLTypes,
        *,
        params: QueryParamTypes | None = None,
        headers: HeaderTypes | None = None,
        cookies: CookieTypes | None = None,
        follow_redirects: bool = True,
        timeout: TimeoutTypes | None = None,
        verify: VerifyTypes = True,
        http2: bool = False,
        proxies: ProxiesTypes | None = None,
        **kwargs,
    ) -> Response:
        """发起 DELETE 请求。

        ### 参数
            url: 请求地址

            params: 请求参数

            headers: 请求头

            cookies: 请求 Cookie

            follow_redirects: 是否跟随重定向

            timeout: 超时时间，单位: 秒

            verify: 是否验证 SSL 证书

            http2: 是否使用 HTTP/2

            proxies: 代理地址

            **kwargs: 传递给 `httpx.AsyncClient` 的其他参数

        ### 返回
            `httpx.Response` 对象
        """
        async with httpx.AsyncClient(
            verify=verify,
            http2=http2,
            proxies=proxies or bot_config.proxy_url,  # type: ignore
            **kwargs,
        ) as client:
            return await client.delete(
                url,
                params=params,
                headers=add_user_agent(headers),
                cookies=cookies,
                follow_redirects=follow_redirects,
                timeout=timeout if timeout is not None else bot_config.http_timeout,
            )

    @classmethod
    async def patch(
        cls,
        url: URLTypes,
        *,
        content: RequestContent | None = None,
        data: RequestData | None = None,
        files: RequestFiles | None = None,
        json: Any = None,
        params: QueryParamTypes | None = None,
        headers: HeaderTypes | None = None,
        cookies: CookieTypes | None = None,
        follow_redirects: bool = True,
        timeout: TimeoutTypes | None = None,
        verify: VerifyTypes = True,
        http2: bool = False,
        proxies: ProxiesTypes | None = None,
        **kwargs,
    ) -> Response:
        """发起 PATCH 请求。

        ### 参数
            url: 请求地址

            content: 请求内容

            data: 请求数据

            files: 请求文件

            json: 请求 JSON

            params: 请求参数

            headers: 请求头

            cookies: 请求 Cookie

            follow_redirects: 是否跟随重定向

            timeout: 超时时间，单位: 秒

            verify: 是否验证 SSL 证书

            http2: 是否使用 HTTP/2

            proxies: 代理地址

            **kwargs: 传递给 `httpx.AsyncClient` 的其他参数

        ### 返回
            `httpx.Response` 对象
        """
        async with httpx.AsyncClient(
            verify=verify,
            http2=http2,
            proxies=proxies or bot_config.proxy_url,  # type: ignore
            **kwargs,
        ) as client:
            return await client.patch(
                url,
                content=content,
                data=data,
                files=files,
                json=json,
                params=params,
                headers=add_user_agent(headers),
                cookies=cookies,
                follow_redirects=follow_redirects,
                timeout=timeout if timeout is not None else bot_config.http_timeout,
            )

    @classmethod
    async def head(
        cls,
        url: URLTypes,
        *,
        params: QueryParamTypes | None = None,
        headers: HeaderTypes | None = None,
        cookies: CookieTypes | None = None,
        follow_redirects: bool = True,
        timeout: TimeoutTypes | None = None,
        verify: VerifyTypes = True,
        http2: bool = False,
        proxies: ProxiesTypes | None = None,
        **kwargs,
    ) -> Response:
        """发起 HEAD 请求。

        ### 参数
            url: 请求地址

            params: 请求参数

            headers: 请求头

            cookies: 请求 Cookie

            follow_redirects: 是否跟随重定向

            timeout: 超时时间，单位: 秒

            verify: 是否验证 SSL 证书

            http2: 是否使用 HTTP/2

            proxies: 代理地址

            **kwargs: 传递给 `httpx.AsyncClient` 的其他参数

        ### 返回
            `httpx.Response` 对象
        """
        async with httpx.AsyncClient(
            verify=verify,
            http2=http2,
            proxies=proxies or bot_config.proxy_url,  # type: ignore
            **kwargs,
        ) as client:
            return await client.head(
                url,
                params=params,
                headers=add_user_agent(headers),
                cookies=cookies,
                follow_redirects=follow_redirects,
                timeout=timeout if timeout is not None else bot_config.http_timeout,
            )

    @classmethod
    async def options(
        cls,
        url: URLTypes,
        *,
        params: QueryParamTypes | None = None,
        headers: HeaderTypes | None = None,
        cookies: CookieTypes | None = None,
        follow_redirects: bool = True,
        timeout: TimeoutTypes | None = None,
        verify: VerifyTypes = True,
        http2: bool = False,
        proxies: ProxiesTypes | None = None,
        **kwargs,
    ) -> Response:
        """发起 OPTIONS 请求。

        ### 参数
            url: 请求地址

            params: 请求参数

            headers: 请求头

            cookies: 请求 Cookie

            follow_redirects: 是否跟随重定向

            timeout: 超时时间，单位: 秒

            verify: 是否验证 SSL 证书

            http2: 是否使用 HTTP/2

            proxies: 代理地址

            **kwargs: 传递给 `httpx.AsyncClient` 的其他参数

        ### 返回
            `httpx.Response` 对象
        """
        async with httpx.AsyncClient(
            verify=verify,
            http2=http2,
            proxies=proxies or bot_config.proxy_url,  # type: ignore
            **kwargs,
        ) as client:
            return await client.options(
                url,
                params=params,
                headers=add_user_agent(headers),
                cookies=cookies,
                follow_redirects=follow_redirects,
                timeout=timeout if timeout is not None else bot_config.http_timeout,
            )

    @classmethod
    async def request(
        cls,
        method: Literal["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"],
        url: URLTypes,
        *,
        content: RequestContent | None = None,
        data: RequestData | None = None,
        files: RequestFiles | None = None,
        json: Any = None,
        params: QueryParamTypes | None = None,
        headers: HeaderTypes | None = None,
        cookies: CookieTypes | None = None,
        follow_redirects: bool = True,
        timeout: TimeoutTypes | None = None,
        verify: VerifyTypes = True,
        http2: bool = False,
        proxies: ProxiesTypes | None = None,
        **kwargs,
    ) -> Response:
        """发起请求。

        ### 参数
            method: 请求方法

            url: 请求地址

            content: 请求内容

            data: 请求数据

            files: 请求文件

            json: 请求 JSON

            params: 请求参数

            headers: 请求头

            cookies: 请求 Cookie

            follow_redirects: 是否跟随重定向

            timeout: 超时时间，单位: 秒

            verify: 是否验证 SSL 证书

            http2: 是否使用 HTTP/2

            proxies: 代理地址

            **kwargs: 传递给 `httpx.AsyncClient` 的其他参数

        ### 返回
            `httpx.Response` 对象
        """
        async with httpx.AsyncClient(
            verify=verify,
            http2=http2,
            proxies=proxies or bot_config.proxy_url,  # type: ignore
            **kwargs,
        ) as client:
            return await client.request(
                method,
                url,
                content=content,
                data=data,
                files=files,
                json=json,
                params=params,
                headers=add_user_agent(headers),
                cookies=cookies,
                follow_redirects=follow_redirects,
                timeout=timeout if timeout is not None else bot_config.http_timeout,
            )

    @classmethod
    @asynccontextmanager
    async def stream(
        cls,
        method: Literal["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"],
        url: URLTypes,
        *,
        content: RequestContent | None = None,
        data: RequestData | None = None,
        files: RequestFiles | None = None,
        json: Any = None,
        params: QueryParamTypes | None = None,
        headers: HeaderTypes | None = None,
        cookies: CookieTypes | None = None,
        follow_redirects: bool = True,
        timeout: TimeoutTypes | None = None,
        verify: VerifyTypes = True,
        http2: bool = False,
        proxies: ProxiesTypes | None = None,
        **kwargs,
    ) -> AsyncGenerator[Response, None]:
        """发起流式请求。

        ### 参数
            method: 请求方法

            url: 请求地址

            content: 请求内容

            data: 请求数据

            files: 请求文件

            json: 请求 JSON

            params: 请求参数

            headers: 请求头

            cookies: 请求 Cookie

            follow_redirects: 是否跟随重定向

            timeout: 超时时间，单位: 秒

            verify: 是否验证 SSL 证书

            http2: 是否使用 HTTP/2

            proxies: 代理地址

            **kwargs: 传递给 `httpx.AsyncClient` 的其他参数

        ### 生成
            `httpx.Response` 对象
        """
        async with httpx.AsyncClient(
            verify=verify,
            http2=http2,
            proxies=proxies or bot_config.proxy_url,  # type: ignore
            **kwargs,
        ) as client, client.stream(
            method,
            url,
            content=content,
            data=data,
            files=files,
            json=json,
            params=params,
            headers=add_user_agent(headers),
            cookies=cookies,
            follow_redirects=follow_redirects,
            timeout=timeout if timeout is not None else bot_config.http_timeout,
        ) as response:
            yield response

    @classmethod
    @asynccontextmanager
    async def client_session(
        cls,
        verify: VerifyTypes = True,
        http2: bool = False,
        proxies: ProxiesTypes | None = None,
        follow_redirects: bool = True,
        **kwargs,
    ) -> AsyncGenerator[httpx.AsyncClient, None]:
        """创建 `httpx.AsyncClient` 会话。

        ### 参数
            verify: 是否验证 SSL 证书

            http2: 是否使用 HTTP/2

            proxies: 代理地址

            follow_redirects: 是否跟随重定向

            **kwargs: 传递给 `httpx.AsyncClient` 的其他参数

        ### 生成
            `httpx.AsyncClient` 对象
        """
        async with httpx.AsyncClient(
            verify=verify,
            http2=http2,
            proxies=proxies or bot_config.proxy_url,  # type: ignore
            follow_redirects=follow_redirects,
            **kwargs,
        ) as client:
            yield client
