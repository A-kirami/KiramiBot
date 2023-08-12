"""本模块提供了 KiramiBot 运行所需的配置及目录。"""

from .config import BaseConfig as BaseConfig
from .config import KiramiConfig
from .path import AUDIO_DIR as AUDIO_DIR
from .path import BOT_DIR as BOT_DIR
from .path import DATA_DIR as DATA_DIR
from .path import FONT_DIR as FONT_DIR
from .path import IMAGE_DIR as IMAGE_DIR
from .path import LOG_DIR as LOG_DIR
from .path import PAGE_DIR as PAGE_DIR
from .path import RES_DIR as RES_DIR
from .path import VIDEO_DIR as VIDEO_DIR
from .utils import load_config

kirami_config = KiramiConfig(**load_config())
"""KiramiBot 配置"""

bot_config = kirami_config.bot
"""本体主要配置"""

plugin_config = kirami_config.plugin
"""插件加载相关配置"""

server_config = kirami_config.server
"""服务器相关配置"""

log_config = kirami_config.log
"""日志相关配置"""

database_config = kirami_config.database
"""数据库相关配置"""
