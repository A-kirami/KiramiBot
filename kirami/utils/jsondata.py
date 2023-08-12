"""本模块提供了 json 字典和 json 模型"""

import json
from pathlib import Path
from typing import Any, ClassVar

from pydantic import BaseModel, PrivateAttr, root_validator
from typing_extensions import Self

from kirami.config import DATA_DIR
from kirami.exception import FileNotExistError, ReadFileError


class JsonDict(dict[str, Any]):
    _file_path: Path
    _auto_load: bool
    _initial_data: dict[str, Any]

    def __init__(
        self,
        data: dict[str, Any] | None = None,
        /,
        *,
        path: str | Path = DATA_DIR,
        auto_load: bool = False,
    ) -> None:
        """创建 json 数据字典

        ### 参数
            data: json 数据

            path: 文件路径

            auto_load: 是否自动加载文件
        """
        self._file_path = Path(path)
        self._auto_load = auto_load
        self._initial_data = data.copy() if data else {}

        if auto_load and self._file_path.is_file():
            json_data = json.loads(self._file_path.read_text("utf-8"))
        else:
            json_data = self._initial_data
            self.file_path.parent.mkdir(parents=True, exist_ok=True)

        super().__init__(**json_data)

    @property
    def file_path(self) -> Path:
        """文件路径"""
        return self._file_path

    def load(self) -> None:
        """从文件加载数据"""
        if self._auto_load:
            raise RuntimeError("Auto load is enabled, cannot load manually.")
        if not self._file_path.is_file():
            raise FileNotFoundError(self._file_path)
        self.update(json.loads(self._file_path.read_text("utf-8")))

    def save(self) -> None:
        """保存数据到文件"""
        self.file_path.write_text(json.dumps(self))

    def clear(self) -> None:
        """清除全部数据"""
        super().clear()
        self.save()

    def delete(self) -> None:
        """删除文件"""
        super().clear()
        self.file_path.unlink(missing_ok=True)

    def reset(self) -> None:
        """重置数据"""
        super().clear()
        self.update(self._initial_data)
        self.save()


class JsonModel(BaseModel):
    """json 模型"""

    _file_path: ClassVar[Path]
    _auto_load: ClassVar[bool]
    _scatter_fields: ClassVar[list[str]]
    _initial_data: dict[str, Any] = PrivateAttr()

    def __init_subclass__(
        cls,
        path: str | Path = DATA_DIR,
        auto_load: bool = False,
    ) -> None:
        cls._file_path = Path(path) / f"{cls.__name__.lower()}.json"
        cls._auto_load = auto_load
        scatter_fields = []
        for field in cls.__fields__.values():
            if field.field_info.extra.get("scatter", False):
                scatter_fields.append(field.name)
                field.field_info.allow_mutation = False
        cls._scatter_fields = scatter_fields
        if cls._auto_load and cls._scatter_fields:
            raise ValueError("auto_load and scatter fields cannot be used together.")
        return super().__init_subclass__()

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self._initial_data = self.dict()

    @root_validator(pre=True)
    def _load_file(cls, values: dict[str, Any]) -> dict[str, Any]:
        if cls._auto_load and cls._file_path.is_file():
            return json.loads(cls._file_path.read_text("utf-8"))
        return values

    @property
    def file_path(self) -> Path:
        """文件路径"""
        file_path = self.__class__._file_path
        if self.__class__._scatter_fields:
            return file_path.with_suffix("") / f"{self.scatter_key}.json"
        return file_path

    @property
    def scatter_key(self) -> str:
        """离散键"""
        return "_".join(
            str(getattr(self, field)) for field in self.__class__._scatter_fields
        )

    @classmethod
    def load(cls, scatter_key: str | None = None) -> Self:
        """加载数据。

        ### 参数
            scatter_key: 离散键
        """
        if cls._auto_load:
            raise ReadFileError("Auto load is enabled, cannot load manually.")
        if scatter_key:
            file_path = cls._file_path.with_suffix("") / f"{scatter_key}.json"
        else:
            file_path = cls._file_path
        if file_path.is_file():
            return cls(**json.loads(file_path.read_text("utf-8")))
        raise FileNotExistError

    @classmethod
    def load_all(cls) -> list[Self]:
        """加载全部数据"""
        if cls._auto_load:
            raise ReadFileError("Auto load is enabled, cannot load manually.")
        if not cls._scatter_fields:
            raise ReadFileError("No scatter fields.")
        return [
            cls.load(file.name)
            for file in cls._file_path.with_suffix("").glob("*.json")
        ]

    def save(self) -> None:
        """保存数据到文件"""
        self.file_path.write_text(json.dumps(self.dict()))

    def delete(self) -> None:
        """删除文件"""
        self.file_path.unlink(missing_ok=True)

    def reset(self) -> None:
        """重置数据"""
        for field, value in self._initial_data.items():
            setattr(self, field, value)

    class Config:
        validate_assignment = True
