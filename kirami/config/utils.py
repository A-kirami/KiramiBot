import itertools
from pathlib import Path
from typing import Any

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
