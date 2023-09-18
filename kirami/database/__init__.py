"""本模块包含了数据库连接和数据库模型的定义"""

from mango import Mango
from pymongo.errors import ServerSelectionTimeoutError

from kirami.exception import DatabaseError
from kirami.hook import on_shutdown, on_startup
from kirami.log import logger

from .models.argot import Argot as Argot
from .models.group import Group as Group
from .models.user import User as User


@on_startup(pre=True)
async def connect_database() -> None:
    from kirami.config import database_config

    try:
        await Mango.init(
            database_config.database,
            uri=database_config.uri,
            tz_aware=True,
            serverSelectionTimeoutMS=1000 * 10,
        )
        logger.success("已连接到 MongoDB 数据库")
    except ServerSelectionTimeoutError as e:
        raise DatabaseError("无法连接到数据库, 请确保 MangoDB 已启动且配置正确") from e


@on_shutdown
def disconnect_database() -> None:
    Mango.disconnect()
    logger.success("已断开与 MongoDB 数据库的连接")
