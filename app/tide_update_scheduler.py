import threading
import time
import logging
from datetime import datetime, timedelta

class TideUpdateScheduler:
    def __init__(self, cache_manager, tide_fetcher, config, prefetch_days=7, interval_days=7):
        self.cache = cache_manager
        self.fetcher = tide_fetcher
        self.config = config
        self.prefetch_days = prefetch_days
        self.interval_seconds = interval_days * 24 * 60 * 60
        self._stop_event = threading.Event()
        self._wake_event = threading.Event()    # Allows external callers to interrupt sleep
        self._run_once_lock = threading.Lock()  # Prevent concurrent _run_once() calls
        self.thread = threading.Thread(target=self._run_loop, daemon=True)

        self.current_lat = config["tide"]["location"]["latitude"]
        self.current_lon = config["tide"]["location"]["longitude"]
        
        self._visualizer = None  # Will be set later
        self._fetch_failed = False  # Track fetch failure state

    def start(self):
        self.thread.start()

    def stop(self):
        self._stop_event.set()
        self._wake_event.set()  # Unblock any ongoing wait so the loop can exit
        self.thread.join()

    def set_visualizer(self, visualizer):
        """Set visualizer to notify when data updates."""
        self._visualizer = visualizer

    def run_once(self):
        """Trigger a single update cycle (public API)."""
        self._run_once()

    def on_config_updated(self, new_config):
        new_lat = new_config["tide"]["location"]["latitude"]
        new_lon = new_config["tide"]["location"]["longitude"]

        if new_lat != self.current_lat or new_lon != self.current_lon:
            logging.info("[Scheduler] Location change detected")
            self.cache.invalidate_all()  # Clears data AND location metadata

            self.current_lat = new_lat
            self.current_lon = new_lon

            self._run_once()  # Fetch new data and store new location in metadata
            self._wake_event.set()  # Interrupt any ongoing sleep so retry interval is recalculated

    def _run_once(self):
        """
        Run a single update cycle. Thread-safe; prevents concurrent API calls.
        """
        with self._run_once_lock:
            start = datetime.now()
            end = start + timedelta(days=self.prefetch_days)
            lat = self.current_lat
            lon = self.current_lon

            # Check if cache is empty or missing data for the required range
            if self.cache.is_empty() or not self.cache.has_data_for_range(start, end):
                logging.info("[Scheduler] Fetching tide data...")
                waterlevels = self.fetcher.fetch_waterlevels(
                    latitude=lat, 
                    longitude=lon, 
                    days_back=1,  # Include 1 day back to ensure current time is covered
                    days_forward=self.prefetch_days
                )
                
                if waterlevels:  # Only insert if we got data
                    self.cache.insert_waterlevels(waterlevels, lat, lon)
                    logging.info(f"[Scheduler] Inserted {len(waterlevels)} waterlevel events.")
                    self._fetch_failed = False
                    
                    # Notify visualizer of new data
                    if self._visualizer:
                        self._visualizer.on_tide_data_updated()
                else:
                    # Empty list returned (API failed or no data)
                    self._fetch_failed = True
                    logging.debug("[Scheduler] Tide data fetch returned no data")
            else:
                logging.info("[Scheduler] Cache up-to-date.")
                self._fetch_failed = False

    def _run_loop(self):
        while not self._stop_event.is_set():
            self._run_once()
            
            # Determine wait time based on fetch state
            if self._fetch_failed:
                # Retry every 60 seconds after a fetch failure (prevents cache expiration)
                wait_time = 60
            else:
                # Normal 7-day interval
                wait_time = int(self.interval_seconds)
            
            # Sleep until next cycle, but allow early wake-up via _wake_event
            # (e.g. when a location change fails and we need to reschedule to 60s retries)
            self._wake_event.wait(timeout=wait_time)
            self._wake_event.clear()
