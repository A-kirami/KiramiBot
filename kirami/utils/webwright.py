"""本模块提供了一个简单的浏览器管理器"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import ClassVar, Literal, cast

from loguru import logger
from playwright.async_api import (
    Browser,
    BrowserContext,
    BrowserType,
    Error,
    Page,
    Playwright,
    async_playwright,
)

from kirami.config import bot_config
from kirami.hook import on_shutdown


class WebWright:
    _playwright: ClassVar[Playwright | None] = None
    _browser: ClassVar[Browser | None] = None

    @classmethod
    async def launch(
        cls,
        browser: Literal["chromium", "firefox", "webkit"] | None = None,
        *args,
        **kwargs,
    ) -> None:
        """启动浏览器。

        ### 参数
            browser: 浏览器类型，可选值为 `chromium`，`firefox`，`webkit`，未指定时使用配置文件中的默认值

            *args: 传递给 [playwright.async_api.BrowserType.launch](https://playwright.dev/python/docs/api/class-browsertype#browser-type-launch) 的位置参数

            **kwargs: 传递给 [playwright.async_api.BrowserType.launch](https://playwright.dev/python/docs/api/class-browsertype#browser-type-launch) 的关键字参数
        """
        try:
            if not cls._playwright:
                cls._playwright = await async_playwright().start()
            if not cls._browser:
                browser_type: BrowserType = getattr(
                    cls._playwright, browser or bot_config.browser
                )
                cls._browser = await browser_type.launch(*args, **kwargs)
            logger.success(f"{bot_config.browser} 浏览器启动成功")
        except Error:
            logger.error(f"{bot_config.browser} 浏览器未安装，正在尝试自动安装")
            await install_browser()
            await cls.launch(browser, *args, **kwargs)

    @classmethod
    async def stop(cls) -> None:
        """关闭浏览器"""
        if cls._browser:
            await cls._browser.close()
            logger.success(f"{bot_config.browser} 浏览器已关闭")
        if cls._playwright:
            await cls._playwright.stop()

    @classmethod
    async def get_browser(cls) -> Browser:
        """获取浏览器实例"""
        if not cls._browser:
            await cls.launch()
        return cast(Browser, cls._browser)

    @classmethod
    @asynccontextmanager
    async def new_context(cls, **kwargs) -> AsyncGenerator[BrowserContext, None]:
        """新建浏览器上下文。

        ### 参数
            **kwargs: 传递给 [playwright.async_api.Browser.new_context](https://playwright.dev/python/docs/api/class-browser#browser-new-context) 的关键字参数
        """
        browser = await cls.get_browser()
        context = await browser.new_context(**kwargs)
        try:
            yield context
        finally:
            await context.close()

    @classmethod
    @asynccontextmanager
    async def new_page(cls, **kwargs) -> AsyncGenerator[Page, None]:
        """新建页面。

        ### 参数
            **kwargs: 传递给 [playwright.async_api.Browser.new_page](https://playwright.dev/python/docs/api/class-browser#browser-new-page) 的关键字参数
        """
        browser = await cls.get_browser()
        page = await browser.new_page(**kwargs)
        try:
            yield page
        finally:
            await page.close()


async def install_browser() -> None:
    import asyncio

    from playwright._impl._driver import compute_driver_executable, get_driver_env

    logger.info(f"正在安装 {bot_config.browser} 浏览器")
    driver_executable = compute_driver_executable()
    process = await asyncio.create_subprocess_exec(
        driver_executable,
        "install",
        "--with-deps",
        bot_config.browser,
        env=get_driver_env(),
    )
    return_code = await process.wait()
    if return_code:
        logger.error(
            f"{bot_config.browser} 浏览器安装失败，请检查网络状况或尝试手动安装"
        )
    logger.success(f"{bot_config.browser} 浏览器安装成功")


on_shutdown(WebWright.stop)
