# Playwright Python: reliable waiting, exception handling, and troubleshooting

The biggest change in mindset is:

> **Do not wait for “the page to finish.” Wait for the specific state your next action requires.**

Modern web applications may continue loading data, running JavaScript, opening popups, redirecting, or updating the DOM long after `load` fires. Playwright’s locators and assertions are designed to wait for concrete conditions rather than an abstract “fully loaded” state. ([Playwright][1])

---

## 1. Prefer locators and assertions over manual waits

Playwright automatically waits before actions such as `click()` until the element:

* Resolves to exactly one element
* Is visible
* Is stable
* Can receive pointer events
* Is enabled

If these conditions are not met before the timeout, the action raises `playwright.async_api.TimeoutError`. ([Playwright][1])

```python
from playwright.async_api import Page, expect

async def submitLogin(page: Page) -> None:
    await page.get_by_label("Username").fill("james")
    await page.get_by_label("Password").fill("secret")
    await page.get_by_role("button", name="Sign in").click()

    await expect(page.get_by_role("heading", name="Dashboard")).to_be_visible()
```

This is better than:

```python
await page.wait_for_timeout(3000)
await page.locator("#submit").click()
```

A fixed wait is simultaneously:

* Too long when the page responds quickly
* Too short when the page responds slowly
* Unable to confirm that the correct state was reached

Use `wait_for_timeout()` mainly for interactive debugging. Never use `time.sleep()` inside async Playwright code because it blocks the event loop and can prevent Playwright operations from progressing correctly. ([Playwright][2])

---

# 2. Understand the different things you may be waiting for

Several waits sound similar but solve different problems.

## A. Waiting for a URL

Use this when the URL itself is the important result:

```python
await page.get_by_role("button", name="Sign in").click()

await page.wait_for_url(
    "**/dashboard",
    timeout=30_000,
)
```

A string without wildcard characters is an exact URL match. Therefore, this can easily time out:

```python
await page.wait_for_url("https://example.com/dashboard")
```

when the actual URL is:

```text
https://example.com/dashboard/
https://example.com/dashboard?tab=home
https://example.com/dashboard#summary
```

`wait_for_url()` accepts a glob, regex, or predicate. ([Playwright][3])

### Glob pattern

```python
await page.wait_for_url("**/dashboard**")
```

### Regular expression

```python
import re

await page.wait_for_url(
    re.compile(r"/dashboard(?:[/?#]|$)")
)
```

### Predicate

Useful when query parameters or multiple valid destinations exist:

```python
from urllib.parse import urlparse

await page.wait_for_url(
    lambda url: urlparse(url).path.rstrip("/") == "/dashboard"
)
```

## B. Asserting the eventual URL

For testing, an assertion usually gives better failure output:

```python
import re
from playwright.async_api import expect

await expect(page).to_have_url(
    re.compile(r"/dashboard(?:[/?#]|$)"),
    timeout=30_000,
)
```

Playwright assertions automatically retry until the condition succeeds or times out. ([Playwright][4])

## C. Waiting for a visible UI result

Often this is more reliable than waiting only for a URL:

```python
await page.get_by_role("button", name="Sign in").click()

await expect(
    page.get_by_role("heading", name="Dashboard")
).to_be_visible()
```

Single-page applications can change their content without performing a traditional document navigation. Conversely, a URL may become correct before the dashboard data is usable.

A strong pattern is to verify both:

```python
await page.get_by_role("button", name="Sign in").click()

await page.wait_for_url("**/dashboard**")

await expect(
    page.get_by_test_id("dashboard-ready")
).to_be_visible()
```

## D. Waiting for a network response

Use this when an API call determines success:

```python
async with page.expect_response(
    lambda response:
        "/api/login" in response.url
        and response.request.method == "POST"
) as responseInfo:
    await page.get_by_role("button", name="Sign in").click()

response = await responseInfo.value

if not response.ok:
    body = await response.text()
    raise RuntimeError(
        f"Login API failed: status={response.status}, body={body[:500]}"
    )
```

## E. Waiting for a popup or new tab

Waiting on the original page’s URL will never work when the action opens another page:

```python
async with page.expect_popup() as popupInfo:
    await page.get_by_role("link", name="Open report").click()

popup = await popupInfo.value
await popup.wait_for_load_state("domcontentloaded")
await popup.wait_for_url("**/report/**")
```

You should then operate on `popup`, not the original `page`.

## F. Waiting for a download

A download may replace an expected navigation:

```python
async with page.expect_download() as downloadInfo:
    await page.get_by_role("button", name="Download").click()

download = await downloadInfo.value
await download.save_as("/tmp/report.pdf")
```

