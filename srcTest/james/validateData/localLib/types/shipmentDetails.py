from pydantic import BaseModel, Field, AfterValidator, BeforeValidator
from typing import Literal, Any, Annotated
from typing_extensions import TypedDict
from datetime import datetime
from decimal import Decimal
from localLib.utils.modelValidators import ModelValidators


class TCustomDataField(BaseModel):
    id: Annotated[int, Field(description="Unique identifier of the custom data field")]
    name: Annotated[str, Field(description="Name of the custom data field")]
    value: Annotated[str, Field(description="Value of the custom data field")]


class TInvoice(BaseModel):
    invoiceOrderNumber: Annotated[int, Field(description="Order number associated with the invoice")]
    invoiceNumber: Annotated[str, Field(description="Invoice number")]
    invoiceDate: Annotated[datetime | None, Field(description="Date the invoice was issued")]
    currencyCode: Annotated[
        str,
        Field("", description="Currency code of the invoice"),
        BeforeValidator(ModelValidators.toEmptyStrOnNull),
    ]


class TBookingItem(BaseModel):
    bookingItemId: Annotated[int, Field(description="Unique identifier of the booking item")]
    bookingItemIdPublic: Annotated[Any | None, Field(description="Public-facing identifier of the booking item")]
    bookingId: Annotated[int, Field(description="Unique identifier of the booking this item belongs to")]
    orderNumber: Annotated[str, Field(description="Purchase order number")]
    linkedOrderNumber: Annotated[str, Field(description="Linked purchase order number")]
    lot: Annotated[str, Field(description="Lot number")]
    itemCode: Annotated[str, Field(description="Item code")]
    productDescription: Annotated[str, Field(description="Description of the product")]
    totalUnits: Annotated[int, Field(description="Total number of units")]
    remainingUnits: Annotated[int, Field(description="Number of units remaining")]
    totalCartons: Annotated[int, Field(description="Total number of cartons")]
    remainingCartons: Annotated[int, Field(description="Number of cartons remaining")]
    totalCBM: Annotated[Decimal, Field(description="Total volume in cubic meters")]
    remainingCBM: Annotated[Decimal, Field(description="Remaining volume in cubic meters")]
    totalKGS: Annotated[Decimal, Field(description="Total weight in kilograms")]
    remainingKGS: Annotated[Decimal, Field(description="Remaining weight in kilograms")]
    itemPrice: Annotated[Decimal, Field(description="Price of the item")]
    warehouse: Annotated[str, Field(description="Warehouse name")]
    poItemMarks: Annotated[
        str,
        Field("", description="PO item marks"),
        BeforeValidator(ModelValidators.toEmptyStrOnNull),
    ]
    colour: Annotated[str, Field(description="Colour of the item")]
    vendorItemCode: Annotated[str, Field(description="Vendor's item code")]
    bookedItemPrice: Annotated[Decimal, Field(description="Price of the item at time of booking")]
    poItemPrice: Annotated[Decimal, Field(description="Price of the item on the purchase order")]
    buyingAgentCode: Annotated[str, Field(description="Code of the buying agent")]
    customDataFields: Annotated[
        list[TCustomDataField], Field(description="Custom data fields associated with the booking item")
    ]
    countryOfOrigin: Annotated[
        str,
        Field("", description="country of origin"),
        BeforeValidator(ModelValidators.toEmptyStrOnNull),
    ]
    countryOfManufacture: Annotated[
        str,
        Field("", description="country of manufacture"),
        BeforeValidator(ModelValidators.toEmptyStrOnNull),
    ]
    buyerName: Annotated[str, Field(description="Name of the buyer")]
    businessUnit: Annotated[str, Field(description="Business unit")]
    lineNum: Annotated[str, Field(description="Line number")]
    style: Annotated[
        str,
        Field("", description="style"),
        BeforeValidator(ModelValidators.toEmptyStrOnNull),
    ]
    destination: Annotated[str, Field(description="Destination")]
    supplierReference: Annotated[
        str,
        Field("", description="Supplier reference number"),
        BeforeValidator(ModelValidators.toEmptyStrOnNull),
    ]
    size: Annotated[str, Field(description="Size of the item")]
    outerPackType: Annotated[str, Field(description="Outer pack type")]


