from pydantic import BaseModel, Field
from typing import Literal, Annotated
from typing_extensions import TypedDict
from datetime import datetime
from decimal import Decimal
from datetime import datetime


class TContainer(BaseModel):
    containerNumber: Annotated[str, Field(description="Container number")]
    containerType: Annotated[str, Field(description="Type of the container")]


class TPackingLine(BaseModel):
    containerNumber: Annotated[str, Field(description="Container number")]
    packQty: Annotated[int, Field(description="Number of packs")]
    packType: Annotated[str, Field(description="Pack type")]
    volume: Annotated[Decimal, Field(description="Volume of the packing line")]
    volumeUnit: Annotated[str, Field(description="Unit of measure for volume")]
    weight: Annotated[Decimal, Field(description="Weight of the packing line")]
    weightUnit: Annotated[str, Field(description="Unit of measure for weight")]
    referenceNumber: Annotated[str, Field(description="Reference number")]
    goodsDescription: Annotated[str, Field(description="Description of the goods")]
    marksAndNos: Annotated[str, Field(description="Marks and numbers")]
    importReferenceNumber: Annotated[str, Field(description="Import reference number")]


class TTransportLeg(BaseModel):
    legOrder: Annotated[int, Field(description="Order of the transport leg")]
    vesselName: Annotated[str, Field(description="Name of the vessel")]
    carrier: Annotated[str, Field(description="Carrier name")]
    pol: Annotated[str, Field(description="Port of loading")]
    pod: Annotated[str, Field(description="Port of discharge")]
    voyageFlightNo: Annotated[str, Field(description="Voyage or flight number")]


class TShipmentSummary(BaseModel):
    cwShipmentNumber: Annotated[str, Field(description="CargoWise shipment number")]
    bookingNumber: Annotated[str, Field(description="Booking number")]
    hasCustomsDeclaration: Annotated[bool, Field(description="Whether a customs declaration exists")]
    consignee: Annotated[str, Field(description="Consignee name")]
    vesselName: Annotated[str, Field(description="Name of the vessel")]
    vesselNames: Annotated[list[str], Field(description="Names of the vessels")]

    outerPacks: Annotated[int, Field(description="Number of outer packs")]
    outerPacksPackageType: Annotated[str, Field(description="Package type of the outer packs")]

    documentedVolume: Annotated[Decimal, Field(description="Documented volume")]
    totalVolume: Annotated[Decimal, Field(description="Total volume")]
    totalVolumeUnit: Annotated[str, Field(description="Unit of measure for total volume")]

    documentedWeight: Annotated[Decimal, Field(description="Documented weight")]
    totalWeight: Annotated[Decimal, Field(description="Total weight")]
    totalWeightUnit: Annotated[str, Field(description="Unit of measure for total weight")]

    pol: Annotated[str, Field(description="Port of loading")]
    pod: Annotated[str, Field(description="Port of discharge")]
    etd: Annotated[datetime, Field(description="Estimated time of departure")]
    eta: Annotated[datetime, Field(description="Estimated time of arrival")]

    supplierName: Annotated[str, Field(description="Name of the supplier")]
    vendorClientId: Annotated[int, Field(description="Unique identifier of the vendor client")]

    containers: Annotated[list[TContainer], Field(description="Containers included in the shipment")]
    packingLines: Annotated[list[TPackingLine], Field(description="Packing lines included in the shipment")]
    transportLegs: Annotated[list[TTransportLeg], Field(description="Transport legs of the shipment")]
