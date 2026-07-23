from pydantic import BaseModel, Field
from pathlib import Path
from typing import Literal, Annotated, Any, TypeVar, Final
from typing_extensions import TypedDict
import swivel.common as U


class App:
    ScriptDir: Final = Path(__file__).resolve().parent
    ProjectRootDir = ScriptDir.parent.parent.parent.parent.parent
    U.logW(f"ProjectRootDir={ProjectRootDir}")
    LogDir = ProjectRootDir / "log"
    # U.logW(f"LogDir={LogDir}")
    DataDir = ProjectRootDir / "data"
    # U.logW(f"DataDir={DataDir}")
    BrowseDataDir = DataDir / "browser"
    # U.logW(f"BrowseDataDir={BrowseDataDir}")

    @classmethod
    def checkHeader(
        cls,
    ):
        funcName = cls.checkHeader.__name__
        prefix = funcName
        try:
            pass
        except Exception as e:
            U.throwPrefix(prefix, e)
