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
from datetime import datetime
from decimal import Decimal
from .common import *

from datetime import datetime

from pydantic import BaseModel


class TShipmentSearch(BaseModel):
    id: int
    bookingNumber: str
    cwShipmentNumber: str
    consolId: str

    supplier: TCwParty
    consignee: TCwParty

    pol: TPort
    pod: TPort

    eta: datetime
    etd: datetime

    deliveryMode: str
    modeOfTransport: str

    motherVesselName: str
    motherVesselCarrierName: str
    motherVesselCarrierCode: str

    dateCreated: datetime
    shipmentState: str
    hasATH: bool

    shipmentGroupRef: str | None
    containers: str