Navigation intent can be transformed into a download, so waiting for a URL in that case would time out. ([Playwright][5])

---

# 3. Avoid race conditions around actions

You need to start listening **before** the action when waiting for an event that might happen immediately.

Correct:

```python
async with page.expect_response("**/api/save") as responseInfo:
    await page.get_by_role("button", name="Save").click()

response = await responseInfo.value
```

Potentially racy:

```python
await page.get_by_role("button", name="Save").click()

# The response may already have happened.
response = await page.wait_for_response("**/api/save")
```

The same principle applies to:

* `expect_popup()`
* `expect_download()`
* `expect_request()`
* `expect_response()`
* `expect_file_chooser()`

For URL changes, the current official guidance favors `wait_for_url()`; `expect_navigation()` is documented as inherently racy and deprecated. ([Playwright][3])

---

# 4. Separate Playwright timeouts from other exceptions

Import Playwright’s exception classes with explicit aliases:

```python
from playwright.async_api import (
    Error as PlaywrightError,
    TimeoutError as PlaywrightTimeoutError,
)
```

All Playwright-specific exceptions inherit from `PlaywrightError`. `PlaywrightTimeoutError` identifies operations terminated because their timeout expired. ([Playwright][6])

A useful structure is:

```python
async def runWorkflow(page):
    try:
        await page.goto(
            "https://example.com/login",
            wait_until="domcontentloaded",
            timeout=30_000,
        )

        await page.get_by_label("Username").fill("james")
        await page.get_by_label("Password").fill("secret")

        await page.get_by_role("button", name="Sign in").click()
        await page.wait_for_url("**/dashboard**", timeout=30_000)

    except PlaywrightTimeoutError as error:
        await collectDiagnostics(page, error, errorType="timeout")
        raise

    except PlaywrightError as error:
        await collectDiagnostics(page, error, errorType="playwright")
        raise

    except Exception as error:
        await collectDiagnostics(page, error, errorType="unexpected")
        raise
```

The order matters:

```python
except PlaywrightTimeoutError:
```

must come before:

```python
except PlaywrightError:
```

because timeout errors are also Playwright errors.

## Do not silently swallow exceptions

Avoid:

```python
try:
    await page.click("#submit")
except Exception:
    pass
```

This makes the workflow continue from an unknown state and usually creates a misleading error later.

Instead:

```python
except PlaywrightTimeoutError as error:
    await collectDiagnostics(page, error, "submit-timeout")
    raise
```

Or wrap it with more context:

```python
except PlaywrightTimeoutError as error:
    raise RuntimeError(
        f"Login did not reach dashboard. Current URL: {safePageUrl(page)}"
    ) from error
```

Using `raise ... from error` preserves the original exception chain.

---

# 5. A robust diagnostic collector

Diagnostics can also fail. For example:

* The page was closed
* The browser context was closed
* The browser process crashed
* The page is still navigating
* The screenshot itself timed out
* The output directory does not exist
* The page is an unusual target that cannot currently render
* `full_page=True` requires significant rendering or scrolling

Therefore, each diagnostic operation should be protected independently.

