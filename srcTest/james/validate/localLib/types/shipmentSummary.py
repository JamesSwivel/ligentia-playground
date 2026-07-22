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


class TContainer(BaseModel):
    containerNumber: str
    containerType: str


class TPackingLine(BaseModel):
    containerNumber: str
    packQty: int
    packType: str
    volume: Decimal
    volumeUnit: str
    weight: Decimal
    weightUnit: str
    referenceNumber: str
    goodsDescription: str
    marksAndNos: str
    importReferenceNumber: str


class TTransportLeg(BaseModel):
    legOrder: int
    vesselName: str
    carrier: str
    pol: str
    pod: str
    voyageFlightNo: str


class TShipmentSummary(BaseModel):
    cwShipmentNumber: str
    bookingNumber: str
    hasCustomsDeclaration: bool
    consignee: str
    vesselName: str
    vesselNames: list[str]

    outerPacks: int
    outerPacksPackageType: str

    documentedVolume: Decimal
    totalVolume: Decimal
    totalVolumeUnit: str

    documentedWeight: Decimal
    totalWeight: Decimal
    totalWeightUnit: str

    pol: str
    pod: str
    etd: datetime
    eta: datetime

    supplierName: str
    vendorClientId: int

    containers: list[TContainer]
    packingLines: list[TPackingLine]
    transportLegs: list[TTransportLeg]
