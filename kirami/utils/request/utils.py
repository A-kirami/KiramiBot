import json
import secrets
from collections.abc import Sequence
from pathlib import Path
from typing import Literal

from httpx._types import HeaderTypes


def fake_user_agent(
    browser: Literal["chrome", "opera", "firefox", "safari", "internetexplorer"]
    | None = None,
) -> dict[str, str]:
    """获取一个随机的 User-Agent。

    ### 参数
        browser: 浏览器类型，如果不指定则随机选择
    """
    fake_file = Path(__file__).parent / "fake_user_agent.json"
    if not fake_file.is_file():
        raise FileNotFoundError(f"{fake_file} is not found.")
    fake_data = json.loads(fake_file.read_text(encoding="utf-8"))
    if not browser:
        browser = secrets.choice(list(fake_data["randomize"].values()))
    return {"User-Agent": secrets.choice(fake_data["browsers"][browser])}


def add_user_agent(headers: HeaderTypes | None = None) -> HeaderTypes:
    """添加随机的 User-Agent 到请求头中。

    ### 参数
        headers: 请求头字典或列表

    ### 返回
        添加了随机 User-Agent 的请求头字典
    """
    user_agent = fake_user_agent()
    if headers:
        _headers = dict(headers) if isinstance(headers, Sequence) else headers
        return {**user_agent, **_headers}  # type: ignore
    return user_agent