```python
from __future__ import annotations

import asyncio
import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

from playwright.async_api import Page


def safePageUrl(page: Page | None) -> str:
    if page is None:
        return "<no-page>"

    try:
        return page.url
    except Exception as error:
        return f"<url-unavailable: {error}>"


async def collectDiagnostics(
    page: Page | None,
    error: BaseException,
    errorType: str,
    outputDir: Path = Path("playwright-errors"),
) -> None:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    diagnosticDir = outputDir / f"{timestamp}-{errorType}"

    try:
        diagnosticDir.mkdir(parents=True, exist_ok=True)
    except Exception:
        # There is nowhere reliable to save additional diagnostics.
        return

    metadata: dict[str, Any] = {
        "errorType": errorType,
        "exceptionClass": type(error).__name__,
        "exceptionMessage": str(error),
        "traceback": "".join(
            traceback.format_exception(type(error), error, error.__traceback__)
        ),
        "pageUrl": safePageUrl(page),
    }

    if page is None:
        await writeJsonSafely(
            diagnosticDir / "metadata.json",
            metadata,
        )
        return

    try:
        metadata["pageClosed"] = page.is_closed()
    except Exception as diagnosticError:
        metadata["pageClosedError"] = repr(diagnosticError)

    try:
        context = page.context
        metadata["pages"] = [
            {
                "index": index,
                "url": safePageUrl(currentPage),
                "closed": currentPage.is_closed(),
            }
            for index, currentPage in enumerate(context.pages)
        ]
    except Exception as diagnosticError:
        metadata["contextPagesError"] = repr(diagnosticError)

    await writeJsonSafely(
        diagnosticDir / "metadata.json",
        metadata,
    )

    if page.is_closed():
        return

    try:
        await asyncio.wait_for(
            page.screenshot(
                path=diagnosticDir / "screenshot.png",
                full_page=False,
                timeout=10_000,
            ),
            timeout=15,
        )
    except Exception as diagnosticError:
        await writeTextSafely(
            diagnosticDir / "screenshot-error.txt",
            repr(diagnosticError),
        )

    try:
        html = await asyncio.wait_for(
            page.content(),
            timeout=10,
        )
        await writeTextSafely(
            diagnosticDir / "page.html",
            html,
        )
    except Exception as diagnosticError:
        await writeTextSafely(
            diagnosticDir / "html-error.txt",
            repr(diagnosticError),
        )

    try:
        title = await asyncio.wait_for(
            page.title(),
            timeout=5,
        )
        await writeTextSafely(
            diagnosticDir / "title.txt",
            title,
        )
    except Exception as diagnosticError:
        await writeTextSafely(
            diagnosticDir / "title-error.txt",
            repr(diagnosticError),
        )


async def writeJsonSafely(path: Path, data: Any) -> None:
    try:
        await asyncio.to_thread(
            path.write_text,
            json.dumps(data, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )
    except Exception:
        pass


async def writeTextSafely(path: Path, text: str) -> None:
    try:
        await asyncio.to_thread(
            path.write_text,
            text,
            encoding="utf-8",
        )
    except Exception:
        pass
```

## Why start with `full_page=False`?

For failure diagnostics, a viewport screenshot is generally more robust:

```python
await page.screenshot(full_page=False)
```

A full-page screenshot may have to calculate and render a very large document. On an unstable page, that can be slower or fail separately.

You can attempt a full-page screenshot as a second diagnostic:

```python
try:
    await page.screenshot(
        path=diagnosticDir / "full-page.png",
        full_page=True,
        timeout=20_000,
    )
except Exception:
    pass
```

---

# 6. Why `page.is_closed() == False` does not guarantee screenshots work

`is_closed() == False` means the `Page` object has not been marked closed. It does **not** guarantee that every page operation can complete successfully.

For example:

1. The page exists, but its browser or context is in the process of shutting down.
2. The renderer has crashed.
3. A navigation has left the execution context unstable.
4. The screenshot operation times out while rendering.
5. The page remains open but is blocked on a dialog.
6. The page is no longer the page you intended; a popup or replacement page is active.
7. The screenshot output path cannot be created or written.
8. Your cleanup code closes the context concurrently.
9. The page is extremely tall and `full_page=True` fails or exhausts resources.

Always log the **screenshot exception itself**:

```python
except Exception as screenshotError:
    logger.exception(
        "Unable to capture screenshot: pageUrl=%s closed=%s",
        safePageUrl(page),
        page.is_closed(),
    )
```

A common bug in diagnostic handlers is shadowing the original error:

```python
except Exception as e:
    ...
    except Exception as e:
        ...
```

Use distinct names:

```python
except Exception as originalError:
    try:
        ...
    except Exception as diagnosticError:
        ...
```

Otherwise, logs become confusing and you can lose track of the actual failure.

---

# 7. Configure sensible timeout layers

Playwright has separate general and navigation timeouts:

```python
page.set_default_timeout(15_000)
page.set_default_navigation_timeout(45_000)
```

Or at context level:

```python
context.set_default_timeout(15_000)
context.set_default_navigation_timeout(45_000)
```

A useful policy is:

* Element actions: 10–15 seconds
* Assertions: 10–20 seconds
* Normal navigation: 30–45 seconds
* Slow external login/SSO: 60–90 seconds
* Diagnostics: short bounded timeout, such as 5–15 seconds

Avoid making all timeouts extremely large. A 5-minute timeout usually delays useful diagnostics rather than increasing reliability.

Use a larger timeout only for a specific known slow operation:

```python
await page.wait_for_url(
    "**/signin-callback**",
    timeout=90_000,
)
```

Not globally:

```python
page.set_default_timeout(300_000)
```

---

# 8. Treat navigation as a state machine

Login workflows commonly have multiple valid paths:

```text
login
  ├── dashboard
  ├── MFA page
  ├── password-change page
  ├── consent page
  ├── signin callback
  ├── account locked
  └── login error
```

Waiting only for `/dashboard` hides all other outcomes behind a timeout.

Instead, wait for several possible states and classify the result.

