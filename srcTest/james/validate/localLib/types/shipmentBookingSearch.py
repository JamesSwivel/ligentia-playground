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
from datetime import datetime
from decimal import Decimal


class TPort(BaseModel):
    portCode: Annotated[str, Field(description="Port code")]
    countryCode: Annotated[str, Field(description="Country code of the port")]


class TShipmentBookingSearch(BaseModel):
    cbm: Annotated[Decimal, Field(description="Volume in cubic meters")]
    bookingId: Annotated[int, Field(description="Unique identifier of the booking")]
    bookingNumber: Annotated[str, Field(description="Booking number")]
    clientId: Annotated[int, Field(description="Unique identifier of the client")]
    clientName: Annotated[str, Field(description="Name of the client")]
    vendorName: Annotated[str, Field(description="Name of the vendor")]
    vendorClientId: Annotated[int, Field(description="Unique identifier of the vendor client")]
    vendorCargoWiseCode: Annotated[str, Field(description="CargoWise code of the vendor")]
    supplierName: Annotated[str, Field(description="Name of the supplier")]
    motherVesselName: Annotated[str, Field(description="Name of the mother vessel")]
    motherVesselCarrierName: Annotated[str, Field(description="Name of the mother vessel's carrier")]
    motherVesselCarrierCode: Annotated[str, Field(description="Code of the mother vessel's carrier")]
    etd: Annotated[datetime, Field(description="Estimated time of departure")]
    pol: Annotated[TPort, Field(description="Port of loading")]
    mot: Annotated[str, Field(description="Mode of transport")]
    status: Annotated[str, Field(description="Status of the booking")]
    deliveryMode: Annotated[str, Field(description="Delivery mode")]
    cwRef: Annotated[str, Field(description="CargoWise reference")]
    isReadOnly: Annotated[bool, Field(description="Whether the booking is read-only")]
    isFumigated: Annotated[bool, Field(description="Whether the booking is fumigated")]
    containers: Annotated[str, Field(description="Container numbers")]
    incoTerm: Annotated[str, Field(description="Incoterm")]
    incoTermPort: Annotated[TPort, Field(description="Port associated with the Incoterm")]
    shipmentStatus: Annotated[str, Field(description="Status of the shipment")]
    bookingApproved: Annotated[bool, Field(description="Whether the booking is approved")]
    createdByUserId: Annotated[int, Field(description="Unique identifier of the user who created the booking")]
