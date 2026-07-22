import sys
import asyncio
import json
import re
import os
from pydantic import BaseModel, Field
from pathlib import Path
from typing import Literal, Annotated
from typing_extensions import TypedDict
import swivel.common as U

TBookingScenarioId = Literal[
    "1",
    "2",
    "3",
    "4",
    "1.part2",
    "2.part2",
]


SCENARIO_BASE_DIRS: dict[
    TBookingScenarioId,
    str,
] = {
    "1": "data/Data Extraction/Scenario 1",
    "2": "data/Data Extraction/Scenario 2",
    "3": "data/Data Extraction/Scenario 3",
    "4": "data/Data Extraction/Scenario 4",
    "1.part2": "data/Data Extraction/Scenario 1 (PART 2)",
    "2.part2": "data/Data Extraction/Scenario 2 (PART 2)",
}


class TBookingScenarios(TypedDict):
    env: Literal["UAT", "PROD"]
    scenarioId: TBookingScenarioId
    bookingNumber: str
    cwShipmentNumber: str
