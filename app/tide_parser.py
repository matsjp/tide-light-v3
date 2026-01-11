from datetime import datetime
import xml.etree.ElementTree as ET
from typing import List

from tide_models import WaterLevel, WaterLevelFlag


def parse_waterlevels(xml_string: str) -> List[WaterLevel]:
    root = ET.fromstring(xml_string)
    waterlevels: List[WaterLevel] = []

    for wl in root.findall(".//waterlevel"):
        time = datetime.fromisoformat(wl.attrib["time"])
        # Remove timezone info to match datetime.now() (naive datetime)
        if time.tzinfo is not None:
            time = time.replace(tzinfo=None)
        flag_str = wl.attrib["flag"]

        try:
            flag = WaterLevelFlag(flag_str)
        except ValueError:
            # Unknown flag from API — ignore safely
            continue

        waterlevels.append(
            WaterLevel(
                time=time,
                flag=flag
            )
        )

    return waterlevels