class TPurchaseOrder(BaseModel):
    orderNumber: Annotated[str, Field(description="Purchase order number")]
    linkedOrderNumber: Annotated[
        str,
        Field("", description="linked order number"),
        BeforeValidator(ModelValidators.toEmptyStrOnNull),
    ]
    deliveryDueDate: Annotated[datetime | None, Field(description="Date delivery is due")]
    supplierId: Annotated[int | None, Field(description="Unique identifier of the supplier")]
    businessUnit: Annotated[
        str,
        Field("", description="business unit"),
        BeforeValidator(ModelValidators.toEmptyStrOnNull),
    ]
    bookingItems: Annotated[
        list[TBookingItem],
        Field([], description="booking items"),
        BeforeValidator(
            ModelValidators.toEmptyListOnNull,
        ),
    ]


class TBooking(BaseModel):
    bookingNumber: Annotated[str, Field(description="Booking number")]
    originalCWShipmentNumber: Annotated[
        str,
        Field("", description="original cargowise shipment number"),
        BeforeValidator(ModelValidators.toEmptyStrOnNull),
    ]
    supplierName: Annotated[str, Field(description="Name of the supplier")]
    containers: Annotated[str, Field(description="Container numbers")]
    cbm: Annotated[Decimal, Field(description="Volume in cubic meters")]
    purchaseOrders: Annotated[list[TPurchaseOrder], Field(description="Purchase orders included in the booking")]


class TContainerType(BaseModel):
    name: Annotated[str, Field(description="Name of the container type")]
    maxCBM: Annotated[Decimal, Field(description="Maximum volume capacity in cubic meters")]
    maxKG: Annotated[Decimal, Field(description="Maximum weight capacity in kilograms")]
    cargowiseCode: Annotated[
        str,
        Field("", description="cargowise code"),
        BeforeValidator(ModelValidators.toEmptyStrOnNull),
    ]


class TContainerLine(BaseModel):
    bookingItemId: Annotated[int, Field(description="Unique identifier of the booking item")]
    orderNumber: Annotated[str, Field(description="Purchase order number")]
    linkedOrderNumber: Annotated[str, Field(description="Linked purchase order number")]
    lot: Annotated[str, Field(description="Lot number")]
    itemCode: Annotated[str, Field(description="Item code")]
    productDescription: Annotated[str, Field(description="Description of the product")]
    units: Annotated[int, Field(description="Number of units")]
    cartons: Annotated[int, Field(description="Number of cartons")]
    cbm: Annotated[Decimal, Field(description="Volume in cubic meters")]
    kgs: Annotated[Decimal, Field(description="Weight in kilograms")]
    netWeightKgs: Annotated[Decimal | None, Field(description="Net weight in kilograms")]
    invoice: Annotated[TInvoice, Field(description="Invoice associated with this container line")]
    itemPrice: Annotated[Decimal, Field(description="Price of the item")]
    batchCode: Annotated[str, Field(description="Batch code")]
    propertyMarks: Annotated[str, Field(description="Property marks")]
    loadSeq: Annotated[str, Field(description="Load sequence")]
    loadType: Annotated[
        str,
        Field("", description="Type of load"),
        BeforeValidator(ModelValidators.toEmptyStrOnNull),
    ]
    warehouse: Annotated[str, Field(description="Warehouse name")]
    colour: Annotated[str, Field(description="Colour of the item")]
    poItemMarks: Annotated[
        str,
        Field("", description="PO item marks"),
        BeforeValidator(ModelValidators.toEmptyStrOnNull),
    ]
    packTypeCode: Annotated[str, Field(description="Pack type code")]
    poItemPrice: Annotated[Decimal, Field(description="Price of the item on the purchase order")]
    customDataFields: Annotated[
        list[TCustomDataField], Field(description="Custom data fields associated with the container line")
    ]
    orderLineId: Annotated[int, Field(description="Unique identifier of the order line")]
    parentOrderLineId: Annotated[int | None, Field(description="Unique identifier of the parent order line")]
    vendorItemCode: Annotated[str, Field(description="Vendor's item code")]
    size: Annotated[str, Field(description="Size of the item")]
    bookedItemPrice: Annotated[Decimal, Field(description="Price of the item at time of booking")]
    buyingAgentCode: Annotated[
        str,
        Field("", description="Code of the buying agent"),
        BeforeValidator(ModelValidators.toEmptyStrOnNull),
    ]
    cfsDeliveredOrderLineId: Annotated[
        int | None, Field(description="Unique identifier of the CFS delivered order line")
    ]
    countryOfManufacture: Annotated[
        str,
        Field("", description="country of manufacture"),
        BeforeValidator(ModelValidators.toEmptyStrOnNull),
    ]
    countryOfOrigin: Annotated[
        str,
        Field("", description="country of origin"),
        BeforeValidator(ModelValidators.toEmptyStrOnNull),
    ]
    buyerName: Annotated[str, Field(description="Name of the buyer")]
    businessUnit: Annotated[str, Field(description="Business unit")]
    lineNum: Annotated[str, Field(description="Line number")]
    destination: Annotated[str, Field(description="Destination")]
    supplierReference: Annotated[
        str,
        Field("", description="supplier reference"),
        BeforeValidator(ModelValidators.toEmptyStrOnNull),
    ]
    style: Annotated[
        str,
        Field("", description="style"),
        BeforeValidator(ModelValidators.toEmptyStrOnNull),
    ]
    subPackType: Annotated[
        str,
        Field("", description="sub pack type"),
        BeforeValidator(ModelValidators.toEmptyStrOnNull),
    ]
    outerPackType: Annotated[str, Field(description="Outer pack type")]
    bookingNumber: Annotated[
        str,
        Field("", description="booking number"),
        BeforeValidator(ModelValidators.toEmptyStrOnNull),
    ]
    bookingItemIdPublic: Annotated[Any | None, Field(description="Public-facing identifier of the booking item")]


