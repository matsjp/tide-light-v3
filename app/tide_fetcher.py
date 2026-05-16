import logging
import time
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

        logging.info(f"[TideFetcher] Fetching tide data for ({latitude}, {longitude}) from {time_from} to {time_to}")
        
        start_time = time.time()
        response = self._api.get_location_data(
            longitude,
            latitude,
            time_from,
            time_to,
            "TAB"
        )
        
        waterlevels = parse_waterlevels(response)
        duration = time.time() - start_time
        
        logging.info(f"[TideFetcher] Received {len(waterlevels)} waterlevel events in {duration:.2f}s")
        
        return waterlevels

    @staticmethod
    def _format_time(dt: datetime) -> str:
        return dt.strftime("%Y-%m-%dT%H:%M")