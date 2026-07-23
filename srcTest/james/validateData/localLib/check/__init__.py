They are similar because both **repeatedly check the page URL until it matches or the timeout expires**. The main difference is their purpose and failure reporting.

```python
await page.wait_for_url(urlRegex, timeout=30_000)
```

means:

> Pause the workflow until navigation reaches this URL.

```python
await expect(page).to_have_url(urlRegex, timeout=30_000)
```

means:

> Assert that the page eventually has this URL; otherwise report an assertion failure.

Playwright officially recommends `wait_for_url()` when explicitly waiting for navigation, while `expect(page).to_have_url()` is part of its retrying test assertions. ([Playwright][1])

## Key differences

| Difference            | `page.wait_for_url()`              | `expect(page).to_have_url()`       |
| --------------------- | ---------------------------------- | ---------------------------------- |
| Main purpose          | Synchronization/navigation waiting | Verification/testing               |
| Success result        | Returns `None`                     | Returns `None`                     |
| Failure type          | `PlaywrightTimeoutError`           | `AssertionError`                   |
| Default timeout       | Navigation/default timeout         | Expect timeout, normally 5 seconds |
| Error message         | Navigation timeout details         | Expected URL versus received URL   |
| Supports regex        | Yes                                | Yes                                |
| Supports glob strings | Yes                                | No glob semantics                  |
| Supports `wait_until` | Yes                                | No                                 |
| Best suited to        | Browser automation workflows       | Tests and final validation         |

## 1. The exception type is different

### `wait_for_url()`

```python
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

try:
    await page.wait_for_url(
        re.compile(r"/dashboard(?:[/?#]|$)"),
        timeout=30_000,
    )
except PlaywrightTimeoutError:
    print(f"Navigation timed out; current URL={page.url}")
```

### `expect().to_have_url()`

```python
from playwright.async_api import expect

try:
    await expect(page).to_have_url(
        re.compile(r"/dashboard(?:[/?#]|$)"),
        timeout=30_000,
    )
except AssertionError:
    print(f"URL assertion failed; current URL={page.url}")
```

This matters in your exception-handling design. If all your Playwright timeout handling catches only `PlaywrightTimeoutError`, it will **not** catch an `expect()` assertion failure.

For example:

```python
except PlaywrightTimeoutError:
    await dumpPageErrors(page, error)
```

will not handle:

```python
await expect(page).to_have_url(...)
```

You would need:

```python
except (PlaywrightTimeoutError, AssertionError) as error:
    await dumpPageErrors(page, error)
    raise
```

Or keep the categories separate:

```python
except PlaywrightTimeoutError as error:
    await dumpPageErrors(page, error)
    raise

except AssertionError as error:
    await dumpPageErrors(page, error)
    raise
```

## 2. Their timeout settings are different

`wait_for_url()` uses Playwright’s navigation timeout configuration:

```python
page.set_default_navigation_timeout(45_000)
```

```python
await page.wait_for_url(urlRegex)
```

`expect(page).to_have_url()` uses the assertion timeout, which defaults to approximately five seconds unless overridden. ([Playwright][2])

```python
await expect(page).to_have_url(
    urlRegex,
    timeout=45_000,
)
```

Therefore, this may unexpectedly fail much sooner:

```python
page.set_default_navigation_timeout(60_000)

# This does not necessarily inherit the 60-second navigation timeout.
await expect(page).to_have_url(urlRegex)
```

You can configure the default assertion timeout:

```python
from playwright.async_api import expect

expect.set_options(timeout=15_000)
```

For external authentication and SSO, I would usually specify the timeout explicitly:

```python
await expect(page).to_have_url(
    urlRegex,
    timeout=60_000,
)
```

## 3. `wait_for_url()` supports navigation load states

`wait_for_url()` has a `wait_until` argument:

```python
await page.wait_for_url(
    urlRegex,
    wait_until="commit",
    timeout=30_000,
)
```

Possible values include:

```python
"commit"
"domcontentloaded"
"load"
"networkidle"
```

This means you can require both:

1. The URL matches.
2. Navigation reaches a specified lifecycle state.

For example:

```python
await page.wait_for_url(
    re.compile(r"/dashboard(?:[/?#]|$)"),
    wait_until="domcontentloaded",
    timeout=30_000,
)
```

By contrast:

```python
await expect(page).to_have_url(urlRegex)
```

only verifies the current URL. It does not require `DOMContentLoaded` or `load`.

That said, the URL matching does **not** prove that your application is usable. It is usually better to wait separately for a meaningful page element:

