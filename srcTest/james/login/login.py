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
    Playwright,
)

########################################################
## Change to project root dir
########################################################
scriptDir = f"{os.path.dirname(__file__)}"
projRootDir = f"{os.path.dirname(__file__)}/../../.."
os.chdir(projRootDir)

########################################################
## Explicitly appends the search paths, where self-developed modules/packages are resided
## This helps consistent imports, without using relative paths.
########################################################
importDirs = ["./src/lib", scriptDir]
sysDirsToAppend: list[str] = []
for importDir in importDirs:
    if os.path.exists(importDir) and os.path.isdir(importDir):
        sys.path.append(importDir)
        sysDirsToAppend.append(importDir)

if len(sysDirsToAppend) == 0:
    raise Exception(f"import dirs not found, targetPaths={importDirs}")


from localLib import App, PlaywrightHelper, askMenu, TWaitForPattern

App.readEnv()


async def createBrowser(p: Playwright, hostname: str):
    """
    Description
    - create browser context and page, load session data on if exists
    """

    funcName = createBrowser.__name__
    prefix = funcName
    try:
        sessionStorageData: str | None = None
        isLoadBrowserSession = os.path.isfile(App.SessionFile) and os.path.isfile(App.StateFile)
        if isLoadBrowserSession:
            U.logW(f"Loading session SessionStorage: {App.SessionFile}")
            U.logW(f"Loading cookies and LocalStorage: {App.StateFile}")
            with open(App.SessionFile, "r+") as f:
                sessionStorageData = f.read()
                # U.logD(session_storage)
        else:
            U.logW("Browser Session/LocalStorage + Cookies NOT found!")

        browser = await p.chromium.launch()
        context = await browser.new_context(storage_state=App.StateFile if isLoadBrowserSession else None)
        page = await context.new_page()
        PlaywrightHelper.installPageTrace(page)
        await PlaywrightHelper.installInitScript(
            context, hostname=f"supplier.{hostname}", sessionStorage=sessionStorageData
        )
        PlaywrightHelper.installBrowserContextTrace(context, App.BrowseDataDir)

        return browser, context, page

    except Exception as e:
        U.throwPrefix(prefix, e)


