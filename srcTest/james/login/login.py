# Flow:
# login first to save the authentication state
# > https://playwright.dev/python/docs/auth
#  store the JWT into a file
# use it to send requests to APIs
# if the JWT expires, run the process of reauthentication
import asyncio
import json
import re
import os
from pathlib import Path
import swivel.common as U
from playwright.async_api import async_playwright
from dotenv import dotenv_values

script_dir = Path(__file__).resolve().parent
env_file = script_dir / ".env"
config = dotenv_values(env_file)
session_file = script_dir / "temp/session.json"
state_file = script_dir / "temp/state.json"
jwt_file = script_dir / "temp/jwt.txt"


async def main():
    funcName = main.__name__
    prefix = funcName
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
                username = config.get("UAT_USER")
                password = config.get("UAT_PASSWORD")
                hostname = config.get("UAT_HOST")

                # main_supplier_url = "https://supplier.uat1.ligentix.net/"
                # regex_NotLogin = r"^((?!supplier\.uat1\.ligentix\.net/login).)*$"
                # regex_signin_callback = r"^.*supplier\.uat1\.ligentix\.net/signin-callback.*$"
                # supplier_wildcard = "**/supplier.uat1.ligentix.net/"
                # regex_identity = r"^.*identity\.uat1\.ligentix\.net/.*$"

            case 2:
                username = config.get("PROD_USER")
                password = config.get("PROD_PASSWORD")
                hostname = config.get("PROD_HOST")

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

        async with async_playwright() as p:
            session_storage = ""
            try:
                if os.path.isfile(session_file) and os.path.isfile(state_file):
                    U.logI(f"Loading session SessionStorage: {session_file}")
                    U.logI(f"Loading cookies and LocalStorage: {state_file}")
                    with open(session_file, "r+") as f:
                        session_storage = f.read()
                        U.logD(session_storage)
                    browser = await p.chromium.launch()
                    context = await browser.new_context(storage_state=state_file)
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
                storage = await context.storage_state(path=state_file)  # contains cookies and local storage
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
                await page.wait_for_url("**ligentix.net", timeout=60000)
                U.logI(f"Loaded page: {page.url}")

                # still on identity page -> captcha required
                if re.match(regex_identity, page.url):
                    U.logI("Case C: recaptcha required")
                    # send alert
                    raise Exception("recaptcha required.")
                else:
                    U.logD(f"Waiting page: {supplier_wildcard} ...")
                    await page.wait_for_url(supplier_wildcard, timeout=240000)
                    U.logI(f"Loaded page: {page.url}")

                    session_storage = await page.evaluate("() => JSON.stringify(sessionStorage)")
                    storage = await context.storage_state(path=state_file)  # contains cookies and local storage
                    U.logD(session_storage)
                    await save_session(session_storage)
                    # Extract JWT
                    await extract_jwt()
                # await page.wait_for_url("**/supplier.uat1.ligentix.net/shipments/search", timeout=60000)
                await context.close()
                await browser.close()
    except Exception as e:
        U.logPrefixE(funcName, e, __file__)


async def save_session(session_storage_data):
    with open(session_file, "w+") as f:
        f.write(session_storage_data)
    U.logI("Session storage and cookies saved!")


async def extract_jwt():
    with open(session_file, "r+") as f:
        temp = json.load(f)
        token = temp["oidc.user:https://identity.uat1.ligentix.net/:shipping-confirmation-portal-app"]
        temp2 = json.loads(token).get("access_token")
        U.logI(f"JWT Bearer = {temp2}")
        with open(jwt_file, "w+") as f:
            f.write(temp2)


asyncio.run(main())
