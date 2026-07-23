from pydantic import BaseModel, Field
from pathlib import Path
from typing import Literal, Annotated, Any, TypeVar
from typing_extensions import TypedDict
import swivel.common as U

from localLib.types import *

BookingsMetaData: dict[str, TBookingScenarioDirMeta] = {
    "S01863302": {
        "env": "UAT",
        "scenarioId": "1",
        "bookingNumber": "SE0612240084",
        "cwShipmentNumber": "S01863302",
        "data": None,
    },
    "S01889327": {
        "env": "UAT",
        "scenarioId": "1",
        "bookingNumber": "SE1212240411",
        "cwShipmentNumber": "S01889327",
        "data": None,
    },
}
