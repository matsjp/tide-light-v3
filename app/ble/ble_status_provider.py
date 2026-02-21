"""
BLE status provider for Tide Light.

Provides current system status for the BLE status characteristic.
Queries tide state, cache information, and system metrics.
"""

import json
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from tide_calculator import TideCalculator
from tide_cache_manager import TideCacheManager


class BLEStatusProvider:
    """
    Provides status information for BLE clients.
    Queries tide state and system information.
    """
    
    def __init__(self, tide_calculator: TideCalculator, tide_cache: TideCacheManager):
        """
        Initialize status provider.
        
        Args:
            tide_calculator: TideCalculator for current tide state
            tide_cache: TideCacheManager for cache information
        """
        self._calculator = tide_calculator
        self._cache = tide_cache
        self._start_time = time.time()
    
    def get_status_json(self) -> str:
        """
        Get current status as JSON string.
        
        Returns:
            JSON string with tide state, cache info, and system metrics
        """
        logging.info("[BLE Status Provider] Building status JSON")
        try:
            status = self._build_status_dict()
            # Use compact JSON (no indent) to minimize BLE packet size
            json_str = json.dumps(status)
            logging.info(f"[BLE Status Provider] Status JSON size: {len(json_str)} bytes")
            logging.debug(f"[BLE Status Provider] Status JSON: {json_str}")
            return json_str
        except Exception as e:
            logging.exception(f"[BLE Status Provider] Error building status: {e}")
            raise
    
    def _build_status_dict(self) -> Dict[str, Any]:
        """
        Build status dictionary with all information.
        
        Returns:
            Dictionary with tide, cache, and system sections
        """
        status = {
            "tide": self._get_tide_status(),
            "cache": self._get_cache_status(),
            "system": self._get_system_status()
        }
        return status
    
    def _get_tide_status(self) -> Dict[str, Any]:
        """
        Get current tide state information.
        
        Returns:
            Dictionary with direction, progress, and tide events
        """
        tide_state = self._calculator.get_current_state()
        
        if tide_state is None:
            return {
                "available": False,
                "reason": "No tide data available"
            }
        
        return {
            "available": True,
            "direction": tide_state.direction,
            "progress": round(tide_state.progress, 3),
            "next_event": {
                "time": tide_state.next_event.time.isoformat(),
                "flag": tide_state.next_event.flag.value
            },
            "last_event": {
                "time": tide_state.last_event.time.isoformat(),
                "flag": tide_state.last_event.flag.value
            }
        }
    
    def _get_cache_status(self) -> Dict[str, Any]:
        """
        Get cache status information.
        
        Returns:
            Dictionary with cached location and data availability
        """
        cached_location = self._cache.get_cached_location()
        is_empty = self._cache.is_empty()
        
        if cached_location is None:
            return {
                "has_data": False,
                "latitude": None,
                "longitude": None
            }
        
        lat, lon = cached_location
        return {
            "has_data": not is_empty,
            "latitude": lat,
            "longitude": lon
        }
    
    def _get_system_status(self) -> Dict[str, Any]:
        """
        Get system status information.
        
        Returns:
            Dictionary with system metrics
        """
        uptime = int(time.time() - self._start_time)
        
        return {
            "uptime_seconds": uptime,
            "last_update": datetime.now().isoformat()
        }
