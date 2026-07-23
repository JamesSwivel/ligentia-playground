#!/usr/bin/env python
"""
checkJwt.py - Decode and inspect a JWT (JSON Web Token).

Usage:
    cat jwt.txt | checkJwt.py
    checkJwt.py -f <jwtFile>
    checkJwt.py -q -f <jwtFile>   # quiet mode, no stdout/stderr output
    checkJwt.py --help

The script decodes the header and payload of a JWT (base64url, no
signature verification is performed unless a secret/key is supplied)
and prints them as formatted JSON. It also reports on standard time
based claims (exp, iat, nbf) if present.

Exit codes (useful for bash scripting):
    0 - payload was decoded successfully and the token is NOT expired
    1 - payload was decoded successfully but the token IS expired
    2 - any unexpected error (bad input, malformed JWT, file not found, etc.)
"""

import argparse
import base64
import json
import sys
import time
from datetime import datetime, timezone
from typing import NoReturn

# Exit codes
EXIT_OK = 0  # decoded fine, not expired
EXIT_EXPIRED = 1  # decoded fine, but expired
EXIT_ERROR = 2  # unexpected error

# Set once argparse has run; controls whether we print anything at all.
quietMode = False


def out(msg: str = "") -> None:
    """Print to stdout, unless quiet mode is enabled."""
    if not quietMode:
        print(msg)


def err(msg: str = "") -> None:
    """Print to stderr, unless quiet mode is enabled."""
    if not quietMode:
        print(msg, file=sys.stderr)


def fail(msg: str, code: int = EXIT_ERROR) -> NoReturn:
    """Report an error (respecting quiet mode) and exit with the given code."""
    err(f"Error: {msg}")
    sys.exit(code)


def b64UrlDecode(segment: str) -> bytes:
    """Decode a base64url-encoded JWT segment, adding padding as needed."""
    padding = "=" * (-len(segment) % 4)
    return base64.urlsafe_b64decode(segment + padding)


def decodeSegment(segment: str, name: str) -> dict:
    try:
        raw = b64UrlDecode(segment)
        return json.loads(raw)
    except Exception as exc:
        fail(f"could not decode JWT {name}: {exc}")


def fmtTimestamp(ts) -> str:
    try:
        # Convert to UTC first, then to the system's local timezone.
        dtUtc = datetime.fromtimestamp(int(ts), tz=timezone.utc)
        dtLocal = dtUtc.astimezone()  # uses the system's local tz
        return dtLocal.strftime("%Y-%m-%d %H:%M:%S %Z")
    except Exception:
        return str(ts)


def checkTimeClaims(payload: dict) -> bool:
    """
    Print (unless quiet) the time-based claims and return whether the
    token is currently expired (True = expired, False = not expired).
    A token with no 'exp' claim is treated as not expired.
    """
    now = int(time.time())
    isExpired = False

    out("\n--- Time-based claims ---")

    if "iat" in payload:
        out(f"iat (issued at):   {payload['iat']}  ({fmtTimestamp(payload['iat'])})")

    if "nbf" in payload:
        nbf = payload["nbf"]
        status = "not yet valid" if now < int(nbf) else "valid (nbf passed)"
        out(f"nbf (not before):  {nbf}  ({fmtTimestamp(nbf)}) -- {status}")

    if "exp" in payload:
        exp = payload["exp"]
        remaining = int(exp) - now
        if remaining > 0:
            status = f"VALID, expires in {remaining} seconds"
        else:
            status = f"EXPIRED {abs(remaining)} seconds ago"
            isExpired = True
        out(f"exp (expires at):  {exp}  ({fmtTimestamp(exp)}) -- {status}")

    if not any(k in payload for k in ("iat", "nbf", "exp")):
        out("No standard time-based claims (iat, nbf, exp) found.")

    return isExpired


def readToken(args) -> str:
    if args.file:
        try:
            with open(args.file, "r") as f:
                token = f.read()
        except OSError as exc:
            fail(f"could not read file '{args.file}': {exc}")
    else:
        if sys.stdin.isatty():
            fail("no JWT provided. Pipe a token via stdin, or use -f <file>.\n" "Run 'checkJwt.py --help' for usage.")
        token = sys.stdin.read()

    return token.strip()


def main():
    global quietMode

    parser = argparse.ArgumentParser(
        prog="checkJwt.py",
        description="Decode and inspect a JWT's header and payload, and check its time-based claims.",
    )
    parser.add_argument(
        "-f",
        "--file",
        metavar="jwtFile",
        help="Path to a file containing the JWT. If omitted, the token is read from stdin.",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress all stdout/stderr output. Only the exit code is set "
        "(0=valid, 1=expired, 2=error). Useful when calling this script "
        "from another bash script that only cares about the exit status.",
    )
    args = parser.parse_args()
    quietMode = args.quiet

    try:
        token = readToken(args)

        if not token:
            fail("empty JWT input.")

        parts = token.split(".")
        if len(parts) != 3:
            fail(f"invalid JWT format. Expected 3 dot-separated segments, got {len(parts)}.")

        headerB64, payloadB64, signatureB64 = parts

        header = decodeSegment(headerB64, "header")
        payload = decodeSegment(payloadB64, "payload")

        out("--- Header ---")
        out(json.dumps(header, indent=2))

        out("\n--- Payload ---")
        out(json.dumps(payload, indent=2))

        out(f"\n--- Signature ---\n{signatureB64}")
        out("(Signature is displayed but not verified. Verification requires the signing key/secret.)")

        isExpired = checkTimeClaims(payload)

        sys.exit(EXIT_EXPIRED if isExpired else EXIT_OK)

    except SystemExit:
        # Let sys.exit() calls (from fail() or the expiry check above) propagate as-is.
        raise
    except Exception as exc:
        # Catch-all for anything truly unexpected.
        fail(f"unexpected failure: {exc}")


if __name__ == "__main__":
    main()