async def main():
    funcName = main.__name__
    prefix = funcName
    page = None
    try:
        #######################################################################
        ## Ask for UAT or PROD
        #######################################################################
        answer = askMenu()
        if answer is None:
            return
        username, password, hostname = answer

        async with async_playwright() as p:
            try:
                dashboardHomeURL = f"https://supplier.{hostname}/"
                patterns: dict[str, TWaitForPattern] = {
                    "identityLogin": {
                        "name": "identityLogin",
                        "desc": "Identity login page",
                        ## This pattern matches
                        ## - https://identity.(uat1.)ligentix.net/Account/Login
                        ## - https://identity.(uat1.)ligentix.net/Account/Login/
                        ## - https://identity.(uat1.)ligentix.net/Account/Login?returnUrl=...
                        "pattern": re.compile(
                            rf"https://identity\.(?:.*){re.escape(hostname)}/Account/Login(?:[/?]|$)"
                        ),
                    },
                    "login": {
                        "name": "login",
                        "desc": "App login page",
                        ## This pattern matches
                        ## - https://supplier.(uat1.)ligentix.net/login
                        ## - https://supplier.(uat1.)ligentix.net/login/
                        ## - https://supplier.(uat1.)ligentix.net/login?returnUrl=...
                        "pattern": re.compile(rf"^https://supplier\.(?:.*){re.escape(hostname)}/login(?:[/?]|$)"),
                    },
                    "signinCallback": {
                        "name": "signinCallback",
                        "desc": "App signin callback",
                        ## This pattern matches
                        ## - https://supplier.(uat1.)ligentix.net/signin-callback
                        ## - https://supplier.(uat1.)ligentix.net/signin-callback/
                        ## - https://supplier.(uat1.)ligentix.net/signin-callback?code=...
                        "pattern": re.compile(
                            rf"^https://supplier\.(?:.*){re.escape(hostname)}/signin-callback(?:[/?]|$)"
                        ),
                    },
                    "dashboardHome": {
                        "name": "dashboardHome",
                        "desc": "Dashboard home page",
                        ## This patterns matches
                        ## - https://supplier.(uat1.)ligentix.net/
                        "pattern": re.compile(rf"https://supplier\.(?:.*){re.escape(hostname)}/$"),
                    },
                }

                dashboardApiPartialUrls: list[str] = [
                    "/Api/statistics/bookings",
                    "/Api/statistics/shipment/rag/count",
                ]

                ##############################################################
                ## create browser and load session if exists
                ##############################################################
                browser, context, page = await createBrowser(p, hostname)

                ##############################################################
                ## Install dashboard API response handler
                ##############################################################
                dashboardApiResponseCounters: dict[str, int] = {url: 0 for url in dashboardApiPartialUrls}
                installDashboardApiResponseEventHandler(page, dashboardApiResponseCounters)

                ##############################################################
                ## Goto supplier dashboard and wait for it (domcontentloaded)
                ##############################################################
                U.logI(f"Loading page: {dashboardHomeURL} ...")
                await page.goto(dashboardHomeURL, wait_until="commit")

                ## Wait for full page load using 'domcontentloaded'
                waitedMatch = await PlaywrightHelper.waitForUrl(
                    page,
                    patterns["dashboardHome"],
                    isDebug=True,
                    wait_until="domcontentloaded",
                    timeout=30_000,
                )
                if waitedMatch["name"] != "dashboardHome":
                    raise Exception(f"Expected to match 'dashboardHome', but got '{waitedMatch['name']}'")

                ##############################################################
                ## It may go to app logon (if this happens, it should be quick in 20sec)
                ##############################################################
                waitedMatch, waitedErr = await PlaywrightHelper.waitForUrlNotThrow(
                    page,
                    patterns["login"],
                    isDebug=True,
                    wait_until="commit",
                    timeout=20_000,
                )

                ##############################################################
                ## Case A: If login is not waited
                ## - simply wait for dashboard API response
                ##############################################################
                if waitedMatch is None:
                    isDashboardWaited = await waitForDashboardApiResponse(
                        page, dashboardApiPartialUrls, dashboardApiResponseCounters
                    )
                    if isDashboardWaited:
                        await App.saveSession(context, page, "dashboard_case_A")
                        ## Case A: wait no login and waited dashboard response
                        U.logW(f"{prefix} ✅ Case A")
                    else:
                        ## Case A.E1: wait no app login and failed to wait for dashboard API response
                        raise Exception(f"❌ Case A.E1 failure")

                ##############################################################
                ## Case B: If login can be waited
                ## - it may go to signin callback and land on dashboard home OR
                ## - go to identity logon page to fill in credentials
                ##############################################################
                else:
                    ## play safe, name must be 'login' here
                    if waitedMatch["name"] != "login":
                        raise Exception(f"unexpected waitedMatch, name={waitedMatch['name']}")

                    waitedMatch = await waitForIdentityLoginOrSigninCallback(
                        page, [patterns[key] for key in patterns.keys() if key in ["signinCallback", "identityLogin"]]
                    )
                    if waitedMatch is None:
                        ## Case B.E1: wait no signin callback nor identity login
                        raise Exception(f"❌ Case B.E1 failure")

                    if waitedMatch["name"] == "signinCallback":
                        isDashboardWaited = await waitForDashboardApiResponse(
                            page, dashboardApiPartialUrls, dashboardApiResponseCounters
                        )
                        if isDashboardWaited:
                            await App.saveSession(context, page, "dashboard_case_B1")
                            ## Case B1: waited login and signin callback, waited dashboard API response
                            U.logW(f"{prefix} ✅ Case B1")
                        else:
                            ## Case B.E2: waited signin callback and failed to wait for dashboard API response
                            raise Exception(f"❌ Case B.E2 failure")

                    elif waitedMatch["name"] == "identityLogin":
                        U.logW("RPA login required")
                        U.logD("Auto-filling credentials...")
                        await page.get_by_placeholder("Username").fill(username)  # type: ignore
                        await page.get_by_placeholder("Password").fill(password)  # type: ignore
                        await page.get_by_label("Remember me next time").check()
                        U.logW("Click button: Login to Ligentix")
                        await page.get_by_role("button", name="Login to Ligentix").click()

                        waitedMatch = await waitForIdentityLoginOrSigninCallback(
                            page,
                            [patterns[key] for key in patterns.keys() if key in ["signinCallback", "identityLogin"]],
                        )
                        if waitedMatch is None:
                            ## Case B.E3: after RPA logon, wait no signin callback and identity login
                            raise Exception(f"❌ Case B.E3 failure")

                        if waitedMatch["name"] == "signinCallback":
                            isDashboardWaited = await waitForDashboardApiResponse(
                                page, dashboardApiPartialUrls, dashboardApiResponseCounters
                            )
                            if isDashboardWaited:
                                await App.saveSession(context, page, "dashboard_B2")
                                ## Case B2: waited login and signin callback, waited dashboard API response
                                U.logW(f"{prefix} ✅ Case B2")
                            else:
                                ## Case B.E2: waited signin callback and failed to wait for dashboard API response
                                raise Exception(f"case B.E2 failure")

                        elif waitedMatch["name"] == "identityLogin":
                            U.logW("Case C: recaptcha may be required")
                            try:
                                await page.wait_for_selector('iframe[title="reCAPTCHA"]', state="visible", timeout=8000)
                                U.logI("reCAPTCHA widget rendered")
                            except PwTimeoutError:
                                U.logW(
                                    "reCAPTCHA widget did NOT render within 8s "
                                    "(likely withheld by bot detection, not just slow to load)"
                                )
                            raise Exception("recaptcha required.")

                    else:
                        raise Exception(f"unexpected waitedMatch, name={waitedMatch['name']}")

                    ## clean up
                    await context.close()
                    await browser.close()

            except Exception as e:
                U.logPrefixE(funcName, e, __file__)
                if page is not None:
                    await PlaywrightHelper.dumpPageErrors(
                        page,
                        e,
                        App.BrowseDataDir,
                        baseNamePrefix="wait-for-ligentix",
                    )

    except Exception as e:
        U.logPrefixE(funcName, e, __file__)


