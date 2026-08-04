#!/usr/bin/env python

# Flow:
# login first to save the authentication state
# > https://playwright.dev/python/docs/auth
#  store the JWT into a file
# use it to send requests to APIs
# if the JWT expires, run the process of reauthentication
import asyncio
import json
import re
from textwrap import dedent
import os
from pathlib import Path
from typing import Callable, Literal
from typing_extensions import TypedDict
import swivel.common as U
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
from dotenv import dotenv_values

### Load <scriptDir>/.env
ScriptDir = Path(__file__).resolve().parent
U.logW(f"ScriptDir={ScriptDir}")

EnvFile = ScriptDir / ".env"
EnvConfig = dotenv_values(EnvFile)

## Determine project root and working directories
ProjectRootDir = ScriptDir.parent.parent.parent
U.logW(f"ProjectRootDir={ProjectRootDir}")
LogDir = ProjectRootDir / "log"
U.logW(f"LogDir={LogDir}")
DataDir = ProjectRootDir / "data"
U.logW(f"DataDir={DataDir}")
BrowseDataDir = DataDir / "browser"
U.logW(f"BrowseDataDir={BrowseDataDir}")

## Browser state files
SessionFile = BrowseDataDir / "session.json"
StateFile = BrowseDataDir / "state.json"
JwtFile = BrowseDataDir / "jwt.txt"


import json
from textwrap import dedent
from typing import Any, Mapping

from playwright.async_api import BrowserContext


class TWaitForPattern(TypedDict):
    name: str
    """name of the pattern"""
    pattern: re.Pattern
    """regex pattern to match the URL"""


