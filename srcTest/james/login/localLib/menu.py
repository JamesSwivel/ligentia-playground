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

from .app import *


def askMenu():
    username = ""
    password = ""
    hostname = ""
    TEST_MENU = "1. UAT | 2. PROD | 0. Exit > "
    menuInt = U.askQuestionInt(TEST_MENU, {"validValues": [0, 1, 2], "isShowValidValues": False})
    match menuInt:
        case 0:
            return None
        case 1:
            username = App.EnvConfig.get("UAT_USER")
            password = App.EnvConfig.get("UAT_PASSWORD")
            hostname = App.EnvConfig.get("UAT_HOST")

            # main_supplier_url = "https://supplier.uat1.ligentix.net/"
            # regex_NotLogin = r"^((?!supplier\.uat1\.ligentix\.net/login).)*$"
            # regex_signin_callback = r"^.*supplier\.uat1\.ligentix\.net/signin-callback.*$"
            # supplier_wildcard = "**/supplier.uat1.ligentix.net/"
            # regex_identity = r"^.*identity\.uat1\.ligentix\.net/.*$"

        case 2:
            username = App.EnvConfig.get("PROD_USER")
            password = App.EnvConfig.get("PROD_PASSWORD")
            hostname = App.EnvConfig.get("PROD_HOST")

            # main_supplier_url = "https://supplier.ligentix.net/"
            # regex_NotLogin = r"^((?!supplier\.ligentix\.net/login).)*$"
            # regex_signin_callback = r"^.*supplier\.ligentix\.net/signin-callback.*$"
            # supplier_wildcard = "**/supplier.ligentix.net/"
            # regex_identity = r"^.*identity\.ligentix\.net/.*$"

    if username is None or password is None or hostname is None:
        raise Exception("invalid username/password/hostname")

    return username, password, hostname
