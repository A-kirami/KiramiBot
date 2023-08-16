"""本模块定义了 KiramiBot 运行所需的文件目录"""

from pathlib import Path

# ========== 根目录 ==========

BOT_DIR = Path.cwd()
"""Bot 根目录"""

# ========== 文件目录 ==========

DATA_DIR = BOT_DIR / "data"
"""数据保存目录"""

LOG_DIR = BOT_DIR / "logs"
"""日志保存目录"""

RES_DIR = BOT_DIR / "resources"
"""资源文件目录"""

# ========== 资源目录 ==========

IMAGE_DIR = RES_DIR / "image"
"""图片文件目录"""

VIDEO_DIR = RES_DIR / "video"
"""视频文件目录"""

AUDIO_DIR = RES_DIR / "audio"
"""音频文件目录"""

FONT_DIR = RES_DIR / "font"
"""字体文件目录"""

PAGE_DIR = RES_DIR / "page"
"""网页文件目录"""

# ========== 创建目录 ==========

for name, var in locals().copy().items():
    if name.endswith("_DIR") and isinstance(var, Path):
        var.mkdir(parents=True, exist_ok=True)