```python
await page.wait_for_url(
    re.compile(r"/dashboard(?:[/?#]|$)"),
    wait_until="domcontentloaded",
    timeout=30_000,
)

await expect(
    page.get_by_test_id("dashboard-root")
).to_be_visible(timeout=30_000)
```

## 4. Glob patterns behave differently

`wait_for_url()` accepts Playwright URL glob patterns:

```python
await page.wait_for_url("**/dashboard/**")
```

`expect(page).to_have_url()` accepts a URL string or compiled regex, but a string should be treated as an expected URL rather than a Playwright glob.

Therefore, do not assume this has the same meaning:

```python
await expect(page).to_have_url("**/dashboard/**")
```

Since you already use compiled regex, this difference does not affect you:

```python
urlRegex = re.compile(r"/dashboard(?:[/?#]|$)")
```

Both methods accept it.

## 5. Assertion reporting is normally better

Suppose the current URL is:

```text
https://supplier.example.com/login?error=invalid_session
```

and you expected:

```python
re.compile(r"/dashboard(?:[/?#]|$)")
```

An assertion normally gives test-oriented information describing the expected and received state. Playwright assertions are specifically designed to retry and produce useful test failure output. ([Playwright][3])

This makes `expect()` especially useful in pytest:

```python
async def testLogin(page: Page) -> None:
    await login(page)

    await expect(page).to_have_url(
        re.compile(r"/dashboard(?:[/?#]|$)")
    )
```

A failed URL assertion clearly means the test’s expected outcome was not reached.

## 6. Which should you use?

For your type of automation, I recommend:

### Use `wait_for_url()` for workflow synchronization

Use it when reaching the URL is an intermediate step before continuing:

```python
await page.get_by_role("button", name="Sign in").click()

await page.wait_for_url(
    re.compile(r"/signin-callback(?:[/?#]|$)"),
    timeout=60_000,
)

await page.wait_for_url(
    re.compile(r"/dashboard(?:[/?#]|$)"),
    timeout=60_000,
)

await processDashboard(page)
```

This fits normal automation semantics:

> Wait until the browser reaches this stage, then continue.

It also works naturally with your existing `PlaywrightTimeoutError` handler.

### Use `expect().to_have_url()` for verification

Use it when the URL itself is an expected test result:

```python
await login(page)

await expect(page).to_have_url(
    re.compile(r"/dashboard(?:[/?#]|$)"),
    timeout=30_000,
)
```

This fits test semantics:

> The login operation must finish at the dashboard URL.

## Recommended practical rule

For production automation or scraping:

```python
await page.wait_for_url(...)
```

For pytest assertions:

```python
await expect(page).to_have_url(...)
```

For a workflow test, using both is normally unnecessary because they are checking almost the same condition. Instead, wait for the URL and assert a meaningful page state:

```python
await page.wait_for_url(
    re.compile(r"/dashboard(?:[/?#]|$)"),
    timeout=45_000,
)

await expect(
    page.get_by_test_id("dashboard-root")
).to_be_visible(timeout=20_000)
```

This confirms two different facts:

1. The browser reached the intended route.
2. The destination page actually rendered successfully.

## My recommendation for your existing code

Since you are handling unexpected login flows, URL timeouts, screenshots, and runtime errors—not merely writing assertions—I would keep using `wait_for_url()`:

```python
try:
    await page.wait_for_url(
        regexExpectedUrl,
        wait_until="domcontentloaded",
        timeout=60_000,
    )

except PlaywrightTimeoutError as error:
    U.logPrefixE(
        prefix,
        (
            f"Failed waiting for expected URL: "
            f"pattern={regexExpectedUrl.pattern!r}, "
            f"currentUrl={page.url!r}"
        ),
    )
    await dumpPageErrors(page, error)
    raise
```

Then use `expect()` to confirm destination-page elements:

```python
await expect(
    page.get_by_test_id("main-content")
).to_be_visible(timeout=30_000)
```

One final caution: `wait_for_url(..., wait_until="domcontentloaded")` can still time out after the URL visibly changed if the corresponding document never reaches `DOMContentLoaded`. When troubleshooting, try:

```python
await page.wait_for_url(
    regexExpectedUrl,
    wait_until="commit",
    timeout=60_000,
)
```

Then separately wait for the application’s meaningful element. This gives you more precise control over whether the problem is **navigation**, **document loading**, or **application rendering**.

[1]: https://playwright.dev/python/docs/navigations?utm_source=chatgpt.com "Navigations | Playwright Python"
[2]: https://playwright.dev/python/docs/api/class-pageassertions?utm_source=chatgpt.com "PageAssertions | Playwright Python"
[3]: https://playwright.dev/python/docs/test-assertions?utm_source=chatgpt.com "Assertions | Playwright Python"
