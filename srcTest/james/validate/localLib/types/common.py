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


class TPort(BaseModel):
    portCode: str
    countryCode: str


class TCwParty(BaseModel):
    id: int
    cargoWiseCode: str
    name: str


class TBookingScenarios(TypedDict):
    env: Literal["UAT", "PROD"]
    scenario: str
    bookingNumber: str
    cwShipmentNumber: str
