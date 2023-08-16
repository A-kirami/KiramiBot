"""本模块包含了所有 KiramiBot 运行时可能会抛出的异常"""

from nonebot.adapters.onebot.v11.exception import ActionFailed as ActionFailed
from nonebot.adapters.onebot.v11.exception import ApiNotAvailable as ApiNotAvailable
from nonebot.exception import AdapterException as AdapterException
from nonebot.exception import FinishedException as FinishedException
from nonebot.exception import IgnoredException as IgnoredException
from nonebot.exception import MatcherException as MatcherException
from nonebot.exception import MockApiException as MockApiException
from nonebot.exception import NoLogException as NoLogException
from nonebot.exception import NoneBotException
from nonebot.exception import ParserExit as ParserExit
from nonebot.exception import PausedException as PausedException
from nonebot.exception import ProcessException as ProcessException
from nonebot.exception import RejectedException as RejectedException
from nonebot.exception import SkippedException as SkippedException
from nonebot.exception import StopPropagation as StopPropagation
from nonebot.exception import TypeMisMatch as TypeMisMatch


class KiramiBotError(NoneBotException):
    """所有 KiramiBot 发生的异常基类"""


# ==============================================================================


class NetworkError(KiramiBotError):
    """网络错误"""


class HttpRequestError(NetworkError):
    """HTTP 请求异常"""


# ==============================================================================


class ServerError(KiramiBotError):
    """服务器错误"""


# ==============================================================================


class ResourceError(KiramiBotError):
    """资源操作异常"""


class FileNotExistError(ResourceError, FileNotFoundError):
    """文件不存在"""


class ReadFileError(ResourceError):
    """读取文件错误"""


class WriteFileError(ResourceError):
    """写入文件错误"""


class FileTypeError(ResourceError):
    """文件类型错误"""


# ==============================================================================


class ServiceError(KiramiBotError):
    """插件服务异常"""


class ServitizationError(ServiceError):
    """插件服务化异常"""


# ==============================================================================


class StoreError(KiramiBotError):
    """存储异常"""


class DatabaseError(StoreError):
    """数据库异常"""


# ==============================================================================


class PermissionError(KiramiBotError):
    """权限异常"""


class UnauthorizedError(PermissionError):
    """无权访问"""