```python
import asyncio
from dataclasses import dataclass
from enum import StrEnum

from playwright.async_api import Page


class LoginResult(StrEnum):
    DASHBOARD = "dashboard"
    MFA = "mfa"
    PASSWORD_CHANGE = "passwordChange"
    LOGIN_ERROR = "loginError"
    TIMEOUT = "timeout"


@dataclass
class LoginOutcome:
    result: LoginResult
    url: str
    message: str = ""


async def waitForLoginOutcome(
    page: Page,
    timeoutSec: float = 45,
) -> LoginOutcome:
    dashboard = page.get_by_test_id("dashboard-root")
    mfaForm = page.get_by_role("heading", name="Verification")
    passwordChange = page.get_by_role(
        "heading",
        name="Change password",
    )
    loginError = page.get_by_role("alert")

    deadline = asyncio.get_running_loop().time() + timeoutSec

    while asyncio.get_running_loop().time() < deadline:
        if await dashboard.is_visible():
            return LoginOutcome(
                LoginResult.DASHBOARD,
                page.url,
            )

        if await mfaForm.is_visible():
            return LoginOutcome(
                LoginResult.MFA,
                page.url,
            )

        if await passwordChange.is_visible():
            return LoginOutcome(
                LoginResult.PASSWORD_CHANGE,
                page.url,
            )

        if await loginError.is_visible():
            return LoginOutcome(
                LoginResult.LOGIN_ERROR,
                page.url,
                await loginError.inner_text(),
            )

        await page.wait_for_timeout(200)

    return LoginOutcome(
        LoginResult.TIMEOUT,
        page.url,
        "No recognized login result appeared",
    )
```

However, repeated `is_visible()` polling is not my first choice for every workflow because each call tests only the current state. For a small number of mutually exclusive outcomes, racing explicit waits is cleaner.

```python
import asyncio
from contextlib import suppress

from playwright.async_api import Page


async def waitForFirstLoginResult(page: Page) -> str:
    async def waitForDashboard() -> str:
        await page.get_by_test_id("dashboard-root").wait_for(
            state="visible",
            timeout=45_000,
        )
        return "dashboard"

    async def waitForMfa() -> str:
        await page.get_by_test_id("mfa-form").wait_for(
            state="visible",
            timeout=45_000,
        )
        return "mfa"

    async def waitForError() -> str:
        await page.get_by_role("alert").wait_for(
            state="visible",
            timeout=45_000,
        )
        return "loginError"

    tasks = {
        asyncio.create_task(waitForDashboard()),
        asyncio.create_task(waitForMfa()),
        asyncio.create_task(waitForError()),
    }

    done, pending = await asyncio.wait(
        tasks,
        return_when=asyncio.FIRST_COMPLETED,
    )

    for task in pending:
        task.cancel()

    for task in pending:
        with suppress(asyncio.CancelledError):
            await task

    completedTask = next(iter(done))
    return await completedTask
```

This turns an unexplained timeout into a defined business result.

---

# 9. Do not use `networkidle` as a universal readiness signal

This is often tempting:

```python
await page.wait_for_load_state("networkidle")
```

But many modern applications continuously maintain:

* WebSockets
* Polling
* Analytics requests
* Background refreshes
* Service-worker traffic

The page may never become meaningfully idle, or it may briefly become idle before the UI is ready.

Prefer a business/UI state:

```python
await expect(page.get_by_test_id("orders-table")).to_be_visible()
```

or a specific API response:

```python
async with page.expect_response(
    lambda response:
        response.url.endswith("/api/orders")
        and response.status == 200
):
    await page.goto(ordersUrl)
```

The navigation documentation explicitly notes that there is no universal way to decide when a modern page is “loaded”; readiness depends on the application. ([Playwright][5])

---

# 10. Use resilient locators

Recommended locator priorities are generally:

1. `get_by_role()`
2. `get_by_label()`
3. `get_by_placeholder()`
4. `get_by_text()`
5. `get_by_test_id()`
6. CSS/XPath only when necessary

These built-in locators are the recommended approach and participate in Playwright’s retry and auto-waiting model. ([Playwright][7])

Good:

```python
page.get_by_role("button", name="Submit")
page.get_by_label("Email")
page.get_by_test_id("shipment-table")
```

Fragile:

```python
page.locator(
    "body > div:nth-child(3) > div > form > button:nth-child(2)"
)
```

## Handle strict-mode locator errors

This fails when more than one button matches:

```python
await page.get_by_role("button", name="Save").click()
```

That is useful—it exposes ambiguity instead of clicking an arbitrary element.

Narrow it:

```python
form = page.get_by_role("form", name="Shipment details")

await form.get_by_role(
    "button",
    name="Save",
    exact=True,
).click()
```

