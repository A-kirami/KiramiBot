"""本模块定义了 KiramiBot 运行所需的配置项"""


from collections.abc import KeysView, Mapping
from datetime import timedelta
from ipaddress import IPv4Address
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, ClassVar, Literal, NoReturn, TypeAlias

from mango.drive import DEFAULT_CONNECT_URI
from nonebot.config import Config, Env
from pydantic import BaseModel, Field, IPvAnyAddress, root_validator
from typing_extensions import Self

from .utils import find_plugin

LevelName: TypeAlias = Literal[
    "TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"
]


class BaseConfig(BaseModel, Mapping):
    __raw_config__: ClassVar[MappingProxyType[str, Any]] = MappingProxyType({})

    def __getitem__(self, key: str) -> Any:
        try:
            return getattr(self, key)
        except AttributeError as e:
            raise RuntimeError(
                f"{self.__class__.__name__} 不存在 {key} 配置, 请检查拼写是否正确"
            ) from e

    def __setitem__(self, *_) -> NoReturn:
        raise RuntimeError("无法在运行时修改配置")

    def __delitem__(self, _) -> NoReturn:
        raise RuntimeError("无法在运行时修改配置")

    def __setattr__(self, *_) -> NoReturn:
        raise RuntimeError("无法在运行时修改配置")

    def __delattr__(self, _) -> NoReturn:
        raise RuntimeError("无法在运行时修改配置")

    def __len__(self) -> int:
        return len(self.__dict__)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.__dict__}>"

    def keys(self) -> KeysView[str]:
        return self.__dict__.keys()

    @classmethod
    def load_config(cls, namespace: str | None = None) -> Self:
        """加载配置。

        ### 参数
            namespace: 配置的命名空间，如果为 None 则自动查找并使用插件名称
        """
        if namespace is None and (plugin := find_plugin(cls)):
            namespace = plugin.name

        if not namespace:
            raise RuntimeError("无法确定配置所属插件，请指定 namespace")

        return cls(**cls.__raw_config__.get(namespace, {}))


class LogConfig(BaseConfig):
    log_expire_timeout: int = 7
    """日志文件过期时间"""


class DatabaseConfig(BaseConfig):
    """
    MongoDB 数据库配置
    """

    uri: str = DEFAULT_CONNECT_URI
    """MongoDB 连接 URI"""

    host: IPvAnyAddress = IPv4Address("127.0.0.1")  # type: ignore
    """MongoDB 服务器地址"""

    port: int = Field(default=27017, ge=1, le=65535)
    """MongoDB 服务器端口"""

    username: str = ""
    """MongoDB 连接用户名"""

    password: str = ""
    """MongoDB 连接密码"""

    database: str = "kirami"
    """MongoDB 数据库名称"""


class PluginConfig(BaseConfig):
    """
    插件加载配置
    """

    plugins: set[str] = set()
    """加载的插件"""

    plugin_dirs: set[str] = set()
    """插件目录列表"""

    whitelist: set[str] | None = None
    """插件白名单，只加载指定插件"""

    blacklist: set[str] | None = None
    """插件黑名单，不加载指定插件"""


class ServerConfig(BaseConfig):
    """
    APP 服务器配置
    """

    allow_cors: bool = True
    """是否允许跨域请求。默认为 True"""

    allow_origins: list[str] = ["*"]
    """允许跨域请求的源列表。默认允许所有"""

    allow_origin_regex: str | None = None
    """正则表达式字符串，匹配的源允许跨域请求"""

    allow_methods: list[str] = ["*"]
    """允许跨域请求的 HTTP 方法列表。默认允许所有标准方法"""

    allow_headers: list[str] = ["*"]
    """允许跨域请求的 HTTP 请求头列表。默认允许所有的请求头。`Accept`、`Accept-Language`、`Content-Language` 以及 `Content-Type` 请求头总是允许 CORS 请求"""

    allow_credentials: bool = False
    """指示跨域请求支持 cookies。默认为 False。另外，允许凭证时 allow_origins 不能设定为 ['*']，必须指定源"""

    expose_headers: list[str] = []
    """指示可以被浏览器访问的响应头。默认为 []"""

    max_age: int = 600
    """设定浏览器缓存 CORS 响应的最长时间，单位是秒。默认为 600"""


