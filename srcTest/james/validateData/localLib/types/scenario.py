from pydantic import BaseModel, Field
from typing import Literal, Annotated
from typing_extensions import TypedDict

from .shipmentSearch import TShipmentSearch
from .shipmentBookingSearch import TShipmentBookingSearch
from .shipmentSummary import TShipmentSummary
from .shipmentDetails import TShipmentDetail

TBookingScenarioId = Literal[
    "1",
    "2",
    "3",
    "4",
    "1.part2",
    "2.part2",
]


SCENARIO_BASE_DIRS: dict[
    TBookingScenarioId,
    str,
] = {
    "1": "data/Data Extraction/Scenario 1",
    "2": "data/Data Extraction/Scenario 2",
    "3": "data/Data Extraction/Scenario 3",
    "4": "data/Data Extraction/Scenario 4",
    "1.part2": "data/Data Extraction/Scenario 1 (PART 2)",
    "2.part2": "data/Data Extraction/Scenario 2 (PART 2)",
}


class TBookingScenarioDirMeta_data(TypedDict):
    isValid: bool
    shipmentSearch: TShipmentSearch
    shipmentBookingSearch: TShipmentBookingSearch
    shipmentSummary: TShipmentSummary
    shipmentDetail: TShipmentDetail


class TBookingScenarioDirMeta(TypedDict):
    env: Literal["UAT", "PROD"]
    scenarioId: TBookingScenarioId
    bookingNumber: str
    cwShipmentNumber: str
    data: TBookingScenarioDirMeta_data | None
