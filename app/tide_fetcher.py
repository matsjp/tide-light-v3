
from datetime import datetime, timedelta
from typing import List

from kartverket_tide_api import TideApi

from tide_models import WaterLevel
from tide_parser import parse_waterlevels


class TideFetcher:
    def __init__(self):
        self._api = TideApi()

    def fetch_waterlevels(
        self,
        latitude: float,
        longitude: float,
        days_back: int = 1,
        days_forward: int = 3000
    ) -> List[WaterLevel]:
        """
        Fetch tide water levels for a location and time range.
        """

        time_from = self._format_time(datetime.now() - timedelta(days=days_back))
        time_to = self._format_time(datetime.now() + timedelta(days=days_forward))

        response = self._api.get_location_data(
            longitude,
            latitude,
            time_from,
            time_to,
            "TAB"
        )

        return parse_waterlevels(response)

    @staticmethod
    def _format_time(dt: datetime) -> str:
        return dt.strftime("%Y-%m-%dT%H:%M")