class BotConfig(BaseConfig):
    """
    Bot 主要配置。
    """

    driver: str = "~fastapi"
    """KiramiBot 运行所使用的 `Driver`"""

    adapters: set[str] = {"~onebot.v11"}
    """KiramiBot 所使用的 `Adapter`"""

    host: IPvAnyAddress = IPv4Address("127.0.0.1")  # type: ignore
    """KiramiBot 的 HTTP 和 WebSocket 服务端监听的 IP/主机名"""

    port: int = Field(default=8120, ge=1, le=65535)
    """KiramiBot 的 HTTP 和 WebSocket 服务端监听的端口"""

    debug: bool = False
    """是否以调试模式运行 KiramiBot"""

    log_level: LevelName | int = "INFO"
    """配置 KiramiBot 日志输出等级，可以为 `int` 类型等级或等级名称，参考 [loguru 日志等级](https://loguru.readthedocs.io/en/stable/api/logger.html#levels)"""

    log_file: LevelName | tuple[LevelName] = "ERROR"
    """KiramiBot 的日志保存等级，必须为等级名称"""

    api_root: dict[str, str] = {}
    """以机器人 ID 为键，上报地址为值的字典"""

    api_timeout: float = 30.0
    """API 请求超时时间，单位: 秒"""

    onebot_access_token: str = Field(default=None, alias="access_token")
    """API 请求以及上报所需密钥，在请求头中携带"""

    secret: str | None = None
    """HTTP POST 形式上报所需签名，在请求头中携带"""

    superusers: set[str] = set()
    """机器人超级用户"""

    nickname: set[str] = {"kirami", "星见"}
    """机器人昵称"""

    command_start: set[str] = {"/", ""}
    """命令的起始标记，用于判断一条消息是不是命令"""

    command_sep: set[str] = {"."}
    """命令的分隔标记，用于将文本形式的命令切分为元组（实际的命令名）"""

    session_expire_timeout: timedelta = timedelta(minutes=2)
    """等待用户回复的超时时间"""

    proxy_url: str | dict[str, str] | None = None
    """HTTP 代理地址"""

    http_timeout: float = 10.0
    """HTTP 请求超时时间，单位: 秒"""

    browser: Literal["chromium", "firefox", "webkit"] = "chromium"
    """浏览器类型"""

    time_zone: str = "Asia/Shanghai"
    """时区"""

    default_policy_allow: set[str] = {"*"}
    """默认权限策略允许的内容列表"""

    _env_file: str | None = Field(default=None, alias="env_file")
    """配置文件名默认从 `.env.{env_name}` 中读取配置"""

    @root_validator(pre=True)
    def mixin_config(cls, values: dict[str, Any]) -> dict[str, Any]:
        config = Config(**values, _env_file=(".env", f".env.{Env().environment}"))
        return config.dict(exclude_unset=True)

    class Config:
        extra = "allow"

    if TYPE_CHECKING:

        def __getattr__(self, name: str) -> Any:
            ...


class KiramiConfig(BaseConfig):
    """
    KiramiBot 主要配置。
    """

    bot: BotConfig
    """本体主要配置"""

    plugin: PluginConfig
    """插件加载相关配置"""

    server: ServerConfig
    """服务器相关配置"""

    log: LogConfig
    """日志相关配置"""

    database: DatabaseConfig
    """数据库相关配置"""

    @root_validator(pre=True)
    def set_default_config(cls, values: dict[str, Any]) -> dict[str, Any]:
        BaseConfig.__raw_config__ = MappingProxyType(values)
        for name, config in cls.__annotations__.items():
            values.setdefault(name, config())
        return values

    @property
    def config(self) -> MappingProxyType[str, Any]:
        """原始配置"""
        return BaseConfig.__raw_config__
