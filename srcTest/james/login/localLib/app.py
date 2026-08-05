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
from playwright.async_api import (
    async_playwright,
    Page as PwPage,
    TimeoutError as PwTimeoutError,
    Request as PwRequest,
    Response as PwResponse,
    Frame as PwFrame,
    Browser as PwBrowser,
    BrowserContext as PwBrowserContext,
)


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

    @classmethod
    async def saveSession(cls, ctx: PwBrowserContext, page: PwPage, screenPrefixName: str):
        funcName = cls.saveSession.__name__
        prefix = funcName
        try:

            ## avoid import circular reference
            from .playwrightHelper import PlaywrightHelper

            sessionStorage, isSessionStorageEmpty = await PlaywrightHelper.saveSessionStorage(page, cls.SessionFile)
            localStorageAndCookies, isLocalStorageAndCookiesEmpty = await PlaywrightHelper.saveLocalStorageAndCookies(
                ctx, App.StateFile
            )
            try:
                if not isSessionStorageEmpty:
                    jwtKey = "oidc.user:https://identity.uat1.ligentix.net/:shipping-confirmation-portal-app"
                    jwtObjStr = sessionStorage.get(jwtKey)
                    if jwtObjStr is not None:
                        jwtObj = json.loads(jwtObjStr)
                        jwt = jwtObj.get("access_token")
                        with open(App.JwtFile, "w+") as f:
                            f.write(jwt)
                        U.logW(f"JWT: {App.JwtFile}")

            except Exception as e1:
                U.logPrefixE(prefix, e1)

            await PlaywrightHelper.dumpPageScreen(page, App.BrowseDataDir / f"{screenPrefixName}.png")

        except Exception as e:
            U.throwPrefix(prefix, e)
