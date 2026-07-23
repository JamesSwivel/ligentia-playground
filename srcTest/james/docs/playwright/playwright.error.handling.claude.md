# Playwright (Python) — Exception Handling & Troubleshooting Guide

## 1. Understand Playwright's exception types first

Almost everything you'll catch falls into two buckets:

```python
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError

try:
    page.click("button#submit")
except PlaywrightTimeoutError:
    # Element/condition never became true within the timeout window
    ...
except PlaywrightError as e:
    # Everything else: context/page closed, navigation interrupted,
    # selector syntax error, protocol error, target crashed, etc.
    ...
```

- `PlaywrightTimeoutError` — subclass of `Error`. Raised by any `wait_for_*`, `expect_*`, or auto-waiting action (`click`, `fill`, `check`, …) that didn't meet its condition in time.
- `PlaywrightError` — the generic base. Message text is your best clue (e.g. `"Target closed"`, `"Execution context was destroyed"`, `"net::ERR_..."`).

Always catch the specific `TimeoutError` first if you want different handling for "slow/never happened" vs "something broke."

Async API: same classes live in `playwright.async_api`.

---

## 2. Waiting for navigation/URL — the #1 source of pain

### The core problem
`page.goto()` resolves on one condition (default: `load`), but the URL you *actually* care about might change again afterward (client-side redirect, SPA routing, OAuth bounce). If you check `page.url` immediately after `goto()`, you're racing the app.

### Fix patterns, in order of preference

**A. Let Playwright wait, don't poll manually**
```python
with page.expect_navigation(url="**/dashboard**", timeout=15000):
    page.click("text=Log in")
```
`expect_navigation` must wrap the *action that triggers* the navigation — this avoids the classic race where navigation starts and finishes before you start waiting.

**B. For SPA/client-side routing (no real navigation event)**
`expect_navigation` won't fire for history.pushState-based routing. Use:
```python
page.wait_for_url("**/dashboard**", timeout=15000)
```
Call this *after* the click, since `wait_for_url` polls `page.url` and doesn't depend on a navigation lifecycle event.

**C. Multiple possible outcomes (e.g. login can land on /dashboard OR /mfa)**
```python
page.click("text=Log in")
page.wait_for_url(lambda url: "/dashboard" in url or "/mfa" in url, timeout=15000)
```
A predicate function is more robust than one glob pattern when the app can branch.

**D. Never assume `goto()` timeout = load timeout you want**
```python
page.goto(url, wait_until="domcontentloaded", timeout=30000)
```
- `load` (default) waits for all resources — slow on image-heavy pages, can time out for no good reason.
- `domcontentloaded` — usually enough, much faster/more reliable.
- `commit` — only waits for the response to start; use when you'll wait_for_selector afterward anyway.
- `networkidle` — tempting but fragile: SPAs with polling/websockets/analytics beacons never go idle. Avoid unless you know the app is quiet.

### Common mistake checklist
- Checking `page.url` right after `.click()` without any wait → race condition.
- Using `expect_navigation()` as a bare statement *after* the click instead of as a context manager around it → misses navigations that already started.
- Using `wait_until="networkidle"` on a page with background polling → guaranteed timeout.
- Forgetting that popups/new tabs are separate `Page` objects — the URL change happens on a page you're not looking at (see §5).

---

## 3. General exception-handling structure

### Wrap flaky external interactions, not everything
Don't blanket try/except your whole script — you'll swallow real bugs. Wrap the specific risky call, and be intentional about what happens next.

```python
def safe_click(page, selector, timeout=5000):
    try:
        page.click(selector, timeout=timeout)
        return True
    except PlaywrightTimeoutError:
        logger.warning(f"Click timed out: {selector}")
        return False
```

### Retry with backoff for known-flaky steps
```python
def retry(fn, attempts=3, delay=1.0):
    last_exc = None
    for i in range(attempts):
        try:
            return fn()
        except PlaywrightError as e:
            last_exc = e
            logger.warning(f"Attempt {i+1}/{attempts} failed: {e}")
            time.sleep(delay * (i + 1))  # linear/exponential backoff
    raise last_exc
```
Use this for actions that fail due to transient timing (element not yet interactable), not for actions that fail because your selector is wrong — retrying a bad selector just wastes time.

### Always clean up
```python
browser = None
try:
    browser = p.chromium.launch()
    page = browser.new_page()
    ...
except Exception:
    page.screenshot(path="failure.png")  # capture evidence before it's gone
    raise
finally:
    if browser:
        browser.close()
```
Grab a screenshot/HTML dump **before** closing anything — once the context is torn down, the evidence is gone.

### Know which exceptions are "expected" vs bugs
| Situation                          | Typical exception                                         | Usually means                                                                                      |
| ---------------------------------- | --------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| Element never appears              | `TimeoutError` on `click`/`fill`                          | Selector wrong, page didn't load, or content behind auth/loading spinner                           |
| Element removed after you found it | `Error: element is not attached to the DOM`               | DOM re-rendered between locate and action (React/Vue re-render) — use locators, not stored handles |
| Page/tab closed mid-action         | `Error: Target page, context or browser has been closed`  | Popup closed itself, or your own code closed it early                                              |
| Navigation interrupted an action   | `Error: Execution context was destroyed`                  | You ran `page.evaluate` or similar right as a navigation started                                   |
| Wrong iframe/frame scope           | Selector times out even though "it's clearly on the page" | Element is inside an `<iframe>` — see §5                                                           |

---

## 4. Prefer web-first assertions and locators over manual polling

