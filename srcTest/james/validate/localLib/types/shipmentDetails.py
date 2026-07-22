import sys
import asyncio
import json
import re
import os
from pydantic import BaseModel, Field
from pathlib import Path
from typing import Literal, Any, Annotated
from typing_extensions import TypedDict
import swivel.common as U
from datetime import datetime
from decimal import Decimal
from .common import *
from datetime import datetime


class TCustomDataField(BaseModel):
    id: int
    name: str
    value: str


class TInvoice(BaseModel):
    invoiceOrderNumber: int
    invoiceNumber: str
    invoiceDate: datetime | None
    currencyCode: Annotated[str, Field("", description="currency code")]


class TBookingItem(BaseModel):
    bookingItemId: int
    bookingItemIdPublic: Any | None
    bookingId: int
    orderNumber: str
    linkedOrderNumber: str
    lot: str
    itemCode: str
    productDescription: str
    totalUnits: int
    remainingUnits: int
    totalCartons: int
    remainingCartons: int
    totalCBM: Decimal
    remainingCBM: Decimal
    totalKGS: Decimal
    remainingKGS: Decimal
    itemPrice: Decimal
    warehouse: str
    poItemMarks: Annotated[str, Field("", description="PO item marks")]
    colour: str
    vendorItemCode: str
    bookedItemPrice: Decimal
    poItemPrice: Decimal
    buyingAgentCode: str
    customDataFields: list[TCustomDataField]
    countryOfOrigin: Annotated[str, Field("", description="country of origin")]
    countryOfManufacture: Annotated[str, Field("", description="country of manufacture")]
    buyerName: str
    businessUnit: str
    lineNum: str
    style: Annotated[str, Field("", description="style")]
    destination: str
    supplierReference: str | None
    size: str
    outerPackType: str


class TPurchaseOrder(BaseModel):
    orderNumber: str
    linkedOrderNumber: Annotated[str, Field("", description="linked order number")]
    deliveryDueDate: datetime | None
    supplierId: int | None
    businessUnit: Annotated[str, Field("", description="business unit")]
    bookingItems: Annotated[list[TBookingItem], Field([], description="booking items")]


class TBooking(BaseModel):
    bookingNumber: str
    originalCWShipmentNumber: Annotated[str, Field("", description="original cargowise shipment number")]
    supplierName: str
    containers: str
    cbm: Decimal
    purchaseOrders: list[TPurchaseOrder]


class TContainerType(BaseModel):
    name: str
    maxCBM: Decimal
    maxKG: Decimal
    cargowiseCode: Annotated[str, Field("", description="cargowise code")]


class TContainerLine(BaseModel):
    bookingItemId: int
    orderNumber: str
    linkedOrderNumber: str
    lot: str
    itemCode: str
    productDescription: str
    units: int
    cartons: int
    cbm: Decimal
    kgs: Decimal
    netWeightKgs: Decimal | None
    invoice: TInvoice
    itemPrice: Decimal
    batchCode: str
    propertyMarks: str
    loadSeq: str
    loadType: str | None
    warehouse: str
    colour: str
    poItemMarks: str | None
    packTypeCode: str
    poItemPrice: Decimal
    customDataFields: list[TCustomDataField]
    orderLineId: int
    parentOrderLineId: int | None
    vendorItemCode: str
    size: str
    bookedItemPrice: Decimal
    buyingAgentCode: str | None
    cfsDeliveredOrderLineId: int | None
    countryOfManufacture: Annotated[str, Field("", description="country of manufacture")]
    countryOfOrigin: Annotated[str, Field("", description="country of origin")]
    buyerName: str
    businessUnit: str
    lineNum: str
    destination: str
    supplierReference: Annotated[str, Field("", description="supplier reference")]
    style: Annotated[str, Field("", description="style")]
    subPackType: Annotated[str, Field("", description="sub pack type")]
    outerPackType: str
    bookingNumber: Annotated[str, Field("", description="booking number")]
    bookingItemIdPublic: Any | None


class TContainer(BaseModel):
    containerNumber: str
    type: TContainerType
    unitsUsed: int
    cartonsUsed: int
    cbmUsed: Decimal
    kgsUsed: Decimal
    isFumigated: bool | None
    containerLines: list[TContainerLine]
    sortOrder: int
    isVirtual: bool


class TInvoiceSettings(BaseModel):
    required: bool
    allowDefault: bool
    postToCargoWise: bool
    dontAllowInvoiceReuse: bool
    onlyAllowOneInvoice: bool
    showInvoiceDate: bool
    maxCharacters: int | None
    allowedCurrencies: list[str]


class TValidationSettings(BaseModel):
    preventOrdersOnMultipleBKs: bool
    allowZerosShipmentContainer: bool
    allowZeroPkgWeightCbm: bool
    denyZeroPOTotalPkgWeightCbm: bool
    mandatoryLoadSequence: bool
    poGroupValidations: Any | None


class TShipmentCombineSettings(BaseModel):
    allowCombineShipmentsFromDifferentSuppliers: bool
    combinedShipmentsSupplierOverride: Any | None


class TShipmentCreationSettings(BaseModel):
    deliveryModesToAutoPack: list[str]
    additionalShipmentPropertyMapping: list[Any]


class TShipmentGroupSettings(BaseModel):
    createPackingStatus: int
    creationPolCountryCodes: list[str]


class TBookingItemDisplaySetting(BaseModel):
    containerOnly: bool
    name: str
    show: bool
    displayName: str
    canEdit: bool


class TDeclarationOfOriginSettings(BaseModel):
    enabled: bool
    countriesToInclude: list[str] | None


class TContainerPackingSettings(BaseModel):
    defaultPackType: str | None
    packTypesWithMandatorySubPackType: list[str] | None


class TShipmentConfirmationPermissions(BaseModel):
    preventSupplierConfirmationViaPortal: bool
    customSupplierMessageTemplate: str | None
    supplierRedirectURL: str | None


class TShipmentSettings(BaseModel):
    invoiceSettings: TInvoiceSettings
    validationSettings: TValidationSettings
    shipmentCombineSettings: TShipmentCombineSettings
    shipmentCreationSettings: TShipmentCreationSettings
    customEventHandlers: list[Any]
    shipmentGroupSettings: TShipmentGroupSettings
    bookingItemDisplaySettings: list[TBookingItemDisplaySetting]
    customFieldSettings: list[Any]
    declarationOfOriginSettings: TDeclarationOfOriginSettings
    containerPackingSettings: TContainerPackingSettings
    shipmentConfirmationPermissions: TShipmentConfirmationPermissions


class TShipment(BaseModel):
    cwShipmentNumber: str
    deliveryMode: str
    modeOfTransport: str
    consigneeId: int
    invoices: list[TInvoice]
    bookingPurchaseOrders: list[TPurchaseOrder]
    bookings: list[TBooking]
    cfsDeliveredOrders: list[Any]
    isReadOnly: bool
    allBookingsSAApproved: bool
    hasCargoWiseATHEvent: bool
    cfsDeliveredDate: datetime | None
    portDeliveredDate: datetime | None
    canBeUncombined: bool
    dontAllowInvoiceReuse: bool
    onlyAllowOneInvoice: bool
    shipmentType: str
    id: int
    shipmentState: str
    containers: list[TContainer]
    shipmentSettings: TShipmentSettings
