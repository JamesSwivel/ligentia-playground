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


async def main():
    funcName = main.__name__
    prefix = funcName
    page = None
    try:
        answer = askMenu()
        if answer is None:
            return
        username, password, hostname = answer

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

        async with async_playwright() as p:
            try:

                #######################################################################
                ## create browser context and page, load session data on if exists
                #######################################################################
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

                except Exception as e:
                    U.throwPrefix(prefix, e)

                # Flow:
                # Base URL -> /login ->
                # Case A: /signin-callback -> /
                # Case B: identity.* -> require login
                # Direction: can't use if else on wait_for_url, so check the redirected URL after /login
                U.logI(f"Loading page: {main_supplier_url} ...")
                await page.goto(main_supplier_url, wait_until="commit")
                # await page.goto(main_supplier_url, wait_until="domcontentloaded")

                # ## Wait for the redirect to /login
                # ## e.g. https://supplier.(uat1.)ligentix.net/login
                # U.logI("Waiting page: **/login ...")
                # await page.wait_for_url("**/login", wait_until="commit")
                # U.logI(f"Loaded page: {page.url}")

                patterns: dict[str, TWaitForPattern] = {
                    "identityLogin": {
                        "name": "identityLogin",
                        "desc": "Identity login page",
                        ## This pattern matches
                        ## - https://identity.uat1.ligentix.net/Account/Login
                        ## - https://identity.ligentix.net/Account/Login
                        "pattern": re.compile(rf"{re.escape(hostname)}/Account/Login(?:[/?]|$)"),
                    },
                    "login": {
                        "name": "login",
                        "desc": "Login page",
                        ## This pattern matches
                        ## - https://supplier.(uat1.)ligentix.net/login
                        ## - https://supplier.(uat1.)ligentix.net/login/
                        ## - https://supplier.(uat1.)ligentix.net/login?returnUrl=...
                        "pattern": re.compile(rf"/login(?:[/?]|$)", re.IGNORECASE),
                    },
                    "dashboardHome": {
                        "name": "dashboardHome",
                        "desc": "Dashboard home page",
                        ## This pattern matches
                        ## - https://supplier.(uat1.)ligentix.net
                        ## - https://supplier.(uat1.)ligentix.net/
                        ## - https://supplier.(uat1.)ligentix.net/?xxx=...
                        # "pattern": re.compile(rf"supplier.{re.escape(hostname)}(?:[/?]|$)", re.IGNORECASE),
                        ##
                        ## This patterns matches
                        ## - https://supplier.(uat1.)ligentix.net/ (without any query params)
                        "pattern": re.compile(rf"supplier.{re.escape(hostname)}/$", re.IGNORECASE),
                    },
                }

                ## Wait for full page load using 'domcontentloaded'
                waitedMatch = await PlaywrightHelper.waitForUrl(
                    page,
                    patterns["dashboardHome"],
                    isDebug=True,
                    wait_until="domcontentloaded",
                    timeout=30_000,
                )
                if waitedMatch["name"] != "dashboardHome":
                    raise Exception(f"Expected to match dashboardHome, but got {waitedMatch['name']}")

                isDashboardWaited = False
                try:
                    await PlaywrightHelper.waitForApiResponses(
                        page,
                        [
                            "/Api/statistics/bookings",
                            "/Api/statistics/shipment/rag/count",
                        ],
                        timeoutMs=20_000,
                    )
                    isDashboardWaited = True
                except Exception as eWaitDashboard:
                    U.logW(f"{eWaitDashboard}")

                if isDashboardWaited:
                    await App.saveSession(context, page, "dashboard_1")
                else:
                    waitedMatch = await PlaywrightHelper.waitForUrl(
                        page,
                        patterns["login"],
                        isDebug=True,
                        wait_until="domcontentloaded",
                        timeout=30_000,
                    )

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

                        await App.saveSession(context, page, "dashboard_2")
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

                            await App.saveSession(context, page, "dashboard_3")

                    # await page.wait_for_url("**/supplier.uat1.ligentix.net/shipments/search", timeout=60000)
                    # await context.close()
                    # await browser.close()

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


# async def saveJwt():
#     with open(SessionFile, "r+") as f:
#         temp = json.load(f)
#         token = temp["oidc.user:https://identity.uat1.ligentix.net/:shipping-confirmation-portal-app"]
#         temp2 = json.loads(token).get("access_token")
#         # U.logI(f"JWT Bearer = {temp2}")
#         with open(JwtFile, "w+") as f:
#             f.write(temp2)
#         U.logW(f"JWT: {JwtFile}")


asyncio.run(main())
