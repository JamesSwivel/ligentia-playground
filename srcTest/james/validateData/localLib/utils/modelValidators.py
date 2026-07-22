from pydantic import BaseModel, Field
from pathlib import Path
from typing import Literal, Annotated, Any, TypeVar
from typing_extensions import TypedDict
import swivel.common as U


class ModelValidators:

    # @classmethod
    # def toDatetimeWithAppTimeZone(cls, v: Any) -> datetime:
    #     funcName = cls.toDatetimeWithAppTimeZone.__name__
    #     prefix = f"{funcName}"
    #     try:
    #         return DbUtil.toDatetimeWithTimeZone(v, App.TimeZoneId)
    #     except Exception as e:
    #         raise ValueError(e)

    # @classmethod
    # def toDatetimeWithAppTimeZoneNullable(cls, v: Any) -> datetime | None:
    #     funcName = cls.toDatetimeWithAppTimeZoneNullable.__name__
    #     prefix = f"{funcName}"
    #     try:
    #         if v is None:
    #             return None
    #         return DbUtil.toDatetimeWithTimeZone(v, App.TimeZoneId)
    #     except Exception as e:
    #         raise ValueError(e)

    # @classmethod
    # def toUUIDStrNullable(cls, v: Any) -> str | None:
    #     funcName = cls.toUUIDStrNullable.__name__
    #     prefix = f"{funcName}"
    #     try:
    #         if v is None:
    #             return None
    #         return cls.toUUIDStr(v)
    #     except Exception as e:
    #         raise ValueError(e)

    @classmethod
    def toEmptyStrOnNull(cls, v: Any) -> str:
        funcName = cls.toEmptyStrOnNull.__name__
        prefix = f"{funcName}"
        try:
            if isinstance(v, str):
                return v
            elif v is None:
                return ""
            else:
                raise Exception(f"invalid input value")

        except Exception as e:
            raise ValueError(e)

    @classmethod
    def toEmptyListOnNull(cls, v: Any) -> list:
        funcName = cls.toEmptyListOnNull.__name__
        prefix = f"{funcName}"
        try:
            if isinstance(v, list):
                return v
            elif v is None:
                return []
            else:
                raise Exception(f"invalid input value")

        except Exception as e:
            raise ValueError(e)
