from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional

from tide_cache_manager import TideCacheManager
from tide_models import WaterLevel, WaterLevelFlag


@dataclass(frozen=True)
class TideState:
    """Represents current tide state at a specific time."""
    direction: str  # "rising" or "falling"
    progress: float  # 0.0 (low tide) to 1.0 (high tide)
    next_event: WaterLevel  # Next tide event (high or low)
    last_event: WaterLevel  # Previous tide event


class TideCalculator:
    """
    Stateless calculator for tide state from cached water level data.
    Queries cache assuming single active location (location-agnostic).
    Thread-safe for concurrent access.
    """
    
    def __init__(self, cache_manager: TideCacheManager):
        """
        Initialize tide calculator.
        
        Args:
            cache_manager: Cache manager for querying tide data
        """
        self._cache = cache_manager
    
    # -----------------------------
    # Public API
    # -----------------------------
    
    def get_current_state(self) -> Optional[TideState]:
        """
        Calculate current tide state from cached data.
        Uses whatever location data is currently in cache (single location assumption).
        
        Returns:
            TideState if data available, None if no data or error
        """
        now = datetime.now()
        
        # Query range: 12 hours before to 24 hours after
        # Ensures we capture previous and next tide events
        start = now - timedelta(hours=12)
        end = now + timedelta(hours=24)
        
        # Get waterlevels from cache (location-agnostic query)
        waterlevels = self._cache.get_waterlevels_in_range(start, end)
        
        if len(waterlevels) < 2:
            # Need at least 2 events (previous and next)
            return None
        
        # Find last event before now and next event after now
        last_event = None
        next_event = None
        
        for wl in waterlevels:
            if wl.time <= now:
                last_event = wl
            elif wl.time > now and next_event is None:
                next_event = wl
                break
        
        if last_event is None or next_event is None:
            # Couldn't find bounding events
            return None
        
        # Determine direction based on next event
        if next_event.flag == WaterLevelFlag.HIGH:
            direction = "rising"
        else:  # WaterLevelFlag.LOW
            direction = "falling"
        
        # Calculate progress
        elapsed = (now - last_event.time).total_seconds()
        total = (next_event.time - last_event.time).total_seconds()
        
        if total <= 0:
            # Prevent division by zero
            return None
        
        progress = elapsed / total
        
        # Clamp progress to [0.0, 1.0]
        progress = max(0.0, min(1.0, progress))
        
        return TideState(
            direction=direction,
            progress=progress,
            next_event=next_event,
            last_event=last_event
        )
