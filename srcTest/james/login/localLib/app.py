import asyncio
import json
import re
from textwrap import dedent
import os
from pathlib import Path
from typing import Callable, Literal, cast, Final
from typing_extensions import TypedDict
import swivel.common as U
from dotenv import dotenv_values

from james.login.login import EnvFile


class App:
    ScriptDir: Final = Path(__file__).parent.parent.resolve()
    ProjectRootDir: Final = ScriptDir.parent.parent.parent.resolve()

    U.logW(f"ScriptDir={ScriptDir}")
    U.logW(f"ProjectRootDir={ProjectRootDir}")

    EnvFile: Final = ScriptDir / ".env"
    LogDir: Final = ProjectRootDir / "log"
    DataDir: Final = ProjectRootDir / "data"
    BrowseDataDir: Final = DataDir / "browser"

    ## Browser state files
    SessionFile: Final = BrowseDataDir / "session.json"
    StateFile: Final = BrowseDataDir / "state.json"
    JwtFile: Final = BrowseDataDir / "jwt.txt"

    ## ENV config
    EnvConfig: dict[str, str | None] = {}

    @classmethod
    def readEnv(cls, envFile: Path | None = None):
        if envFile is None:
            envFile = cls.EnvFile
        cls.EnvConfig = dotenv_values(envFile)
