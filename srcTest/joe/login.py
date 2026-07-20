# Flow:
# login first to save the authentication state
# > https://playwright.dev/python/docs/auth
#  store the JWT into a file
# use it to send requests to APIs
# if the JWT expires, run the process of reauthentication
import asyncio
import json
import re
import os.path
import swivel.common as U
from playwright.async_api import async_playwright
from dotenv import dotenv_values

config = dotenv_values(".env")


async def main():
    funcName = main.__name__
    prefix = funcName
    try:
        # main_supplier_url = ""
        # regex_notlogin = ""
        # regex_signin_callback = ""
        # supplier_wildcard = ""
        # regex_identity = ""

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
                # regex_notlogin = r"^((?!supplier\.uat1\.ligentix\.net\/login).)*$"
                # regex_signin_callback = r"^.*supplier\.uat1\.ligentix\.net\/signin-callback.*$"
                # supplier_wildcard = "**/supplier.uat1.ligentix.net/"
                # regex_identity = r"^.*identity\.uat1\.ligentix\.net\/.*$"

            case 2:
                username = config.get("PROD_USER")
                password = config.get("PROD_PASSWORD")
                hostname = config.get("PROD_HOST")

                # main_supplier_url = "https://supplier.ligentix.net/"
                # regex_notlogin = r"^((?!supplier\.ligentix\.net\/login).)*$"
                # regex_signin_callback = r"^.*supplier\.ligentix\.net\/signin-callback.*$"
                # supplier_wildcard = "**/supplier.ligentix.net/"
                # regex_identity = r"^.*identity\.ligentix\.net\/.*$"

        main_supplier_url = f"https://supplier.{hostname}/"
        regex_notlogin = re.compile(r"^((?!supplier\.{}\/login).)*$".format(re.escape(hostname)))
        regex_signin_callback = re.compile(r"^.*supplier\.{}\/signin-callback.*$".format(re.escape(hostname)))
        supplier_wildcard = f"**/supplier.{hostname}/"
        regex_identity = re.compile(r"^.*identity\.{}\/.*$".format(re.escape(hostname)))

        # print(regex_notlogin.pattern)
        # print(regex_signin_callback.pattern)
        # print(regex_identity.pattern)

        async with async_playwright() as p:
            session_storage = ""
            try:
                if os.path.isfile("session.json") and os.path.isfile("state.json"):
                    print("loading existing browser data")
                    with open("session.json", "r+") as f:
                        session_storage = f.read()
                        print(session_storage)
                    browser = await p.chromium.launch(headless=False)
                    context = await browser.new_context(storage_state="state.json")
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
                    print("no existing browser data")
                    browser = await p.chromium.launch()
                    context = await browser.new_context()
                    page = await context.new_page()
            except Exception as e:
                print(f"Error loading browser data, please delete all json file and try again ({e})")
            print("page loading...")
            # Flow:
            # Base URL -> /login ->
            # Case A: /signin-callback -> /
            # Case B: identity.* -> require login
            # Direction: can't use if else on wait_for_url, so check the redirected URL after /login
            await page.goto(main_supplier_url, wait_until="commit")
            print("page loaded")
            # Wait for the /login redirect
            await page.wait_for_url("**/login", wait_until="commit")
            print(page.url)
            # Use regex to wait for a URL that isn't the login page
            await page.wait_for_url(regex_notlogin, wait_until="commit")
            print(page.url)
            # Todo: regex to check whether the redirected URL is case 1 or 2
            if re.match(regex_signin_callback, page.url):
                # if await page.wait_for_url("**/supplier.uat1.ligentix.net/signin-callback**", timeout=120000):
                print("Case A: callback")
                await page.wait_for_url(supplier_wildcard, timeout=240000)

                session_storage = await page.evaluate("() => JSON.stringify(sessionStorage)")
                storage = await context.storage_state(path="state.json")  # contains cookies and local storage
                print(session_storage)
                with open("session.json", "w+") as f:
                    f.write(session_storage)
                print("Session storage and cookies saved!")
                # await page.wait_for_url("**/supplier.uat1.ligentix.net/shipments/search", timeout=60000)
                await context.close()
                await browser.close()
            elif re.match(regex_identity, page.url):
                # elif await page.wait_for_url("**/identity.uat1.ligentix.net/**", timeout=120000):
                print("Case B: login required")
                #     print("login screen loaded")
                #     print(config.get("UAT_USER"))
                await page.get_by_placeholder("Username").fill(username)  # type: ignore
                await page.get_by_placeholder("Password").fill(password)  # type: ignore
                await page.get_by_label("Remember me next time").check()
                await page.get_by_role("button", name="Login to Ligentix").click()

                # await page.wait_for_url("**/supplier.uat1.ligentix.net/", timeout=240000)
                await page.wait_for_url("**ligentix.net", timeout=60000)
                print(page.url)
                # still on identity page -> captcha required
                if re.match(regex_identity, page.url):
                    print("Case C: recaptcha required")
                    # send alert
                else:
                    await page.wait_for_url(supplier_wildcard, timeout=240000)
                    session_storage = await page.evaluate("() => JSON.stringify(sessionStorage)")
                    storage = await context.storage_state(path="state.json")  # contains cookies and local storage
                    print(session_storage)
                    with open("session.json", "w+") as f:
                        f.write(session_storage)
                    print("Session storage and cookies saved!")
                # await page.wait_for_url("**/supplier.uat1.ligentix.net/shipments/search", timeout=60000)
                await context.close()
                await browser.close()
    except Exception as e:
        U.logPrefixE(funcName, e, __file__)


asyncio.run(main())
