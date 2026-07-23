Good question — they overlap a lot, but they're built for different jobs.

**`page.wait_for_url(pattern)`**
- An *action/wait*, not an assertion. It just pauses execution until the condition is true, then returns `None`.
- Raises `PlaywrightTimeoutError` on failure.
- Built specifically for URL — nothing else.
- Natural fit for **flow control**: "hold here until the URL changes, then keep going with the rest of my script."

**`expect(page).to_have_url(pattern)`**
- A *web-first assertion*, from the `expect` API used for pass/fail checks (text, visibility, count, URL, title, etc. — one unified interface).
- Raises `AssertionError` on failure, with a nicely formatted diff (`Expected: ...` vs `Actual: ...`), which is much easier to read in test output/CI logs than a bare timeout.
- Same underlying polling mechanism as `wait_for_url` — both retry internally until timeout, both accept a string (glob), a regex, or a callable.

So functionally, for *just waiting on a URL*, they behave almost identically — same regex support, same retry-until-timeout behavior. The real difference is intent and error reporting:

|               | `wait_for_url()`                     | `expect(page).to_have_url()`                     |
| ------------- | ------------------------------------ | ------------------------------------------------ |
| Purpose       | Flow control ("wait, then continue") | Assertion ("verify this is true")                |
| Failure       | `TimeoutError`                       | `AssertionError` with expected/actual diff       |
| Best used in  | General automation/scraping scripts  | Test suites (pytest-playwright, Playwright Test) |
| Regex support | Yes                                  | Yes                                              |

**Which to use:**
- If you're writing **automation/scraping** (your original login → dashboard example), stick with `wait_for_url()` — that's exactly its job, and it reads more naturally than wrapping a wait in an assertion.
- If you're writing **tests** where the URL match *is* a test outcome you want reported clearly on failure ("did the login actually redirect correctly?"), use `expect(page).to_have_url()` — you get the nice diff output and it's the idiomatic style in Playwright's test framework.

A common pattern in real test suites is actually both together: `wait_for_url()` (or `expect_navigation`) to get past the redirect, then a separate `expect(...)` assertion afterward to verify something on the resulting page — because at that point you're no longer waiting, you're asserting a result.