class TContainer(BaseModel):
    containerNumber: Annotated[str, Field(description="Container number")]
    type: Annotated[TContainerType, Field(description="Type of the container")]
    unitsUsed: Annotated[int, Field(description="Number of units used")]
    cartonsUsed: Annotated[int, Field(description="Number of cartons used")]
    cbmUsed: Annotated[Decimal, Field(description="Volume used in cubic meters")]
    kgsUsed: Annotated[Decimal, Field(description="Weight used in kilograms")]
    isFumigated: Annotated[bool | None, Field(description="Whether the container is fumigated")]
    containerLines: Annotated[list[TContainerLine], Field(description="Lines contained within the container")]
    sortOrder: Annotated[int, Field(description="Sort order of the container")]
    isVirtual: Annotated[bool, Field(description="Whether the container is virtual")]


class TInvoiceSettings(BaseModel):
    required: Annotated[bool, Field(description="Whether an invoice is required")]
    allowDefault: Annotated[bool, Field(description="Whether a default invoice is allowed")]
    postToCargoWise: Annotated[bool, Field(description="Whether invoices are posted to CargoWise")]
    dontAllowInvoiceReuse: Annotated[bool, Field(description="Whether invoice reuse is disallowed")]
    onlyAllowOneInvoice: Annotated[bool, Field(description="Whether only one invoice is allowed")]
    showInvoiceDate: Annotated[bool, Field(description="Whether the invoice date is shown")]
    maxCharacters: Annotated[int | None, Field(description="Maximum number of characters allowed")]
    allowedCurrencies: Annotated[list[str], Field(description="Currencies allowed for the invoice")]


class TValidationSettings(BaseModel):
    preventOrdersOnMultipleBKs: Annotated[
        bool, Field(description="Whether orders are prevented from spanning multiple bookings")
    ]
    allowZerosShipmentContainer: Annotated[
        bool, Field(description="Whether zero values are allowed in shipment containers")
    ]
    allowZeroPkgWeightCbm: Annotated[bool, Field(description="Whether zero package weight/CBM is allowed")]
    denyZeroPOTotalPkgWeightCbm: Annotated[
        bool, Field(description="Whether zero total package weight/CBM is denied for purchase orders")
    ]
    mandatoryLoadSequence: Annotated[bool, Field(description="Whether load sequence is mandatory")]
    poGroupValidations: Annotated[Any | None, Field(description="Purchase order group validation rules")]


class TShipmentCombineSettings(BaseModel):
    allowCombineShipmentsFromDifferentSuppliers: Annotated[
        bool, Field(description="Whether shipments from different suppliers can be combined")
    ]
    combinedShipmentsSupplierOverride: Annotated[
        Any | None, Field(description="Supplier override for combined shipments")
    ]


class TShipmentCreationSettings(BaseModel):
    deliveryModesToAutoPack: Annotated[list[str], Field(description="Delivery modes that are automatically packed")]
    additionalShipmentPropertyMapping: Annotated[list[Any], Field(description="Additional shipment property mappings")]


class TShipmentGroupSettings(BaseModel):
    createPackingStatus: Annotated[int, Field(description="Packing status set when the shipment group is created")]
    creationPolCountryCodes: Annotated[list[str], Field(description="Port of loading country codes used at creation")]


class TBookingItemDisplaySetting(BaseModel):
    containerOnly: Annotated[bool, Field(description="Whether the setting applies to containers only")]
    name: Annotated[str, Field(description="Name of the field")]
    show: Annotated[bool, Field(description="Whether the field is shown")]
    displayName: Annotated[str, Field(description="Display name of the field")]
    canEdit: Annotated[bool, Field(description="Whether the field can be edited")]


