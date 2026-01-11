from enum import Enum
from dataclasses import dataclass
from datetime import datetime


class WaterLevelFlag(Enum):
    HIGH = "high"
    LOW = "low"


@dataclass(frozen=True)
class WaterLevel:
    time: datetime
    flag: WaterLevelFlag