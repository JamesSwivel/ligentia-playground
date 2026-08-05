import asyncio
import json
import re
from textwrap import dedent
import os
import sys
from pathlib import Path
from typing import Callable, Literal, cast, Any, Mapping
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

"""
- For page.wait_for_url(pattern, wait_until="xxx", timeout=timeoutMs) where xxx:
  'commit': network response received, document started loading. For pure SPA route changes
    (history.pushState, no new document), there's nothing to "commit" in the strict sense —
    but since 'commit' doesn't depend on document-lifecycle events that only fire for a real
    page load, it doesn't get stuck waiting on something that will never re-fire. In practice
    this makes it resolve as soon as the URL matches, for both real navigations and SPA route
    changes — which is why it "sees" SPA transitions even though no actual commit occurs.
  'domcontentloaded': HTML doc is parsed but other blocking resources, e.g. image loading, JavaScript invoking, are still in progress
  'load': when browser window fires 'load' event, which means the page and virtually all its resources have finished loading
- default timeout is 30_000, i.e. 30K msec = 30sec

"""


class TWaitForPattern(TypedDict):
    name: str
    """name of the pattern"""
    desc: str
    """description of the pattern"""
    pattern: re.Pattern
    """regex pattern to match the URL"""


class PlaywrightHelper:

    ON_PAGE_INDEX: int = 0

    class ForExitError(Exception):
        """A custom Exception for exiting try/exception block"""

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
        patterns: list[TWaitForPattern] | TWaitForPattern,
        *,
        isDebug: bool = False,
        wait_until: Literal["commit", "domcontentloaded", "load", "networkidle", None] = "load",
        **kwargs,
    ) -> TWaitForPattern:
        """
        ### Description
        - Enhanced version of wait_for_url() that support waiting for multiple regex in form of regex list
        """
        funcName = cls.waitForUrl.__name__
        prefix = funcName
        try:
            """Wait for a URL that matches any of the given patterns, and return the matched pattern."""
            if not isinstance(patterns, list):
                patterns = [patterns]

            timeoutSec = 30_000 / 1000.0
            if "timeout" in kwargs:
                timeoutSec = kwargs["timeout"] / 1000.0

            if isDebug:
                U.logD(
                    f"{prefix} waiting for URLs[{wait_until}][{timeoutSec:.0f}s]: {[p['name'] for p in patterns]} ..."
                )

            predicate = cls.makeUrlPatternPredicate(patterns)
            await page.wait_for_url(predicate, wait_until=wait_until, **kwargs)
            matchedPattern = cls.findMatchedPattern(page.url, patterns)
            if matchedPattern is None:
                raise Exception(f"wait_for_url() returned but no pattern matched the URL: {page.url}")
            if isDebug:
                U.logD(f"{prefix} loaded URL[{wait_until}].match[{matchedPattern['name']}]: {page.url}")
            return matchedPattern
        except Exception as e:
            U.throwPrefix(prefix, e)

    @classmethod
    async def waitForUrlNotThrow(
        cls,
        page: PwPage,
        patterns: list[TWaitForPattern] | TWaitForPattern,
        *,
        isDebug: bool = False,
        wait_until: Literal["commit", "domcontentloaded", "load", "networkidle", None] = "load",
        **kwargs,
    ) -> tuple[TWaitForPattern | None, Exception | None]:
        """
        ### Description
        - not throw version of waitForUrl
        """

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
            # U.logPrefixE(prefix, e)
            err = e
        return matched, err

    @classmethod
    async def waitForApiResponses(cls, page: PwPage, urlSubstrings: list[str], timeoutMs: int = 30_000) -> None:
        """
        ### Description
        - Sometimes, it is useful to wait for API responses instead of URLs
        """
        funcName = cls.waitForApiResponses.__name__
        prefix = funcName

        ## initially, all urlSubstrings are not seen, i.e. False
        seen = {s: False for s in urlSubstrings}

        def onResponse(response: PwResponse) -> None:
            for s in urlSubstrings:
                if s in response.url and response.status == 200:
                    U.logD(f"{prefix} API responses received: {response.url}")
                    seen[s] = True

        ## event listeners are stacked but NOT overwriting the older handlers
        ## Thus, it has to be removed after used
        page.on("response", onResponse)

        try:
            U.logD(f"{prefix} Waiting for API responses: {urlSubstrings} ...")
            deadline = asyncio.get_event_loop().time() + timeoutMs / 1000
            while not all(seen.values()):
                if asyncio.get_event_loop().time() > deadline:
                    missing = [s for s, ok in seen.items() if not ok]
                    errMessage = f"Timed out waiting for API responses: {missing}"
                    U.logPrefixE(prefix, errMessage)
                    raise PwTimeoutError(errMessage)
                await asyncio.sleep(0.05)
            U.logD(f"{prefix} All API responses received")

        finally:
            ## remove the event listener
            page.remove_listener("response", onResponse)

    @classmethod
    async def dumpPageScreen(
        cls,
        page: PwPage,
        imageFile: Path,
        *,
        isWaitDomContentLoaded: bool = True,
        waitDomContentLoadedTimeout: int = 30_000,
        maxAttempts: int = 3,
    ) -> bool:
        funcName = cls.dumpPageScreen.__name__
        prefix = funcName
        isSaveOK = False
        try:
            prefix = f"{prefix}[{page.url}]"

            if page.is_closed():
                raise cls.ForExitError(f"page already closed")

            if isWaitDomContentLoaded:
                try:
                    await page.wait_for_load_state("domcontentloaded", timeout=waitDomContentLoadedTimeout)
                except Exception as eWaitLoad:
                    U.logPrefixE(prefix, eWaitLoad)

            ## It allows to capture the screenshot by a few attempts
            for attempt in range(1, maxAttempts + 1):
                try:
                    if page.is_closed():
                        raise cls.ForExitError(f"page closed before screenshot")
                    await page.screenshot(
                        path=imageFile,
                        full_page=True,
                        animations="disabled",
                        timeout=10_000,
                    )
                    U.logW(f"{prefix} {imageFile}")
                    return True

                except cls.ForExitError:
                    raise

                except Exception as e:
                    U.logW(f"{prefix} screenshot attempt " f"{attempt}/{maxAttempts} failed: {e}")
                    if attempt < maxAttempts:
                        await asyncio.sleep(0.5 * attempt)

            ## Full-page screenshot may fail when the page is changing,
            ## navigating, or temporarily too large to capture.
            U.logW(f"{prefix} falling back to viewport screenshot")

            await page.screenshot(
                path=imageFile,
                full_page=False,
                animations="disabled",
                timeout=10_000,
            )
            isSaveOK = True
            U.logW(f"{prefix} {imageFile} [viewport fallback]")

        except cls.ForExitError as e1:
            U.logW(f"{prefix} {e1}")

        except Exception as e:
            U.logPrefixE(prefix, e)

        return isSaveOK

    @classmethod
    async def saveSessionStorage(cls, page: PwPage, sessionFilePath: Path):
        funcName = cls.saveSessionStorage.__name__
        prefix = funcName
        isEmpty = True
        try:
            prefix = f"{prefix}[{page.url}]"
            sessionStorageStr = await page.evaluate("() => JSON.stringify(sessionStorage)")
            js = U.toDictNotThrow(sessionStorageStr)
            if len(js) == 0:
                U.logW(f"{prefix} sessionStorage is empty")
            else:
                await U.SwAsyncFile.writeJsonFileFromDict(str(sessionFilePath), js, isIndent=True)
                U.logW(f"{prefix} {sessionFilePath}")
                isEmpty = False
            return js, isEmpty
        except Exception as e:
            U.throwPrefix(prefix, e)

    @classmethod
    async def saveLocalStorageAndCookies(cls, ctx: PwBrowserContext, sessionFilePath: Path):
        funcName = cls.saveLocalStorageAndCookies.__name__
        prefix = funcName
        isEmpty = True
        try:
            ## The storage has shape
            ## {
            ##   "cookies": [...],
            ##   "origins": [...]
            ## }
            storage = await ctx.storage_state()  # contains cookies and local storage
            js = dict(storage)

            isSave = False
            if len(js) > 0:
                cookies = js.get("cookies", [])
                origins = js.get("origins", [])
                if isinstance(cookies, list) and len(cookies) > 0 and isinstance(origins, list) and len(origins) > 0:
                    isSave = True

            if isSave:
                await U.SwAsyncFile.writeJsonFileFromDict(str(sessionFilePath), js, isIndent=True)
                U.logW(f"{prefix} {sessionFilePath}")
                isEmpty = False
            else:
                U.logW(f"{prefix} storage_state is empty")
            return js, isEmpty
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
                //console.log("[LOG][initScript] running initScript...");
                (() => {{
                    const targetHostname = {json.dumps(hostname)};
                    const currentHostname = window.location.hostname;

                    const sessionStorageStatus = {json.dumps(sessionStorageStatus)};
                    const sessionStorageEntries = {json.dumps(sessionStorageData, ensure_ascii=False)};
                    const sessionStorageInitMarker = "__playwrightSessionStorageInitialized__";
                    const routingTraceMarker = "__playwrightRoutingTraceInstalled__";

                    // restores session storage for the specified hostname
                    if (currentHostname !== targetHostname) {{
                        //console.log("[LOG][initScript] Hostname not matched:", "expected=" + targetHostname, "actual=" + currentHostname);
                        //console.log("[LOG][initScript] sessionStorage initialization skipped: hostname not matched");
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
                        //console.log("[LOG][initScript] Installing client-side routing trace:", window.location.href);
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
                elif request.resource_type in ("xhr", "fetch"):
                    U.logD(f"XHR/FETCH REQUEST: {request.method} {request.url}")

            def onRequestFailed(request: PwRequest) -> None:
                if request.frame != page.main_frame:
                    return
                failure = request.failure
                kind = "NAVIGATION" if request.is_navigation_request() else request.resource_type.upper()
                U.logD(f"{kind} REQUEST FAILED: {request.url}  reason={failure}")

            def onResponse(response: PwResponse) -> None:
                if response.request.frame != page.main_frame:
                    return

                if response.request.is_navigation_request():
                    U.logD(f"NAVIGATION RESPONSE: {response.status} {response.url}")
                elif response.request.resource_type in ("xhr", "fetch"):
                    # Flag auth-relevant status codes explicitly, adjust as needed
                    marker = ""
                    if response.status in (401, 403):
                        marker = "  <-- AUTH FAILURE"
                    U.logD(f"XHR/FETCH RESPONSE: {response.status} {response.url}{marker}")

            def onDomContentLoaded(page: PwPage) -> None:
                U.logD(f"DOM CONTENT LOADED: {page.url}")

            def onLoad(page: PwPage) -> None:
                U.logD(f"LOAD COMPLETE: {page.url}")

            def onFrameNavigated(frame: PwFrame) -> None:
                if frame == page.main_frame:
                    U.logD(f"BROWSER COMMITTED: {frame.url}")

            page.on("request", onRequest)
            page.on("response", onResponse)
            page.on("framenavigated", onFrameNavigated)
            page.on("domcontentloaded", onDomContentLoaded)
            page.on("load", onLoad)
            page.on("console", onConsole)

            page.on("requestfailed", onRequestFailed)

        except Exception as e:
            U.throwPrefix(prefix, e)

    @classmethod
    def installBrowserContextTrace(cls, ctx: PwBrowserContext, dataPath: Path):
        funcName = cls.installBrowserContextTrace.__name__
        prefix = funcName
        try:

            async def onPage(new_page: PwPage):
                U.logI(f"New page/tab opened[{cls.ON_PAGE_INDEX}]: {new_page.url}")
                isLoaded = False
                try:
                    await new_page.wait_for_load_state("domcontentloaded", timeout=30_000)
                    isLoaded = True
                    cls.ON_PAGE_INDEX += 1
                except Exception:
                    pass
                if isLoaded:
                    await PlaywrightHelper.dumpPageScreen(new_page, dataPath / f"popup.{cls.ON_PAGE_INDEX:02d}.png")

            ctx.on("page", onPage)

        except Exception as e:
            U.throwPrefix(prefix, e)

    @classmethod
    async def dumpPageErrors(cls, page: PwPage, inputE: Exception, logDir: Path, imageBaseNamePrefix: str = "") -> None:
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
                        logDir / f"{imageBaseNamePrefix}.p{index+1:02d}.png",
                    )

                except Exception as error:
                    U.logPrefixE(prefix, error)

        except Exception as e:
            U.logPrefixE(prefix, e)