class PlaywrightHelper:

    @classmethod
    def makeUrlPatternPredicate(cls, patterns: list[TWaitForPattern]) -> Callable[[str], bool]:
        """Builds the predicate function to pass into wait_for_url()."""
        return lambda url: any(p["pattern"].search(url) for p in patterns)

    @classmethod
    def findMatchedPattern(cls, url: str, patterns: list[TWaitForPattern]) -> TWaitForPattern | None:
        """After wait_for_url() resolves, find which pattern matched."""
        return next((p for p in patterns if p["pattern"].search(url)), None)

    @classmethod
    async def waitForUrl(
        cls,
        page: PwPage,
        patterns: list[TWaitForPattern],
        *,
        isDebug: bool = False,
        wait_until: Literal["commit", "domcontentloaded", "load", "networkidle", None] = "load",
        **kwargs,
    ) -> TWaitForPattern:
        funcName = cls.waitForUrl.__name__
        prefix = funcName
        try:
            """Wait for a URL that matches any of the given patterns, and return the matched pattern."""
            if isDebug:
                U.logD(f"{prefix} waiting for URLs: {[p['name'] for p in patterns]} ...")
            predicate = cls.makeUrlPatternPredicate(patterns)
            await page.wait_for_url(predicate, wait_until=wait_until, **kwargs)
            matchedPattern = cls.findMatchedPattern(page.url, patterns)
            if matchedPattern is None:
                raise Exception(f"wait_for_url() returned but no pattern matched the URL: {page.url}")
            if isDebug:
                U.logD(f"{prefix} matched URL: {page.url}, pattern: {matchedPattern['name']}")
            return matchedPattern
        except Exception as e:
            U.throwPrefix(prefix, e)

    @classmethod
    async def waitForUrlNotThrow(
        cls,
        page: PwPage,
        patterns: list[TWaitForPattern],
        *,
        isDebug: bool = False,
        wait_until: Literal["commit", "domcontentloaded", "load", "networkidle", None] = "load",
        **kwargs,
    ) -> tuple[TWaitForPattern | None, Exception | None]:
        funcName = cls.waitForUrlNotThrow.__name__
        prefix = funcName
        err: Exception | None = None
        matched: TWaitForPattern | None = None
        try:
            matchedPattern = await cls.waitForUrl(
                page,
                patterns,
                isDebug=isDebug,
                wait_until=wait_until,
                **kwargs,
            )
            return matchedPattern, err
        except Exception as e:
            U.logPrefixE(prefix, e)
            err = e
        return matched, err

    @classmethod
    async def dumpPageScreen(cls, page: PwPage, imageFile: Path):
        funcName = cls.dumpPageScreen.__name__
        prefix = funcName
        try:
            prefix = f"{prefix}[{page.url}]"
            await page.screenshot(path=imageFile, full_page=True)
            U.logW(f"{prefix} {imageFile}")
        except Exception as e:
            U.logPrefixE(prefix, e)

    @classmethod
    async def saveSessionStorage(cls, page: PwPage, sessionFilePath: Path):
        funcName = cls.saveSessionStorage.__name__
        prefix = funcName
        try:
            prefix = f"{prefix}[{page.url}]"
            sessionStorageStr = await page.evaluate("() => JSON.stringify(sessionStorage)")
            js = U.toDictNotThrow(sessionStorageStr)
            await U.SwAsyncFile.writeJsonFileFromDict(str(sessionFilePath), js, isIndent=True)
            U.logW(f"{prefix} {sessionFilePath}")
            return js
        except Exception as e:
            U.throwPrefix(prefix, e)

    @classmethod
    async def saveLocalStorageAndCookies(cls, ctx: PwBrowserContext, sessionFilePath: Path):
        funcName = cls.saveLocalStorageAndCookies.__name__
        prefix = funcName
        try:
            storage = await ctx.storage_state()  # contains cookies and local storage
            js = dict(storage)
            await U.SwAsyncFile.writeJsonFileFromDict(str(sessionFilePath), js, isIndent=True)
            U.logW(f"{prefix} {sessionFilePath}")
            return js
        except Exception as e:
            U.throwPrefix(prefix, e)

    @classmethod
    async def installInitScript(
        cls,
        context: PwBrowserContext,
        *,
        hostname: str,
        sessionStorage: str | Mapping[str, Any] | None,
    ) -> None:
        """
        Description:
        - Install a browser initialization script
          - restores sessionStorage for the specified hostname.
          - installs a client-side routing trace to log URL changes in the browser console.
        """
        funcName = cls.installInitScript.__name__
        prefix = funcName
        try:

            sessionStorageData: dict[str, Any] = {}
            sessionStorageStatus: str

            if sessionStorage is None:
                sessionStorageStatus = "none"

            elif isinstance(sessionStorage, str):
                strippedSessionStorage = sessionStorage.strip()

                if not strippedSessionStorage:
                    sessionStorageStatus = "empty string"
                else:
                    try:
                        parsedSessionStorage = json.loads(strippedSessionStorage)
                    except json.JSONDecodeError as error:
                        raise ValueError("sessionStorage must be a valid JSON object string") from error

                    if not isinstance(parsedSessionStorage, dict):
                        raise ValueError("sessionStorage JSON must represent an object")

                    sessionStorageData = parsedSessionStorage

                    if sessionStorageData:
                        sessionStorageStatus = "available"
                    else:
                        sessionStorageStatus = "empty object"

            elif isinstance(sessionStorage, Mapping):
                sessionStorageData = dict(sessionStorage)

                if sessionStorageData:
                    sessionStorageStatus = "available"
                else:
                    sessionStorageStatus = "empty mapping"

            else:
                raise TypeError("sessionStorage must be a JSON string, Mapping, or None")

            initScript = dedent(f"""
                console.log("[LOG][initScript] running initScript...");
                (() => {{
                    const targetHostname = {json.dumps(hostname)};
                    const currentHostname = window.location.hostname;

                    const sessionStorageStatus = {json.dumps(sessionStorageStatus)};
                    const sessionStorageEntries = {json.dumps(sessionStorageData, ensure_ascii=False)};
                    const sessionStorageInitMarker = "__playwrightSessionStorageInitialized__";
                    const routingTraceMarker = "__playwrightRoutingTraceInstalled__";

                    // restores session storage for the specified hostname
                    if (currentHostname !== targetHostname) {{
                        console.log("[LOG][initScript] Hostname not matched:", "expected=" + targetHostname, "actual=" + currentHostname);
                        console.log("[LOG][initScript] sessionStorage initialization skipped: hostname not matched");
                    }} else {{
                        console.log("[LOG][initScript] Hostname matched:", currentHostname);

                        // avoids re-initializing sessionStorage if already initialized
                        if (sessionStorageStatus !== "available") {{
                            console.log("[LOG][initScript] sessionStorage initialization skipped:", sessionStorageStatus);
                        }} else if (window.sessionStorage.getItem(sessionStorageInitMarker) === "true") {{
                            console.log("[LOG][initScript] sessionStorage initialization skipped: already initialized");
                        }} else {{
                            let restoredCount = 0;
                            const restoredKeys = [];
                            for (const [key, value] of Object.entries(sessionStorageEntries)) {{
                                const storageValue =
                                    typeof value === "string" ? value : JSON.stringify(value);
                                window.sessionStorage.setItem(key, storageValue);
                                restoredCount += 1;
                                restoredKeys.push(key);
                            }}

                            //  create a marker to indicate that sessionStorage has been initialized
                            window.sessionStorage.setItem(sessionStorageInitMarker, "true");

                            console.log("[LOG][initScript] sessionStorage initialized: ", 
                              "restoredCount=" + restoredCount + 
                              "keys=" + JSON.stringify(restoredKeys)
                            );
                            console.log("[LOG][initScript] sessionStorage initialization marker created:", sessionStorageInitMarker);
                        }}
                    }}

                    if (window[routingTraceMarker] === true) {{
                        console.log("[LOG][initScript] Client-side routing trace skipped: already installed");
                    }} else {{
                        window[routingTraceMarker] = true;

                        console.log("[LOG][initScript] Installing client-side routing trace:", window.location.href);

                        const reportUrlChange = (source) => {{
                            console.log("[LOG][initScript] URL changed:", source, window.location.href);
                        }};

                        const originalPushState = history.pushState;
                        history.pushState = function (...args) {{
                            const result = originalPushState.apply(this, args);
                            reportUrlChange("pushState");
                            return result;
                        }};

                        const originalReplaceState = history.replaceState;
                        history.replaceState = function (...args) {{
                            const result = originalReplaceState.apply(this, args);
                            reportUrlChange("replaceState");
                            return result;
                        }};

                        window.addEventListener("popstate", () => reportUrlChange("popstate"));
                        window.addEventListener("hashchange", () => reportUrlChange("hashchange"));
                    }}
                }})();
                """)

            await context.add_init_script(initScript)

        except Exception as e:
            U.throwPrefix(prefix, e)

    @classmethod
    def installPageTrace(cls, page: PwPage):
        funcName = cls.installPageTrace.__name__
        prefix = funcName
        try:

            def onConsole(message) -> None:
                if message.text.startswith("[URL_CHANGE]"):
                    U.logD(f"CLIENT ROUTE: {message.text}")
                elif message.text.startswith("[LOG]"):
                    U.logD(f"BROWSER CONSOLE: {message.text}")

            def onRequest(request: PwRequest) -> None:
                if request.is_navigation_request() and request.frame == page.main_frame:
                    redirected_from = request.redirected_from

                    if redirected_from:
                        U.logD(f"NAVIGATION REQUEST: {redirected_from.url} -> {request.url}")
                    else:
                        U.logD(f"NAVIGATION REQUEST: {request.url}")

            def onResponse(response: PwResponse) -> None:
                request = response.request

                if not (request.is_navigation_request() and request.frame == page.main_frame):
                    return
                location = response.headers.get("location")
                if 300 <= response.status < 400:
                    U.logD(
                        f"HTTP REDIRECT: {response.status} {response.url} -> {location or '<missing Location header>'}"
                    )
                else:
                    U.logD(f"NAVIGATION RESPONSE: {response.status} {response.url}")

            def onFrameNavigated(frame: PwFrame) -> None:
                if frame == page.main_frame:
                    U.logD(
                        f"BROWSER COMMITTED: {frame.url}",
                    )

            page.on("request", onRequest)
            page.on("response", onResponse)
            page.on("framenavigated", onFrameNavigated)
            page.on("console", onConsole)

        except Exception as e:
            U.throwPrefix(prefix, e)

    @classmethod
    async def dumpPageErrors(cls, page: PwPage, inputE: Exception, logDir: Path, baseNamePrefix: str = "") -> None:
        funcName = cls.dumpPageErrors.__name__
        prefix = funcName
        try:

            U.logPrefixE(prefix, f"Current page URL: {page.url}, inputE={inputE}")
            for index, current_page in enumerate(page.context.pages):
                try:
                    U.logPrefixE(
                        prefix,
                        (f"Open page[{index}]: " f"url={current_page.url}, " f"closed={current_page.is_closed()}"),
                    )

                    if current_page.is_closed():
                        U.logW(f"{funcName} cannot capture " f"screenshot on page[{index}]")
                        continue

                    await cls.dumpPageScreen(
                        current_page,
                        logDir / f"{baseNamePrefix}.p{index+1:02d}.png",
                    )

                except Exception as error:
                    U.logPrefixE(prefix, error)

        except Exception as e:
            U.logPrefixE(prefix, e)