Avoid immediately fixing ambiguity with `.first`:

```python
await page.get_by_role("button", name="Save").first.click()
```

That can hide a UI change and click the wrong button.

---

# 11. Do not overuse `force=True`

This bypasses some actionability checks:

```python
await locator.click(force=True)
```

It can be appropriate when you intentionally want low-level behavior, but it often hides the real problem:

* Overlay blocking the element
* Cookie banner
* Loading spinner
* Wrong locator
* Disabled control
* Animation still active
* Sticky header intercepting the click

Playwright normally checks whether the target receives pointer events; forced clicks disable non-essential checks. ([Playwright][1])

Before forcing, inspect:

```python
print("visible:", await locator.is_visible())
print("enabled:", await locator.is_enabled())
print("count:", await locator.count())
print("box:", await locator.bounding_box())
```

Also examine the timeout’s actionability log, which often says something like:

```text
<div class="overlay"> intercepts pointer events
```

---

# 12. Capture browser console, page errors, and network failures

Install listeners immediately after creating the page.

```python
from playwright.async_api import Page


def attachPageDiagnostics(page: Page, logger) -> None:
    page.on(
        "console",
        lambda message: logger.info(
            "browser-console type=%s text=%s",
            message.type,
            message.text,
        ),
    )

    page.on(
        "pageerror",
        lambda error: logger.error(
            "browser-pageerror error=%s",
            error,
        ),
    )

    page.on(
        "requestfailed",
        lambda request: logger.error(
            "request-failed method=%s url=%s failure=%s",
            request.method,
            request.url,
            request.failure,
        ),
    )

    page.on(
        "response",
        lambda response: (
            logger.warning(
                "http-error status=%s url=%s",
                response.status,
                response.url,
            )
            if response.status >= 400
            else None
        ),
    )

    page.on(
        "crash",
        lambda: logger.critical(
            "page-crashed url=%s",
            safePageUrl(page),
        ),
    )

    page.on(
        "close",
        lambda: logger.warning(
            "page-closed url=%s",
            safePageUrl(page),
        ),
    )
```

Important distinction:

* DNS errors, connection resets and similar transport failures trigger `requestfailed`.
* HTTP statuses such as `404` and `503` are still HTTP responses and do not count as failed requests at Playwright’s transport layer. Check response statuses separately. ([Playwright][8])

Be careful about logging every response in production; pages can make hundreds of requests. Logging only failures and selected API endpoints is more manageable.

---

# 13. Record a Playwright trace

A screenshot shows one moment. A trace shows:

* Actions and timings
* Before/after DOM snapshots
* Screenshots over time
* Network activity
* Console output
* Actionability logs
* Source locations

Trace Viewer is usually the highest-value diagnostic tool for intermittent failures. ([Playwright][9])

```python
from pathlib import Path
from playwright.async_api import async_playwright


async def run() -> None:
    tracePath = Path("artifacts/trace.zip")
    tracePath.parent.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context()

        await context.tracing.start(
            screenshots=True,
            snapshots=True,
            sources=True,
        )

        page = await context.new_page()

        try:
            await performWorkflow(page)
        finally:
            await context.tracing.stop(path=tracePath)
            await context.close()
            await browser.close()
```

Open it with:

```bash
playwright show-trace artifacts/trace.zip
```

The lower-level `context.tracing` API records browser operations and network activity, though test-runner-integrated tracing can include richer test assertion information. ([Playwright][10])

---

# 14. Stop traces before closing the context

Incorrect:

```python
await context.close()
await context.tracing.stop(path="trace.zip")
```

Correct:

```python
try:
    await performWorkflow(page)
finally:
    try:
        await context.tracing.stop(path="trace.zip")
    finally:
        await context.close()
        await browser.close()
```

Once the context is closed, it may be too late to save context-based diagnostics.

---

# 15. Troubleshooting common failures

## Case 1: `wait_for_url()` times out but the browser looks correct

Log the exact URL:

```python
print(repr(page.url))
```

Check for:

* Trailing slash
* Query parameters
* URL fragment
* Different hostname
* `http` versus `https`
* SSO callback URL
* Encoded characters
* Popup instead of same-page navigation
* Iframe navigation instead of main-frame navigation
* Redirect back to login
* SPA content update without expected URL

Use a regex or predicate:

```python
import re

await page.wait_for_url(
    re.compile(r"https://[^/]+/dashboard(?:[/?#]|$)")
)
```

Also enumerate pages:

```python
for index, currentPage in enumerate(page.context.pages):
    print(
        index,
        currentPage.url,
        currentPage.is_closed(),
    )
```

## Case 2: Click succeeded but URL never changes