async def waitForDashboardApiResponse(page: PwPage, partialUrls: list[str], counters: dict[str, int]):
    funcName = waitForDashboardApiResponse.__name__
    prefix = funcName
    isDashboardWaited = False
    try:
        isAllReceived = all([counters[k] > 0 for k in counters.keys()])
        if isAllReceived:
            isDashboardWaited = True
        else:
            await PlaywrightHelper.waitForApiResponses(
                page,
                partialUrls,
                timeoutMs=60_000,
            )
            isDashboardWaited = True

    except Exception as e:
        U.logPrefixE(prefix, e)

    return isDashboardWaited


async def waitForIdentityLoginOrSigninCallback(page: PwPage, patterns: list[TWaitForPattern]):
    funcName = waitForIdentityLoginOrSigninCallback.__name__
    prefix = funcName
    waitedMatch: TWaitForPattern | None = None
    try:
        waitedMatch = await PlaywrightHelper.waitForUrl(
            page,
            patterns,
            isDebug=True,
            wait_until="commit",
            timeout=30_000,
        )
    except Exception as e:
        U.logPrefixE(prefix, e)

    return waitedMatch


def installDashboardApiResponseEventHandler(page: PwPage, counters: dict[str, int]):
    funcName = installDashboardApiResponseEventHandler.__name__
    prefix = funcName
    try:
        partialUrls = [k for k in counters.keys()]

        def onResponse(response: PwResponse) -> None:
            for s in partialUrls:
                if s in response.url and response.status == 200:
                    U.logD(f"{prefix} API responses received: {response.url}")
                    counters[s] += 1

        page.on("response", onResponse)

    except Exception as e:
        U.throwPrefix(prefix, e)


asyncio.run(main())