async def main():
    funcName = main.__name__
    prefix = funcName
    page = None
    try:
        username = ""
        password = ""
        hostname = ""
        TEST_MENU = "1. UAT | 2. PROD | 0. Exit > "
        menuInt = U.askQuestionInt(TEST_MENU, {"validValues": [0, 1, 2], "isShowValidValues": False})
        match menuInt:
            case 0:
                return
            case 1:
                username = EnvConfig.get("UAT_USER")
                password = EnvConfig.get("UAT_PASSWORD")
                hostname = EnvConfig.get("UAT_HOST")

                # main_supplier_url = "https://supplier.uat1.ligentix.net/"
                # regex_NotLogin = r"^((?!supplier\.uat1\.ligentix\.net/login).)*$"
                # regex_signin_callback = r"^.*supplier\.uat1\.ligentix\.net/signin-callback.*$"
                # supplier_wildcard = "**/supplier.uat1.ligentix.net/"
                # regex_identity = r"^.*identity\.uat1\.ligentix\.net/.*$"

            case 2:
                username = EnvConfig.get("PROD_USER")
                password = EnvConfig.get("PROD_PASSWORD")
                hostname = EnvConfig.get("PROD_HOST")

                # main_supplier_url = "https://supplier.ligentix.net/"
                # regex_NotLogin = r"^((?!supplier\.ligentix\.net/login).)*$"
                # regex_signin_callback = r"^.*supplier\.ligentix\.net/signin-callback.*$"
                # supplier_wildcard = "**/supplier.ligentix.net/"
                # regex_identity = r"^.*identity\.ligentix\.net/.*$"

        if username is None or password is None or hostname is None:
            raise Exception("invalid username/password/hostname")

        ## Supplier URL: https://supplier.(uat1.)ligentix.net/
        main_supplier_url = f"https://supplier.{hostname}/"

        ## Login URL: https://supplier.(uat1.)ligentix.net/login \
        ## regex used to detect if the URL is not the login URL
        regex_NotLogin = re.compile(rf"^(?!.*supplier\.{re.escape(hostname)}/login).*$")

        ## Callback URL: https://supplier.(uat1.)ligentix.net/signin-callback?...
        regex_signin_callback = re.compile(rf"^.*supplier\.{re.escape(hostname)}/signin-callback.*$")

        supplier_wildcard = f"**/supplier.{hostname}/"

        # Identity URL: https://identity.(uat1.)ligentix.net/
        regex_identity = re.compile(rf"^.*identity\.{re.escape(hostname)}/.*$")

        popup_index = 0

        async def dump_new_page(new_page: PwPage):
            # Fires the instant a new tab/window is opened in the context (e.g. a
            # recaptcha/verification popup). Screenshot it right away, since a
            # transient popup like that can close again before dumpPageErrors's
            # own page.context.pages loop ever gets a chance to see it.
            nonlocal popup_index
            popup_index += 1
            U.logI(f"New page/tab opened in context (index={popup_index}): {new_page.url}")
            try:
                await new_page.wait_for_load_state("domcontentloaded", timeout=5000)
            except Exception:
                pass
            await PlaywrightHelper.dumpPageScreen(new_page, BrowseDataDir / f"popup.{popup_index:02d}.png")

        async with async_playwright() as p:
            try:
                session_storage = ""
                try:
                    if os.path.isfile(SessionFile) and os.path.isfile(StateFile):
                        U.logI(f"Loading session SessionStorage: {SessionFile}")
                        U.logI(f"Loading cookies and LocalStorage: {StateFile}")
                        with open(SessionFile, "r+") as f:
                            session_storage = f.read()
                            # U.logD(session_storage)
                        browser = await p.chromium.launch()
                        context = await browser.new_context(storage_state=StateFile)
                        page = await context.new_page()
                        PlaywrightHelper.installPageTrace(page)
                        await PlaywrightHelper.installInitScript(
                            context, hostname=f"supplier.{hostname}", sessionStorage=session_storage
                        )

                    else:
                        U.logW("Browser Session/LocalStorage + Cookies NOT found!")
                        browser = await p.chromium.launch()
                        context = await browser.new_context()
                        page = await context.new_page()
                        PlaywrightHelper.installPageTrace(page)
                except Exception as e:
                    U.logE(f"Error loading browser data, please delete all json file and try again ({e})")
                    raise Exception("Failed opening browser")

                context.on("page", dump_new_page)

                # Flow:
                # Base URL -> /login ->
                # Case A: /signin-callback -> /
                # Case B: identity.* -> require login
                # Direction: can't use if else on wait_for_url, so check the redirected URL after /login
                U.logI(f"Loading page: {main_supplier_url} ...")
                await page.goto(main_supplier_url, wait_until="commit")

                # ## Wait for the redirect to /login
                # ## e.g. https://supplier.(uat1.)ligentix.net/login
                # U.logI("Waiting page: **/login ...")
                # await page.wait_for_url("**/login", wait_until="commit")
                # U.logI(f"Loaded page: {page.url}")

                patterns: list[TWaitForPattern] = [
                    {
                        "name": "login",
                        ## This pattern matches
                        ## - https://supplier.(uat1.)ligentix.net/login
                        ## - https://supplier.(uat1.)ligentix.net/login/
                        ## - https://supplier.(uat1.)ligentix.net/login?returnUrl=...
                        "pattern": re.compile(rf"/login(?:[/?]|$)"),
                    },
                    {
                        "name": "supplierDashboard",
                        ## This pattern matches
                        ## - https://supplier.(uat1.)ligentix.net
                        ## - https://supplier.(uat1.)ligentix.net/
                        ## - https://supplier.(uat1.)ligentix.net/?xxx=...
                        "pattern": re.compile(rf"supplier.{re.escape(hostname)}(?:[/?]|$)"),
                    },
                ]

                waitedMatch = await PlaywrightHelper.waitForUrl(
                    page,
                    patterns,
                    isDebug=True,
                    wait_until="commit",
                    timeout=30_000,
                )
                U.logI(f"Loaded page: {page.url}")

                if waitedMatch["name"] == "supplierDashboard":
                    sessionStorage = await PlaywrightHelper.saveSessionStorage(page, SessionFile)
                    localStorageAndCookies = await PlaywrightHelper.saveLocalStorageAndCookies(context, StateFile)
                    await saveJwt()

                elif waitedMatch["name"] == "login":
                    ## Use regex to wait for a URL that isn't the login page
                    ## i.e.either the Callback URL or Identity URL
                    U.logI(f"Waiting page: (NOT login page) ...")
                    await page.wait_for_url(regex_NotLogin, wait_until="commit")
                    U.logI(f"Loaded page: {page.url}")

                    # Todo: regex to check whether the redirected URL is case 1 or 2
                    if re.match(regex_signin_callback, page.url):
                        # if await page.wait_for_url("**/supplier.uat1.ligentix.net/signin-callback**", timeout=120000):
                        U.logI("Case A: callback and wait for dashboard home page")
                        await page.wait_for_url(supplier_wildcard, timeout=240000)

                        sessionStorage = await PlaywrightHelper.saveSessionStorage(page, SessionFile)
                        localStorageAndCookies = await PlaywrightHelper.saveLocalStorageAndCookies(context, StateFile)
                        await saveJwt()
                        # await page.wait_for_url("**/supplier.uat1.ligentix.net/shipments/search", timeout=60000)
                        # await context.close()
                        # await browser.close()

                    elif re.match(regex_identity, page.url):
                        # elif await page.wait_for_url("**/identity.uat1.ligentix.net/**", timeout=120000):
                        U.logI("Case B: login required")
                        U.logD("Auto-filling credentials and logging in...")
                        await page.get_by_placeholder("Username").fill(username)  # type: ignore
                        await page.get_by_placeholder("Password").fill(password)  # type: ignore
                        await page.get_by_label("Remember me next time").check()

                        U.logI("Click button: Login to Ligentix")
                        await page.get_by_role("button", name="Login to Ligentix").click()

                        U.logD(f"Waiting page: **ligentix.net ...")
                        # await page.wait_for_url("**ligentix.net", timeout=60000 * 2)
                        await page.wait_for_url("**://*.ligentix.net/**", timeout=30000)
                        U.logI(f"Loaded page: {page.url}")

                        # still on identity page -> captcha required
                        if re.match(regex_identity, page.url):
                            U.logI("Case C: recaptcha may be required")
                            try:
                                await page.wait_for_selector('iframe[title="reCAPTCHA"]', state="visible", timeout=8000)
                                U.logI("reCAPTCHA widget rendered")
                            except PwTimeoutError:
                                U.logW(
                                    "reCAPTCHA widget did NOT render within 8s "
                                    "(likely withheld by bot detection, not just slow to load)"
                                )
                            # send alert
                            raise Exception("recaptcha required.")
                        else:
                            U.logD(f"Waiting page: {supplier_wildcard} ...")
                            await page.wait_for_url(supplier_wildcard, timeout=60000)
                            U.logI(f"Loaded page: {page.url}")

                            sessionStorage = await PlaywrightHelper.saveSessionStorage(page, SessionFile)
                            localStorageAndCookies = await PlaywrightHelper.saveLocalStorageAndCookies(
                                context, StateFile
                            )
                            await saveJwt()

                    # await page.wait_for_url("**/supplier.uat1.ligentix.net/shipments/search", timeout=60000)
                    # await context.close()
                    # await browser.close()

            except Exception as e:
                U.logPrefixE(funcName, e, __file__)
                if page is not None:
                    await PlaywrightHelper.dumpPageErrors(
                        page,
                        e,
                        BrowseDataDir,
                        baseNamePrefix="wait-for-ligentix",
                    )

    except Exception as e:
        U.logPrefixE(funcName, e, __file__)



async def saveJwt():
    with open(SessionFile, "r+") as f:
        temp = json.load(f)
        token = temp["oidc.user:https://identity.uat1.ligentix.net/:shipping-confirmation-portal-app"]
        temp2 = json.loads(token).get("access_token")
        # U.logI(f"JWT Bearer = {temp2}")
        with open(JwtFile, "w+") as f:
            f.write(temp2)
        U.logW(f"JWT: {JwtFile}")


asyncio.run(main())
