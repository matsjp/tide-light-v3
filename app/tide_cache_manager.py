import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Tuple
import threading

from tide_models import WaterLevel, WaterLevelFlag


class TideCacheManager:
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        # Allow SQLite connection to be used across threads
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.lock = threading.RLock()  # Use RLock for reentrant locking
        self._create_tables()

    # -----------------------------
    # Table creation
    # -----------------------------
    def _create_tables(self):
        with self.lock:
            with self.conn:
                # Create tables if they don't exist
                self.conn.execute("""
                    CREATE TABLE IF NOT EXISTS waterlevels (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        time TEXT NOT NULL UNIQUE,
                        flag TEXT NOT NULL
                    );
                """)
                self.conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_time 
                    ON waterlevels(time);
                """)
                self.conn.execute("""
                    CREATE TABLE IF NOT EXISTS metadata (
                        key TEXT PRIMARY KEY,
                        value TEXT
                    );
                """)

    # -----------------------------
    # Metadata helpers
    # -----------------------------
    def _get_metadata(self, key: str) -> Optional[str]:
        with self.lock:
            row = self.conn.execute(
                "SELECT value FROM metadata WHERE key=?",
                (key,)
            ).fetchone()
            return row["value"] if row else None

    def _set_metadata(self, key: str, value: str):
        with self.lock:
            with self.conn:
                self.conn.execute(
                    "INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)",
                    (key, value)
                )

    # -----------------------------
    # Location metadata
    # -----------------------------
    def get_cached_location(self) -> Optional[Tuple[float, float]]:
        """
        Get the location of currently cached tide data.
        
        Returns:
            Tuple of (latitude, longitude) if cached, None if no location metadata exists.
        """
        lat = self._get_metadata("current_latitude")
        lon = self._get_metadata("current_longitude")
        if lat is None or lon is None:
            return None
        return (float(lat), float(lon))

    def set_cached_location(self, latitude: float, longitude: float):
        """
        Store the location of tide data being cached.
        
        Args:
            latitude: Latitude of the location
            longitude: Longitude of the location
        """
        self._set_metadata("current_latitude", str(latitude))
        self._set_metadata("current_longitude", str(longitude))

    # -----------------------------
    # Cache status
    # -----------------------------
    def is_empty(self) -> bool:
        """
        Check if the cache is empty.
        Cache is considered empty if:
        - No waterlevel data exists, OR
        - No location metadata exists
        
        Both data and metadata must exist for cache to be non-empty.
        
        Returns:
            True if cache is empty, False otherwise.
        """
        # Check if location metadata exists
        has_metadata = self.get_cached_location() is not None
        
        # Check if waterlevel data exists
        with self.lock:
            row = self.conn.execute(
                "SELECT 1 FROM waterlevels LIMIT 1"
            ).fetchone()
        has_data = row is not None
        
        # Empty if missing data OR missing metadata
        return not (has_data and has_metadata)

    # -----------------------------
    # Cache invalidation
    # -----------------------------
    def invalidate_all(self):
        """Clear all cached tide data AND location metadata."""
        with self.lock:
            with self.conn:
                self.conn.execute("DELETE FROM waterlevels")
                self.conn.execute(
                    "DELETE FROM metadata WHERE key IN ('current_latitude', 'current_longitude')"
                )

    # -----------------------------
    # Insert waterlevels
    # -----------------------------
    def insert_waterlevels(self, waterlevels: List[WaterLevel], latitude: float, longitude: float):
        """
        Insert waterlevels for the given location.
        Uses INSERT OR IGNORE to prevent duplicate time entries.
        Stores location in metadata to track which location's data is cached.
        
        Args:
            waterlevels: List of water level events to cache
            latitude: Latitude of the location (stored in metadata only)
            longitude: Longitude of the location (stored in metadata only)
        """
        with self.lock:
            with self.conn:
                # Insert waterlevel data (no lat/lon in rows)
                # INSERT OR IGNORE prevents duplicates based on UNIQUE time constraint
                self.conn.executemany(
                    "INSERT OR IGNORE INTO waterlevels (time, flag) VALUES (?, ?)",
                    [(wl.time.isoformat(), wl.flag.value) for wl in waterlevels]
                )
                # Store location metadata
                self.set_cached_location(latitude, longitude)

    # -----------------------------
    # Query waterlevels
    # -----------------------------
    def get_waterlevels_in_range(self, start: datetime, end: datetime) -> List[WaterLevel]:
        """
        Get waterlevels in time range.
        Assumes cache only contains data for one location.
        
        Args:
            start: Start datetime
            end: End datetime
            
        Returns:
            List of WaterLevel objects in the time range
        """
        with self.lock:
            rows = self.conn.execute(
                """
                SELECT time, flag FROM waterlevels
                WHERE time BETWEEN ? AND ?
                ORDER BY time ASC
                """,
                (start.isoformat(), end.isoformat())
            ).fetchall()

        return [
            WaterLevel(time=datetime.fromisoformat(row["time"]), flag=WaterLevelFlag(row["flag"]))
            for row in rows
        ]

    # -----------------------------
    # Check if data exists
    # -----------------------------
    def has_data_for_range(self, start: datetime, end: datetime) -> bool:
        """
        Check if data exists in range.
        Assumes cache only contains data for one location.
        
        Args:
            start: Start datetime
            end: End datetime
            
        Returns:
            True if data exists in range, False otherwise
        """
        with self.lock:
            row = self.conn.execute(
                "SELECT 1 FROM waterlevels WHERE time BETWEEN ? AND ? LIMIT 1",
                (start.isoformat(), end.isoformat())
            ).fetchone()
        return row is not None
