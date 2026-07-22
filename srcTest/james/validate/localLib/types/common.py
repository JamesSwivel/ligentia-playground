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


class TPort(BaseModel):
    portCode: Annotated[str, Field(description="Port code")]
    countryCode: Annotated[str, Field(description="Country code of the port")]


class TCwParty(BaseModel):
    id: Annotated[int, Field(description="Unique identifier of the CargoWise party")]
    cargoWiseCode: Annotated[str, Field(description="CargoWise code of the party")]
    name: Annotated[str, Field(description="Name of the party")]
