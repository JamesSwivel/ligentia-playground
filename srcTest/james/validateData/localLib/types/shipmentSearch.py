from pydantic import BaseModel, Field, AfterValidator, BeforeValidator
from typing import Literal, Annotated
from typing_extensions import TypedDict
from datetime import datetime
from decimal import Decimal
from .common import *
from localLib.utils.modelValidators import ModelValidators


class TShipmentSearchItem(BaseModel):
    id: Annotated[int, Field(description="Unique identifier of the shipment")]
    bookingNumber: Annotated[str, Field(description="Booking number")]
    cwShipmentNumber: Annotated[str, Field(description="CargoWise shipment number")]
    consolId: Annotated[str, Field(description="Consolidation identifier")]

    supplier: Annotated[TCwParty, Field(description="Supplier of the shipment")]
    consignee: Annotated[TCwParty, Field(description="Consignee of the shipment")]

    pol: Annotated[TPort, Field(description="Port of loading")]
    pod: Annotated[TPort, Field(description="Port of discharge")]

    eta: Annotated[datetime, Field(description="Estimated time of arrival")]
    etd: Annotated[datetime, Field(description="Estimated time of departure")]

    deliveryMode: Annotated[str, Field(description="Delivery mode")]
    modeOfTransport: Annotated[str, Field(description="Mode of transport")]

    motherVesselName: Annotated[str, Field(description="Name of the mother vessel")]
    motherVesselCarrierName: Annotated[str, Field(description="Name of the mother vessel's carrier")]
    motherVesselCarrierCode: Annotated[str, Field(description="Code of the mother vessel's carrier")]

    dateCreated: Annotated[datetime, Field(description="Date the shipment was created")]
    shipmentState: Annotated[str, Field(description="State of the shipment")]
    hasATH: Annotated[bool, Field(description="Whether the shipment has an ATH event")]

    shipmentGroupRef: Annotated[
        str,
        Field("", description="Reference of the shipment group"),
        BeforeValidator(ModelValidators.toEmptyStrOnNull),
    ]
    containers: Annotated[str, Field(description="Container numbers")]


class TShipmentSearch(BaseModel):
    results: Annotated[list[TShipmentSearchItem], Field(description="search results")]
