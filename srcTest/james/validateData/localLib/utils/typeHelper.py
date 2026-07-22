from pydantic import BaseModel, Field
from pathlib import Path
from typing import Literal, Annotated, Any, TypeVar
from typing_extensions import TypedDict
import swivel.common as U

TBaseModel = TypeVar("TBaseModel", bound=BaseModel)


class TypeHelper:

    @classmethod
    def toBaseModel(
        cls,
        modelType: type[TBaseModel],
        data: dict[str, Any] | Path,
    ) -> TBaseModel:
        funcName = cls.toBaseModel.__name__
        prefix = funcName
        try:
            if isinstance(data, dict):
                return modelType.model_validate(data)
            if isinstance(data, Path):
                obj = U.readFile(str(data.resolve()), "json")
                return modelType.model_validate(obj)
            else:
                raise Exception(f"invalid data")
        except Exception as e:
            U.throwPrefix(prefix, e)
