import unittest
from unittest.mock import MagicMock
from datetime import datetime, timedelta

from tide_models import WaterLevel, WaterLevelFlag
from tide_update_scheduler import TideUpdateScheduler


class TestTideUpdateScheduler(unittest.TestCase):

    def setUp(self):
        # Default config
        self.config = {
            "tide": {
                "location": {"latitude": 59.9, "longitude": 10.7}
            }
        }

        # Fake waterlevel events
        self.fake_waterlevels = [
            WaterLevel(time=datetime.now() + timedelta(hours=1), flag=WaterLevelFlag.HIGH),
            WaterLevel(time=datetime.now() + timedelta(hours=7), flag=WaterLevelFlag.LOW)
        ]

        # Mock tide fetcher always returns fake waterlevels
        self.mock_fetcher = MagicMock()
        self.mock_fetcher.fetch_waterlevels.return_value = self.fake_waterlevels

        # Mock cache manager
        self.mock_cache = MagicMock()

    def test_run_once_fetches_when_cache_missing(self):
        self.mock_cache.is_empty.return_value = False  # Not empty
        self.mock_cache.has_data_for_range.return_value = False  # But missing range

        scheduler = TideUpdateScheduler(self.mock_cache, self.mock_fetcher, self.config)
        scheduler._run_once()

        self.mock_fetcher.fetch_waterlevels.assert_called_once()
        self.mock_cache.insert_waterlevels.assert_called_once()

    def test_run_once_skips_if_cache_present(self):
        self.mock_cache.is_empty.return_value = False  # Not empty
        self.mock_cache.has_data_for_range.return_value = True  # Has required range

        scheduler = TideUpdateScheduler(self.mock_cache, self.mock_fetcher, self.config)
        scheduler._run_once()

        self.mock_fetcher.fetch_waterlevels.assert_not_called()
        self.mock_cache.insert_waterlevels.assert_not_called()

    def test_run_once_fetches_when_cache_empty(self):
        """Test that empty cache triggers fetch even if has_data_for_range would return True."""
        self.mock_cache.is_empty.return_value = True  # Empty cache
        self.mock_cache.has_data_for_range.return_value = True  # Shouldn't be checked due to short-circuit

        scheduler = TideUpdateScheduler(self.mock_cache, self.mock_fetcher, self.config)
        scheduler._run_once()

        # Should fetch because cache is empty
        self.mock_fetcher.fetch_waterlevels.assert_called_once()
        self.mock_cache.insert_waterlevels.assert_called_once()

    def test_on_config_updated_with_location_change(self):
        scheduler = TideUpdateScheduler(self.mock_cache, self.mock_fetcher, self.config)

        # Mock cache state for fetch
        self.mock_cache.is_empty.return_value = False
        self.mock_cache.has_data_for_range.return_value = False  # Missing range, triggers fetch

        new_config = {
            "tide": {
                "location": {"latitude": 60.0, "longitude": 11.0}
            }
        }

        scheduler.on_config_updated(new_config)

        # Verify cache invalidation (no more update_location_metadata)
        self.mock_cache.invalidate_all.assert_called_once()

        # Verify fetch and insert called
        self.mock_fetcher.fetch_waterlevels.assert_called_once_with(
            latitude=60.0, 
            longitude=11.0,
            days_back=1,
            days_forward=7
        )
        self.mock_cache.insert_waterlevels.assert_called_once_with(self.fake_waterlevels, 60.0, 11.0)

        # Scheduler location updated
        self.assertEqual(scheduler.current_lat, 60.0)
        self.assertEqual(scheduler.current_lon, 11.0)

    def test_on_config_updated_same_location_does_nothing(self):
        scheduler = TideUpdateScheduler(self.mock_cache, self.mock_fetcher, self.config)

        same_config = {
            "tide": {
                "location": {"latitude": 59.9, "longitude": 10.7}
            }
        }

        scheduler.on_config_updated(same_config)

        # No calls should be made (removed update_location_metadata assertion)
        self.mock_cache.invalidate_all.assert_not_called()
        self.mock_fetcher.fetch_waterlevels.assert_not_called()
        self.mock_cache.insert_waterlevels.assert_not_called()


if __name__ == "__main__":
    unittest.main()
