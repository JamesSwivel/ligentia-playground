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


class TPort(BaseModel):
    portCode: str
    countryCode: str


class TShipmentBookingSearch(BaseModel):
    cbm: Decimal
    bookingId: int
    bookingNumber: str
    clientId: int
    clientName: str
    vendorName: str
    vendorClientId: int
    vendorCargoWiseCode: str
    supplierName: str
    motherVesselName: str
    motherVesselCarrierName: str
    motherVesselCarrierCode: str
    etd: datetime
    pol: TPort
    mot: str
    status: str
    deliveryMode: str
    cwRef: str
    isReadOnly: bool
    isFumigated: bool
    containers: str
    incoTerm: str
    incoTermPort: TPort
    shipmentStatus: str
    bookingApproved: bool
    createdByUserId: int
