"""本模块提供了一个异步定时任务调度器"""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger
from nonebot.log import LoguruHandler

from kirami.config import bot_config
from kirami.hook import on_shutdown, on_startup

scheduler = AsyncIOScheduler()
apscheduler_config = getattr(bot_config, "apscheduler_config", {})
apscheduler_config.setdefault("apscheduler.timezone", bot_config.time_zone)
scheduler.configure(apscheduler_config)


@on_startup
async def start_scheduler() -> None:
    if not scheduler.running:
        scheduler.start()
        logger.opt(colors=True).success("<y>Scheduler Started</y>")


@on_shutdown
async def shutdown_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown()
        logger.opt(colors=True).success("<y>Scheduler Shutdown</y>")


aps_logger = logging.getLogger("apscheduler")
aps_logger.setLevel(getattr(bot_config, "apscheduler_log_level", 30))
aps_logger.handlers.clear()
aps_logger.addHandler(LoguruHandler())