Possible explanations:

* It opened a popup.
* It triggered a download.
* It made an API request and updated the current DOM.
* JavaScript crashed.
* Form validation rejected the input.
* An overlay intercepted the click.
* The click selected the wrong matching element.
* The action opened an iframe-based flow.

Wait for the actual expected signal:

```python
async with page.expect_response("**/api/login") as responseInfo:
    await submitButton.click()

response = await responseInfo.value
```

Then inspect:

```python
print(response.status)
print(await response.text())
```

## Case 3: Element is visibly present but Playwright cannot click it

Check:

```python
locator = page.get_by_role("button", name="Continue")

print("count:", await locator.count())
print("visible:", await locator.is_visible())
print("enabled:", await locator.is_enabled())
print("box:", await locator.bounding_box())
```

Common causes:

* Duplicate matches
* Transparent overlay
* Loading mask
* Element outside an iframe
* Element detached and replaced
* Animation
* Disabled button
* Wrong page or popup
* Cookie banner
* Element is present but zero-sized
* Another element receives pointer events

Playwright considers an element visible based on its box and CSS visibility; notably, `opacity: 0` can still count as visible under its actionability definition. ([Playwright][11])

## Case 4: `Target page, context or browser has been closed`

Usually this is lifecycle ordering or concurrency.

Look for:

```python
async with async_playwright() as playwright:
    page = await ...
    
# Playwright and browser are closed here.
await page.screenshot(...)
```

Or:

```python
try:
    ...
finally:
    await context.close()

# Another task still uses page.
```

Also check whether multiple coroutines share and close the same page.

Use clear ownership:

```python
async with async_playwright() as playwright:
    browser = await playwright.chromium.launch()
    context = await browser.new_context()

    try:
        page = await context.new_page()
        await performWorkflow(page)
    finally:
        await context.close()
        await browser.close()
```

## Case 5: `Execution context was destroyed`

Usually the page navigated while code was evaluating JavaScript or accessing an element.

Risky:

```python
element = await page.query_selector("#result")
await page.click("#next")
text = await element.text_content()
```

The old element belongs to the previous document.

Prefer locators, which resolve the current element when used:

```python
result = page.locator("#result")

await page.get_by_role("button", name="Next").click()
await result.wait_for()
text = await result.text_content()
```

Locators are specifically designed around re-resolution, auto-waiting, and retryability. ([Playwright][12])

## Case 6: Works headed, fails headless

Check:

* Responsive layout changes
* Different viewport
* Browser extensions present only in headed/manual browser
* Missing fonts
* GPU/rendering differences
* Hover-dependent menus
* Timing differences
* Bot protection
* Download handling
* Permission prompts
* Certificate behavior

Set an explicit viewport:

```python
context = await browser.new_context(
    viewport={"width": 1440, "height": 1000},
)
```

Run with tracing and compare headed/headless behavior.

## Case 7: Works locally, fails in CI or Docker

Verify:

* Browser binaries installed
* System dependencies installed
* Shared memory availability
* Fonts
* Locale and timezone
* Network and DNS
* Proxy configuration
* CA certificates
* File permissions
* Writable artifact directory
* CPU and memory contention

Install the matching browser and operating-system dependencies using the official installation commands appropriate to the environment.

Also avoid assuming a local hostname resolves identically inside Docker.

## Case 8: The locator sometimes matches zero items

Do not use `locator.all()` immediately on a dynamically loaded list. It returns whatever currently exists and does not wait for the list to populate, which can produce flaky results. ([Playwright][12])

Instead:

```python
items = page.get_by_role("listitem")

await expect(items).to_have_count(10)

for index in range(await items.count()):
    print(await items.nth(index).inner_text())
```

## Case 9: A dialog blocks the workflow

Install a listener before the dialog appears:

```python
async def handleDialog(dialog) -> None:
    print(f"Dialog: type={dialog.type} message={dialog.message}")
    await dialog.dismiss()

page.on("dialog", handleDialog)
```

Or accept it:

```python
page.on(
    "dialog",
    lambda dialog: asyncio.create_task(dialog.accept()),
)
```

## Case 10: Wrong iframe

A locator on `page` cannot directly find content inside a child frame.

```python
paymentFrame = page.frame_locator(
    'iframe[title="Payment"]'
)

await paymentFrame.get_by_label(
    "Card number"
).fill("...")
```

Inspect frames:

```python
for frame in page.frames:
    print(frame.name, frame.url)
```

## Case 11: Redirect loop

Record navigation events:

```python
page.on(
    "framenavigated",
    lambda frame: print(
        "navigated:",
        frame.url,
        "mainFrame:",
        frame == page.main_frame,
    ),
)
```

