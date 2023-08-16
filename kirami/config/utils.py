import importlib
import itertools
from collections.abc import Callable
from pathlib import Path
from typing import Any

from nonebot.plugin import Plugin

try:  # pragma: py-gte-311
    import tomllib  # pyright: ignore[reportMissingImports]
except ModuleNotFoundError:  # pragma: py-lt-311
    import tomli as tomllib


def load_config() -> dict[str, Any]:
    """加载 KiramiBot 配置。

    ### 说明
        配置文件优先级: `kirami.toml`，`kirami.config.toml`，`kirami.yaml`，`kirami.config.yaml`，`kirami.yml`，`kirami.config.yml`，`kirami.json`，`kirami.config.json`

        当以上文件均不存在时，会尝试读取 `pyproject.toml` 中的 `tool.kirami` 配置
    """

    def load_file(path: str | Path) -> dict[str, Any]:
        return tomllib.loads(Path(path).read_text(encoding="utf-8"))

    file_name = ("kirami", "kirami.config")
    file_type = ("toml", "yaml", "yml", "json")
    config_files = itertools.product(file_name, file_type)
    for name, type in config_files:
        file = Path(f"{name}.{type}")
        if file.is_file():
            return load_file(file)
    pyproject = load_file("pyproject.toml")
    return pyproject.get("tool", {}).get("kirami", {})


def find_plugin(cls: Callable[..., Any], /) -> Plugin | None:
    """查找类所在的插件对象

    ### 参数
        cls: 查找的类
    """
    module_name = cls.__module__
    module = importlib.import_module(module_name)
    parts = module_name.split(".")

    for i in range(len(parts), 0, -1):
        current_module = ".".join(parts[:i])
        module = importlib.import_module(current_module)
        if plugin := getattr(module, "__plugin__", None):
            return plugin

    return None
