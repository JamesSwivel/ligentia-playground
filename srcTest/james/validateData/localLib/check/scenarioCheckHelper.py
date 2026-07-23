from pydantic import BaseModel, Field
from pathlib import Path
from operator import attrgetter
from typing import Literal, Annotated, Any, TypeVar
from typing_extensions import TypedDict
import swivel.common as U

from localLib.types import *
from localLib.app import App
from localLib.utils import TypeHelper
from .bookingsMeta import BookingsMetaData


class ScenarioCheckHelper:

    class TCheckStats(TypedDict):
        search: int
        bookingSummary: int
        bookingDetail: int

    @classmethod
    def checkSearchHeaders(cls, input: TBookingScenarioDirMeta | str):
        funcName = cls.checkSearchHeaders.__name__
        prefix = funcName
        try:
            if isinstance(input, str):
                if not input in BookingsMetaData:
                    raise Exception(f"invalid shipmentNum: {input}")
                scenarioData = BookingsMetaData[input]
            else:
                scenarioData = input

            shipmentNum = scenarioData["cwShipmentNumber"]
            bookingNum = scenarioData["bookingNumber"]
            prefix = f"{prefix}[{shipmentNum}:{bookingNum}]"
            U.logW(f"{prefix} >>>> checking scenario headers")
            data = scenarioData["data"]
            if data is None or not data["isValid"]:
                raise Exception(f"invalid scenario data")

            stats: ScenarioCheckHelper.TCheckStats = {
                "search": 0,
                "bookingSummary": 0,
                "bookingDetail": 0,
            }
            statsTotalExpected: ScenarioCheckHelper.TCheckStats = {
                "search": 0,
                "bookingSummary": 0,
                "bookingDetail": 0,
            }

            ##################################################
            ## Step 1: search headers
            ##################################################
            shipmentSearch = data["shipmentSearch"].results[0]
            shipmentBookingSearch = data["shipmentBookingSearch"]
            shipmentSummary = data["shipmentSummary"]
            shipmentDetail = data["shipmentDetail"]

            expectedCount = cls.compareFields(
                shipmentSearch,
                shipmentBookingSearch,
                [
                    ("bookingNumber", "bookingNumber"),
                    ("cwShipmentNumber", "cwRef"),
                    ("supplier.id", "vendorClientId"),
                    ("supplier.name", "vendorName"),
                    ("consignee.id", "clientId"),
                    ("consignee.name", "clientName"),
                    ("modeOfTransport", "mot"),
                    ("deliveryMode", "deliveryMode"),
                ],
                label="searchHeaders",
                stats=stats,
                stats_key="search",
            )
            statsTotalExpected["search"] = expectedCount

            ##################################################
            ## Step 2: booking search vs summary
            ##################################################
            expectedCount = cls.compareFields(
                shipmentBookingSearch,
                shipmentSummary,
                [
                    ("cwRef", "cwShipmentNumber"),
                    ("bookingNumber", "bookingNumber"),
                    ("clientName", "consignee", "noThrow"),
                    ("vendorName", "supplierName"),
                ],
                label="bookingSearchVsSummary",
                stats=stats,
                stats_key="bookingSummary",
            )
            statsTotalExpected["bookingSummary"] = expectedCount

            ##################################################
            ## Step 3: booking search vs detail
            ##################################################

            ## Should be single booking number and must be matched with the booking search's booking number
            bookingNumbers = [booking.bookingNumber for booking in shipmentDetail.bookings]
            if len(bookingNumbers) != 1:
                raise Exception(f"bookingNumbers count > 1: {len(bookingNumbers)}")
            if not shipmentBookingSearch.bookingNumber in bookingNumbers:
                raise Exception(f"shipmentBookingSearch.bookingNumber not found in detail bookingNumbers")
            U.logD(f"{prefix} shipmentDetail bookingNumber={bookingNumbers[0]}")

            ## Supplier ID should be one and must be matched with the booking search
            supplierIds = list(
                set([order.supplierId for booking in shipmentDetail.bookings for order in booking.purchaseOrders])
            )
            if len(supplierIds) != 1:
                raise Exception(f"supplierIds count > 1: {len(supplierIds)}")
            if not shipmentBookingSearch.vendorClientId in supplierIds:
                raise Exception(f"shipmentBookingSearch.vendorClientId not found in detail supplierIds")
            U.logD(f"{prefix} shipmentDetail supplierId={supplierIds[0]}")

            expectedCount = cls.compareFields(
                shipmentBookingSearch,
                shipmentDetail,
                [
                    ("cwRef", "cwShipmentNumber"),
                    ("bookingNumber", "bookings.0.bookingNumber"),
                    ("clientId", "consigneeId"),
                    ("mot", "modeOfTransport"),
                    ("deliveryMode", "deliveryMode"),
                ],
                label="bookingSearchVsSummary",
                stats=stats,
                stats_key="bookingDetail",
            )
            statsTotalExpected["bookingDetail"] = expectedCount

            ## dump summary
            statsOut = {k: f"{v:2d}/{statsTotalExpected[k]:2d}" for k, v in stats.items()}
            U.logW(f"{prefix} ==== header stats: {statsOut}")

        except Exception as e:
            U.throwPrefix(prefix, e)

    @classmethod
    def checkShipmentDetail(cls, input: TBookingScenarioDirMeta | str):
        funcName = cls.checkShipmentDetail.__name__
        prefix = funcName
        try:
            pass

        except Exception as e:
            U.throwPrefix(prefix, e)

    @classmethod
    async def loadScenarioData(cls, shipmentNum: str):
        funcName = cls.loadScenarioData.__name__
        prefix = funcName
        try:
            U.logW(f"{prefix} >>>> Opening scenario shipment: {shipmentNum} ...")
            if not shipmentNum in BookingsMetaData:
                raise Exception(f"shipmentNum not found: {shipmentNum}")
            bookingMetaData = BookingsMetaData[shipmentNum]
            bookingMetaData["data"] = None

            scenarioId = bookingMetaData["scenarioId"]
            if not scenarioId in SCENARIO_BASE_DIRS:
                raise Exception(f"invalid scenarioId: {scenarioId}")
            scenarioBaseDir = SCENARIO_BASE_DIRS[scenarioId]

            ## load JSON file
            jsonBaseDir = f"{scenarioBaseDir}/{shipmentNum}/api"

            jsonFile = f"{jsonBaseDir}/currencies.res.json"
            U.logD(f"{prefix} reading {jsonFile} ...")
            currency = U.readFile(jsonFile, "json")

            jsonFile = f"{jsonBaseDir}/shipmentBookingSearch.res.json"
            U.logD(f"{prefix} reading {jsonFile} ...")
            shipmentBookingSearch = TypeHelper.toBaseModel(TShipmentBookingSearch, Path(jsonFile))

            jsonFile = f"{jsonBaseDir}/shipmentDetails.res.json"
            U.logD(f"{prefix} reading {jsonFile} ...")
            shipmentDetail = TypeHelper.toBaseModel(TShipmentDetail, Path(jsonFile))

            jsonFile = f"{jsonBaseDir}/shipmentSearch.res.json"
            U.logD(f"{prefix} reading {jsonFile} ...")
            shipmentSearch = TypeHelper.toBaseModel(TShipmentSearch, Path(jsonFile))

            jsonFile = f"{jsonBaseDir}/shipmentSummary.res.json"
            U.logD(f"{prefix} reading {jsonFile} ...")
            shipmentSummary = TypeHelper.toBaseModel(TShipmentSummary, Path(jsonFile))

            bookingMetaData["data"] = {
                "isValid": True,
                "shipmentSearch": shipmentSearch,
                "shipmentBookingSearch": shipmentBookingSearch,
                "shipmentSummary": shipmentSummary,
                "shipmentDetail": shipmentDetail,
            }

        except Exception as e:
            U.throwPrefix(prefix, e)

    @classmethod
    def compareFields(
        cls,
        obj1: BaseModel,
        obj2: BaseModel,
        fieldPairs: list[tuple[str, str] | tuple[str, str, Literal["noThrow"]]],
        label,
        stats,
        stats_key,
    ):
        """
        field_pairs: list of (path_in_a, path_in_b) strings, dotted for nested attrs.
        If both sides use the same path, you can pass just one string instead of a tuple.
        """
        funcName = cls.loadScenarioData.__name__
        prefix = funcName
        try:
            for fieldPair in fieldPairs:
                isThrow = True
                if len(fieldPair) == 2:
                    attrPath1, attrPath2 = fieldPair
                else:
                    attrPath1, attrPath2, extra = fieldPair
                    if extra == "noThrow":
                        isThrow = False

                val1 = cls.attrgetterExtra(obj1, attrPath1)
                val2 = cls.attrgetterExtra(obj2, attrPath2)

                if val1 != val2:
                    err = f"{label} mismatch[{attrPath1}:{attrPath2}]: {(val1, val2)}"
                    if isThrow:
                        raise Exception(err)
                    else:
                        U.logW(f"{prefix} {err}")
                else:
                    stats[stats_key] += 1

            return len(fieldPairs)

        except Exception as e:
            U.throwPrefix(prefix, e)

    @classmethod
    def attrgetterExtra(cls, obj, path):
        """
        Resolve a dotted path like 'results.1.bookingNum' against a mix of
        BaseModel objects, dicts, and lists.
        - Non-numeric segments -> getattr (falls back to __getitem__ for dicts)
        - Numeric segments -> index into a list/sequence
        """
        current = obj
        for segment in path.split("."):
            if segment.lstrip("-").isdigit():
                current = current[int(segment)]
            ## dict or TypedDict
            elif isinstance(current, dict):
                current = current[segment]
            ## BaseModel or other classes
            else:
                current = getattr(current, segment)
        return current