Then inspect cookies and authentication state:

```python
cookies = await page.context.cookies()
for cookie in cookies:
    print(
        cookie["name"],
        cookie["domain"],
        cookie["path"],
        cookie["secure"],
        cookie["sameSite"],
    )
```

Typical causes include invalid session cookies, wrong cookie domain/path, missing callback state, failed CSRF validation, or an incorrect environment URL.

---

# 16. Retries: retry workflows, not random individual actions

Blind retry:

```python
for attempt in range(3):
    try:
        await page.get_by_role("button", name="Submit").click()
        break
    except Exception:
        pass
```

This can submit a form several times.

A retry should be:

* Limited
* Applied only to known transient failures
* Idempotent
* Logged
* Preceded by state validation
* Followed by recovery or page reset

```python
from collections.abc import Awaitable, Callable
from typing import TypeVar

from playwright.async_api import TimeoutError as PlaywrightTimeoutError

T = TypeVar("T")


async def retryTransient(
    operation: Callable[[], Awaitable[T]],
    *,
    attempts: int = 3,
    delaySec: float = 1,
) -> T:
    lastError: BaseException | None = None

    for attempt in range(1, attempts + 1):
        try:
            return await operation()

        except PlaywrightTimeoutError as error:
            lastError = error

            if attempt == attempts:
                raise

            await asyncio.sleep(delaySec * attempt)

    assert lastError is not None
    raise lastError
```

Suitable:

```python
async def loadReadOnlyStatus():
    await page.reload(wait_until="domcontentloaded")
    await page.get_by_test_id("status").wait_for()
    return await page.get_by_test_id("status").inner_text()
```

Potentially unsafe:

```python
async def submitPayment():
    await page.get_by_role("button", name="Pay").click()
```

For a mutating operation, check whether it already succeeded before retrying.

---

# 17. Logging action boundaries

Log before and after meaningful actions:

```python
logger.info(
    "action=start name=submit-login url=%s",
    page.url,
)

await page.get_by_role("button", name="Sign in").click()

logger.info(
    "action=finished name=submit-login url=%s",
    page.url,
)
```

For waits:

```python
expectedUrl = "**/dashboard**"

logger.info(
    "wait=start condition=url expected=%s current=%s",
    expectedUrl,
    page.url,
)

await page.wait_for_url(expectedUrl, timeout=30_000)

logger.info(
    "wait=finished condition=url current=%s",
    page.url,
)
```

This quickly answers:

* Which operation was running?
* Did the click return?
* What was the URL before and after?
* Was it stuck on the action or the subsequent wait?
* Which timeout applied?

Never log passwords, authentication tokens, full sensitive query strings, or session cookies.

---

# 18. A complete robust workflow pattern

```python
#!/usr/bin/env python

from __future__ import annotations

import asyncio
import logging
import re
from pathlib import Path

from playwright.async_api import (
    Browser,
    BrowserContext,
    Error as PlaywrightError,
    Page,
    TimeoutError as PlaywrightTimeoutError,
    async_playwright,
    expect,
)


logger = logging.getLogger(__name__)


async def login(
    page: Page,
    username: str,
    password: str,
) -> None:
    logger.info("Opening login page")

    response = await page.goto(
        "https://example.com/login",
        wait_until="domcontentloaded",
        timeout=45_000,
    )

    if response is not None and response.status >= 400:
        raise RuntimeError(
            f"Login page returned HTTP {response.status}"
        )

    await expect(
        page.get_by_role("heading", name="Sign in")
    ).to_be_visible(timeout=15_000)

    await page.get_by_label("Username").fill(username)
    await page.get_by_label("Password").fill(password)

    logger.info("Submitting login form")

    async with page.expect_response(
        lambda apiResponse:
            "/api/login" in apiResponse.url
            and apiResponse.request.method == "POST",
        timeout=30_000,
    ) as responseInfo:
        await page.get_by_role(
            "button",
            name="Sign in",
        ).click()

    loginResponse = await responseInfo.value

    if not loginResponse.ok:
        responseBody = await loginResponse.text()
        raise RuntimeError(
            "Login API failed: "
            f"status={loginResponse.status}, "
            f"body={responseBody[:500]}"
        )

    await page.wait_for_url(
        re.compile(r"/dashboard(?:[/?#]|$)"),
        timeout=45_000,
    )

    await expect(
        page.get_by_test_id("dashboard-root")
    ).to_be_visible(timeout=30_000)

    logger.info("Login completed: url=%s", page.url)


async def runWorkflow(
    browser: Browser,
    username: str,
    password: str,
) -> None:
    context: BrowserContext = await browser.new_context(
        viewport={"width": 1440, "height": 1000},
    )

    context.set_default_timeout(15_000)
    context.set_default_navigation_timeout(45_000)

    tracePath = Path("artifacts/trace.zip")
    tracePath.parent.mkdir(parents=True, exist_ok=True)

    await context.tracing.start(
        screenshots=True,
        snapshots=True,
        sources=True,
    )

    page = await context.new_page()
    attachPageDiagnostics(page, logger)

    try:
        await login(page, username, password)

    except PlaywrightTimeoutError as error:
        logger.exception(
            "Playwright timeout: url=%s",
            safePageUrl(page),
        )
        await collectDiagnostics(
            page,
            error,
            "timeout",
        )
        raise

    except PlaywrightError as error:
        logger.exception(
            "Playwright error: url=%s",
            safePageUrl(page),
        )
        await collectDiagnostics(
            page,
            error,
            "playwright",
        )
        raise

    except Exception as error:
        logger.exception(
            "Unexpected workflow error: url=%s",
            safePageUrl(page),
        )
        await collectDiagnostics(
            page,
            error,
            "unexpected",
        )
        raise

    finally:
        try:
            await context.tracing.stop(path=tracePath)
        except Exception:
            logger.exception("Unable to save Playwright trace")

        await context.close()


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s %(levelname)s "
            "%(name)s: %(message)s"
        ),
    )

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=True,
        )

        try:
            await runWorkflow(
                browser,
                username="james",
                password="secret",
            )
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
```