class TDeclarationOfOriginSettings(BaseModel):
    enabled: Annotated[bool, Field(description="Whether declaration of origin is enabled")]
    countriesToInclude: Annotated[
        list[str] | None, Field(description="Countries to include in the declaration of origin")
    ]


class TContainerPackingSettings(BaseModel):
    defaultPackType: Annotated[
        str,
        Field("", description="Default pack type"),
        BeforeValidator(ModelValidators.toEmptyStrOnNull),
    ]
    packTypesWithMandatorySubPackType: Annotated[
        list[str] | None, Field(description="Pack types that require a mandatory sub pack type")
    ]


class TShipmentConfirmationPermissions(BaseModel):
    preventSupplierConfirmationViaPortal: Annotated[
        bool, Field(description="Whether supplier confirmation via the portal is prevented")
    ]
    customSupplierMessageTemplate: Annotated[
        str,
        Field("", description="Custom message template shown to the supplier"),
        BeforeValidator(ModelValidators.toEmptyStrOnNull),
    ]
    supplierRedirectURL: Annotated[
        str,
        Field("", description="URL the supplier is redirected to"),
        BeforeValidator(ModelValidators.toEmptyStrOnNull),
    ]


class TShipmentSettings(BaseModel):
    invoiceSettings: Annotated[TInvoiceSettings, Field(description="Invoice settings")]
    validationSettings: Annotated[TValidationSettings, Field(description="Validation settings")]
    shipmentCombineSettings: Annotated[TShipmentCombineSettings, Field(description="Shipment combine settings")]
    shipmentCreationSettings: Annotated[TShipmentCreationSettings, Field(description="Shipment creation settings")]
    customEventHandlers: Annotated[list[Any], Field(description="Custom event handlers")]
    shipmentGroupSettings: Annotated[TShipmentGroupSettings, Field(description="Shipment group settings")]
    bookingItemDisplaySettings: Annotated[
        list[TBookingItemDisplaySetting], Field(description="Display settings for booking items")
    ]
    customFieldSettings: Annotated[list[Any], Field(description="Custom field settings")]
    declarationOfOriginSettings: Annotated[
        TDeclarationOfOriginSettings, Field(description="Declaration of origin settings")
    ]
    containerPackingSettings: Annotated[TContainerPackingSettings, Field(description="Container packing settings")]
    shipmentConfirmationPermissions: Annotated[
        TShipmentConfirmationPermissions, Field(description="Shipment confirmation permissions")
    ]


class TShipmentDetail(BaseModel):
    cwShipmentNumber: Annotated[str, Field(description="CargoWise shipment number")]
    deliveryMode: Annotated[str, Field(description="Delivery mode")]
    modeOfTransport: Annotated[str, Field(description="Mode of transport")]
    consigneeId: Annotated[int, Field(description="Unique identifier of the consignee")]
    invoices: Annotated[list[TInvoice], Field(description="Invoices associated with the shipment")]
    bookingPurchaseOrders: Annotated[
        list[TPurchaseOrder], Field(description="Purchase orders associated with the shipment's bookings")
    ]
    bookings: Annotated[list[TBooking], Field(description="Bookings associated with the shipment")]
    cfsDeliveredOrders: Annotated[list[Any], Field(description="Orders delivered via CFS")]
    isReadOnly: Annotated[bool, Field(description="Whether the shipment is read-only")]
    allBookingsSAApproved: Annotated[bool, Field(description="Whether all bookings are SA approved")]
    hasCargoWiseATHEvent: Annotated[bool, Field(description="Whether the shipment has a CargoWise ATH event")]
    cfsDeliveredDate: Annotated[datetime | None, Field(description="Date the shipment was delivered to CFS")]
    portDeliveredDate: Annotated[datetime | None, Field(description="Date the shipment was delivered to port")]
    canBeUncombined: Annotated[bool, Field(description="Whether the shipment can be uncombined")]
    dontAllowInvoiceReuse: Annotated[bool, Field(description="Whether invoice reuse is disallowed")]
    onlyAllowOneInvoice: Annotated[bool, Field(description="Whether only one invoice is allowed")]
    shipmentType: Annotated[str, Field(description="Type of shipment")]
    id: Annotated[int, Field(description="Unique identifier of the shipment")]
    shipmentState: Annotated[str, Field(description="State of the shipment")]
    containers: Annotated[list[TContainer], Field(description="Containers included in the shipment")]
    shipmentSettings: Annotated[TShipmentSettings, Field(description="Settings for the shipment")]
