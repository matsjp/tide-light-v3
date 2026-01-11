import threading
import time
from datetime import datetime, timedelta

class TideUpdateScheduler:
    def __init__(self, cache_manager, tide_fetcher, config, prefetch_days=7, interval_days=7):
        self.cache = cache_manager
        self.fetcher = tide_fetcher
        self.config = config
        self.prefetch_days = prefetch_days
        self.interval_seconds = interval_days * 24 * 60 * 60
        self._stop_event = threading.Event()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)

        self.current_lat = config["tide"]["location"]["latitude"]
        self.current_lon = config["tide"]["location"]["longitude"]
        
        self._visualizer = None  # Will be set later

    def start(self):
        self.thread.start()

    def stop(self):
        self._stop_event.set()
        self.thread.join()

    def set_visualizer(self, visualizer):
        """Set visualizer to notify when data updates."""
        self._visualizer = visualizer

    def on_config_updated(self, new_config):
        new_lat = new_config["tide"]["location"]["latitude"]
        new_lon = new_config["tide"]["location"]["longitude"]

        if new_lat != self.current_lat or new_lon != self.current_lon:
            print("[Scheduler] Location change detected")
            self.cache.invalidate_all()  # Clears data AND location metadata

            self.current_lat = new_lat
            self.current_lon = new_lon

            self._run_once()  # Fetch new data and store new location in metadata

    def _run_once(self):
        start = datetime.now()
        end = start + timedelta(days=self.prefetch_days)
        lat = self.current_lat
        lon = self.current_lon

        # Check if cache is empty or missing data for the required range
        if self.cache.is_empty() or not self.cache.has_data_for_range(start, end):
            print("[Scheduler] Fetching tide data...")
            waterlevels = self.fetcher.fetch_waterlevels(
                latitude=lat, 
                longitude=lon, 
                days_back=1,  # Include 1 day back to ensure current time is covered
                days_forward=self.prefetch_days
            )
            self.cache.insert_waterlevels(waterlevels, lat, lon)
            print(f"[Scheduler] Inserted {len(waterlevels)} waterlevel events.")
            
            # Notify visualizer of new data
            if self._visualizer:
                self._visualizer.on_tide_data_updated()
        else:
            print("[Scheduler] Cache up-to-date.")

    def _run_loop(self):
        while not self._stop_event.is_set():
            self._run_once()
            for _ in range(int(self.interval_seconds)):
                if self._stop_event.is_set():
                    break
                time.sleep(1)