Old/manual style (fragile):
```python
element = page.query_selector("#status")
if element and element.inner_text() == "Done":
    ...
```
Modern style (auto-retries internally until timeout, far fewer flaky failures):
```python
from playwright.sync_api import expect

expect(page.locator("#status")).to_have_text("Done", timeout=10000)
```
`expect()` assertions poll the condition — they don't just check once. This eliminates most "it was there a millisecond ago" race conditions. Use locators (`page.locator(...)`) instead of `query_selector`/`element_handle` almost everywhere; locators re-resolve the DOM element every time they're used, so a stale-element error is much rarer.

---

## 5. Frequent real-world gotchas

**Iframes**: a selector on `page` won't see inside an `<iframe>`.
```python
frame = page.frame_locator("iframe#payment")
frame.locator("input#card-number").fill("4242...")
```

**Popups / new tabs**:
```python
with page.expect_popup() as popup_info:
    page.click("text=Open in new tab")
popup = popup_info.value
popup.wait_for_load_state()
```

**Downloads**:
```python
with page.expect_download() as download_info:
    page.click("text=Download report")
download = download_info.value
download.save_as("/path/to/file.csv")
```

**Dialogs (alert/confirm/prompt)** — must be handled *before* they'd appear, or Playwright hangs waiting for you:
```python
page.on("dialog", lambda dialog: dialog.accept())
```

**Multiple elements match your selector**:
```
Error: strict mode violation: locator resolved to 3 elements
```
Fix the selector to be unique, or explicitly pick: `.first`, `.nth(2)`, `.last`.

**Actionability failures** (`element is not visible`, `element is outside viewport`, `element is covered by another element`): Playwright already auto-waits for actionability, but overlays/cookie banners/sticky headers can permanently block a click. Dismiss the overlay first, or use `page.mouse.click(x, y)` / `force=True` as a last resort (bypasses safety checks — use sparingly).

---

## 6. Debugging toolkit (use these before you start guessing)

1. **Trace Viewer** — the single best tool for "why did this fail":
```python
context.tracing.start(screenshots=True, snapshots=True, sources=True)
# ... your test ...
context.tracing.stop(path="trace.zip")
```
```bash
playwright show-trace trace.zip
```
Gives you a timeline with DOM snapshots, network requests, and console logs at every step.

2. **Run headed + slow_mo** to see it with your own eyes:
```python
browser = p.chromium.launch(headless=False, slow_mo=500)
```

3. **PWDEBUG=1** drops you into the Playwright Inspector, step through actions manually:
```bash
PWDEBUG=1 python your_script.py
```

4. **Console & network logging** — catch page-side JS errors that silently break the app:
```python
page.on("console", lambda msg: print(f"[console] {msg.type}: {msg.text}"))
page.on("pageerror", lambda exc: print(f"[pageerror] {exc}"))
page.on("requestfailed", lambda req: print(f"[requestfailed] {req.url} {req.failure}"))
```

5. **Screenshot + HTML dump on failure** (cheap insurance in CI):
```python
page.screenshot(path="on_failure.png", full_page=True)
open("on_failure.html", "w").write(page.content())
```

6. **Video recording** for CI runs where you can't attach a debugger:
```python
context = browser.new_context(record_video_dir="videos/")
```

---

## 7. Quick reference: choosing the right wait

| You want to wait for...                          | Use                                                                                                                                         |
| ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------- |
| A real page navigation (form submit, link click) | `with page.expect_navigation(url=...)` around the action                                                                                    |
| A URL change from client-side routing (SPA)      | `page.wait_for_url(...)` after the action                                                                                                   |
| An element to appear/be actionable               | Just call `.click()`/`.fill()` — auto-waits — or `locator.wait_for()`                                                                       |
| Some text/state to become true                   | `expect(locator).to_have_text(...)`                                                                                                         |
| A network request/response                       | `with page.expect_response("**/api/data") as resp_info`                                                                                     |
| A new tab                                        | `with page.expect_popup() as popup_info`                                                                                                    |
| A download                                       | `with page.expect_download() as download_info`                                                                                              |
| Page fully "settled" after goto                  | `wait_until="domcontentloaded"` + a specific `wait_for_selector` afterward — avoid `networkidle` unless you've confirmed the app goes quiet |

---

## 8. Minimal robust pattern to copy-paste

```python
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    context.tracing.start(screenshots=True, snapshots=True)
    page = context.new_page()
    page.on("pageerror", lambda e: print("PAGE ERROR:", e))

    try:
        page.goto("https://example.com/login", wait_until="domcontentloaded", timeout=30000)
        page.fill("#username", "user")
        page.fill("#password", "pass")

        with page.expect_navigation(url="**/dashboard**", timeout=15000):
            page.click("button[type=submit]")

        page.locator("#welcome-banner").wait_for(state="visible", timeout=10000)
        print("Logged in successfully:", page.url)

    except PWTimeout as e:
        page.screenshot(path="timeout_failure.png", full_page=True)
        print(f"Timed out: {e}")
    except Exception as e:
        page.screenshot(path="error_failure.png", full_page=True)
        print(f"Unexpected error: {e}")
        raise
    finally:
        context.tracing.stop(path="trace.zip")
        context.close()
        browser.close()

with sync_playwright() as p:
    run(p)
```

---

## TL;DR checklist
- [ ] Use `page.locator()` + `expect()` instead of one-shot `query_selector` checks.
- [ ] Wrap navigation-triggering actions in `expect_navigation()`; use `wait_for_url()` for SPA routing.
- [ ] Avoid `networkidle` unless you've verified the app actually idles.
- [ ] Catch `TimeoutError` separately from generic `Error`.
- [ ] Take a screenshot/trace *before* closing context on failure.
- [ ] Use Trace Viewer as your first debugging step, not print statements.
- [ ] Remember iframes and popups live outside `page`'s default selector scope.