---

# 19. Interactive debugging commands

Use Playwright Inspector:

```bash
PWDEBUG=1 pytest -s
```

PowerShell:

```powershell
$env:PWDEBUG = "1"
pytest -s
```

This launches headed mode, opens the Inspector, allows stepping through actions, and displays actionability information. ([Playwright][13])

For a normal Python script:

```bash
PWDEBUG=1 python yourScript.py
```

You can also pause at a suspicious location:

```python
await page.pause()
```

This is particularly useful for checking:

* Which locator matches
* Whether an overlay is present
* Current frames
* Current URL
* Whether a popup was created
* Why an element is not actionable

---

# 20. Practical checklist when a timeout occurs

Record these facts for every failure:

1. The exact operation that timed out.
2. The exact expected URL, locator, request, or response.
3. `repr(page.url)`.
4. Whether `page.is_closed()` is true.
5. Every page in `page.context.pages`.
6. Every frame URL in `page.frames`.
7. Recent browser console errors.
8. Failed network requests.
9. HTTP responses with status 400 or above.
10. A viewport screenshot.
11. Saved HTML.
12. A Playwright trace.
13. Whether a popup, download, dialog, or iframe was involved.
14. Whether cleanup began before diagnostics finished.
15. Whether concurrent tasks were sharing the same page.

The most important design improvement is to stop treating every unexpected result as a timeout. Explicitly model valid alternative outcomes—dashboard, MFA, login error, consent page, popup, download, API failure—and report the actual state that appeared.

[1]: https://playwright.dev/python/docs/actionability?utm_source=chatgpt.com "Auto-waiting | Playwright Python"
[2]: https://playwright.dev/python/docs/library?utm_source=chatgpt.com "Getting started - Library | Playwright Python"
[3]: https://playwright.dev/python/docs/api/class-frame?utm_source=chatgpt.com "Frame | Playwright Python"
[4]: https://playwright.dev/python/docs/test-assertions?utm_source=chatgpt.com "Assertions | Playwright Python"
[5]: https://playwright.dev/python/docs/navigations?utm_source=chatgpt.com "Navigations | Playwright Python"
[6]: https://playwright.dev/python/docs/api/class-error?utm_source=chatgpt.com "Error | Playwright Python"
[7]: https://playwright.dev/python/docs/locators?utm_source=chatgpt.com "Locators | Playwright Python"
[8]: https://playwright.dev/python/docs/api/class-request?utm_source=chatgpt.com "Request | Playwright Python"
[9]: https://playwright.dev/python/docs/trace-viewer?utm_source=chatgpt.com "Trace viewer | Playwright Python"
[10]: https://playwright.dev/python/docs/api/class-tracing?utm_source=chatgpt.com "Tracing | Playwright Python"
[11]: https://playwright.dev/docs/actionability?utm_source=chatgpt.com "Auto-waiting | Playwright"
[12]: https://playwright.dev/python/docs/api/class-locator?utm_source=chatgpt.com "Locator | Playwright Python"
[13]: https://playwright.dev/python/docs/debug?utm_source=chatgpt.com "Debugging Tests | Playwright Python"
