#!/usr/bin/env python

import sys
import asyncio
import json
import re
import os
from pydantic import BaseModel, Field
from pathlib import Path
from typing import Literal
from typing_extensions import TypedDict
import swivel.common as U

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


from localLib.types import *
from localLib.utils import TypeHelper

Bookings: dict[str, TBookingScenarios] = {
    "S01863302": {
        "env": "UAT",
        "scenarioId": "1",
        "bookingNumber": "SE0612240084",
        "cwShipmentNumber": "S01863302",
    }
}


async def loadScenarioData(shipmentNum: str):
    funcName = loadScenarioData.__name__
    prefix = funcName
    try:
        if not shipmentNum in Bookings:
            raise Exception(f"shipmentNum not found: {shipmentNum}")
        booking = Bookings[shipmentNum]

        scenarioId = booking["scenarioId"]
        if not scenarioId in SCENARIO_BASE_DIRS:
            raise Exception(f"invalid scenarioId: {scenarioId}")
        scenarioBaseDir = SCENARIO_BASE_DIRS[scenarioId]

        ## load JSON file
        jsonBaseDir = f"{scenarioBaseDir}/{shipmentNum}/api"

        currencyJsonFile = f"{jsonBaseDir}/currencies.res.json"
        currency = U.readFile(currencyJsonFile, "json")

        jsonFile = f"{jsonBaseDir}/shipmentBookingSearch.res.json"
        shipmentBookingSearch = TypeHelper.toBaseModel(TShipmentBookingSearch, Path(jsonFile))

        jsonFile = f"{jsonBaseDir}/shipmentDetails.res.json"
        shipmentDetail = TypeHelper.toBaseModel(TShipmentDetail, Path(jsonFile))

        jsonFile = f"{jsonBaseDir}/shipmentSearch.res.json"
        shipmentSearch = TypeHelper.toBaseModel(TShipmentSearch, Path(jsonFile))

        jsonFile = f"{jsonBaseDir}/shipmentSummary.res.json"
        shipmentSummary = TypeHelper.toBaseModel(TShipmentSummary, Path(jsonFile))

    except Exception as e:
        U.throwPrefix(prefix, e)


async def main():
    funcName = main.__name__
    prefix = funcName
    try:
        U.logW(f"{prefix} hello")
        await loadScenarioData("S01863302")
    except Exception as e:
        U.throwPrefix(prefix, e)


if __name__ == "__main__":
    prefix = "__main__"
    try:
        asyncio.run(main())
    except Exception as e:
        U.logPrefixE(prefix, e)
