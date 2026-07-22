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
import sys
import os
from pathlib import Path
import swivel.common as U
from playwright.async_api import async_playwright, Page as PwPage, TimeoutError as PwTimeoutError
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
            await dumpPageScreen(new_page, BrowseDataDir / f"popup.{popup_index:02d}.png")

        async with async_playwright() as p:
            try:
                session_storage = ""
                try:
                    if os.path.isfile(SessionFile) and os.path.isfile(StateFile):
                        U.logI(f"Loading session SessionStorage: {SessionFile}")
                        U.logI(f"Loading cookies and LocalStorage: {StateFile}")
                        with open(SessionFile, "r+") as f:
                            session_storage = f.read()
                            U.logD(session_storage)
                        browser = await p.chromium.launch()
                        context = await browser.new_context(storage_state=StateFile)
                        page = await context.new_page()
                        await context.add_init_script(
                            """(storage => {
                            if (window.location.hostname === """
                            + hostname  # type: ignore
                            + """) {
                                const entries = JSON.parse(storage)
                                for (const [key, value] of Object.entries(entries)) {
                                    window.sessionStorage.setItem(key, value)
                                }
                            }
                        })('"""
                            + session_storage
                            + "')"
                        )
                    else:
                        U.logW("Browser Session/LocalStorage + Cookies NOT found!")
                        browser = await p.chromium.launch()
                        context = await browser.new_context()
                        page = await context.new_page()
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

                ## Wait for the redirect to /login
                ## e.g. https://supplier.(uat1.)ligentix.net/login
                U.logI("Waiting page: **/login ...")
                await page.wait_for_url("**/login", wait_until="commit")
                U.logI(f"Loaded page: {page.url}")

                ## Use regex to wait for a URL that isn't the login page
                ## i.e.either the Callback URL or Identity URL
                U.logI(f"Waiting page: (NOT login page) ...")
                await page.wait_for_url(regex_NotLogin, wait_until="commit")
                U.logI(f"Loaded page: {page.url}")

                # Todo: regex to check whether the redirected URL is case 1 or 2
                if re.match(regex_signin_callback, page.url):
                    # if await page.wait_for_url("**/supplier.uat1.ligentix.net/signin-callback**", timeout=120000):
                    U.logI("Case A: callback")
                    await page.wait_for_url(supplier_wildcard, timeout=240000)

                    session_storage = await page.evaluate("() => JSON.stringify(sessionStorage)")
                    storage = await context.storage_state(path=StateFile)  # contains cookies and local storage
                    U.logD(session_storage)
                    await save_session(session_storage)
                    await extract_jwt()
                    # await page.wait_for_url("**/supplier.uat1.ligentix.net/shipments/search", timeout=60000)
                    await context.close()
                    await browser.close()

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
                        await page.wait_for_url(supplier_wildcard, timeout=240000)
                        U.logI(f"Loaded page: {page.url}")

                        session_storage = await page.evaluate("() => JSON.stringify(sessionStorage)")
                        storage = await context.storage_state(path=StateFile)  # contains cookies and local storage
                        U.logD(session_storage)
                        await save_session(session_storage)
                        # Extract JWT
                        await extract_jwt()
                    # await page.wait_for_url("**/supplier.uat1.ligentix.net/shipments/search", timeout=60000)
                    await context.close()
                    await browser.close()
            except Exception as e:
                # Handle it HERE, while browser/context/page are still alive.
                # Letting it escape the `async with` block would run Playwright's
                # __aexit__ (which stops the driver and tears down the browser)
                # before the dump ever runs, causing "page already closed".
                U.logPrefixE(funcName, e, __file__)
                if page is not None:
                    await dumpPageErrors(page, e)

    except Exception as e:
        U.logPrefixE(funcName, e, __file__)


async def dumpPageErrors(page: PwPage, inputE: Exception):
    funcName = dumpPageErrors.__name__
    prefix = funcName
    try:
        await dumpPageScreen(page, BrowseDataDir / f"wait-for-ligentix-timeout.00.png")
        if isinstance(inputE, PwTimeoutError):
            U.logPrefixE(prefix, f"Page Timed out: {page.url}")
        else:
            U.logPrefixE(prefix, f"Page URL: {page.url}")
        for index, current_page in enumerate(page.context.pages):
            U.logPrefixE(prefix, f"Open page[{index}]: url={current_page.url}, closed={current_page.is_closed()}")
            try:
                if current_page.is_closed():
                    U.logW(f"{prefix} cannot capture screenshot on page[{index}]")
                else:
                    await dumpPageScreen(current_page, BrowseDataDir / f"wait-for-ligentix-timeout.{index+1:02d}.png")
            except Exception as e2:
                U.logPrefixE(prefix, e2)

    except Exception as e:
        U.logPrefixE(prefix, e)


async def dumpPageScreen(page: PwPage, imageFile: Path):
    funcName = dumpPageScreen.__name__
    prefix = funcName
    try:
        prefix = f"{prefix}[{page.url}]"
        await page.screenshot(
            path=imageFile,
            full_page=True,
        )
        U.logW(f"{prefix} {imageFile}")

    except Exception as e:
        U.logPrefixE(prefix, e)


async def save_session(session_storage_data):
    with open(SessionFile, "w+") as f:
        f.write(session_storage_data)
    U.logI("Session storage and cookies saved!")


async def extract_jwt():
    with open(SessionFile, "r+") as f:
        temp = json.load(f)
        token = temp["oidc.user:https://identity.uat1.ligentix.net/:shipping-confirmation-portal-app"]
        temp2 = json.loads(token).get("access_token")
        U.logI(f"JWT Bearer = {temp2}")
        with open(JwtFile, "w+") as f:
            f.write(temp2)


asyncio.run(main())
