import unittest
from unittest.mock import MagicMock
from datetime import datetime, timedelta

from tide_calculator import TideCalculator, TideState
from tide_models import WaterLevel, WaterLevelFlag


class TestTideCalculator(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_cache = MagicMock()
        self.calculator = TideCalculator(self.mock_cache)
    
    def test_rising_tide_detection(self):
        """Test that rising tide is detected when next event is HIGH."""
        now = datetime.now()
        waterlevels = [
            WaterLevel(time=now - timedelta(hours=3), flag=WaterLevelFlag.LOW),
            WaterLevel(time=now + timedelta(hours=3), flag=WaterLevelFlag.HIGH)
        ]
        self.mock_cache.get_waterlevels_in_range.return_value = waterlevels
        
        state = self.calculator.get_current_state()
        
        self.assertIsNotNone(state)
        self.assertEqual(state.direction, "rising")
    
    def test_falling_tide_detection(self):
        """Test that falling tide is detected when next event is LOW."""
        now = datetime.now()
        waterlevels = [
            WaterLevel(time=now - timedelta(hours=2), flag=WaterLevelFlag.HIGH),
            WaterLevel(time=now + timedelta(hours=4), flag=WaterLevelFlag.LOW)
        ]
        self.mock_cache.get_waterlevels_in_range.return_value = waterlevels
        
        state = self.calculator.get_current_state()
        
        self.assertIsNotNone(state)
        self.assertEqual(state.direction, "falling")
    
    def test_progress_calculation_at_midpoint(self):
        """Test progress calculation at 50% between tides."""
        now = datetime.now()
        # Last event 3 hours ago, next event 3 hours from now
        waterlevels = [
            WaterLevel(time=now - timedelta(hours=3), flag=WaterLevelFlag.LOW),
            WaterLevel(time=now + timedelta(hours=3), flag=WaterLevelFlag.HIGH)
        ]
        self.mock_cache.get_waterlevels_in_range.return_value = waterlevels
        
        state = self.calculator.get_current_state()
        
        self.assertIsNotNone(state)
        # Progress should be 0.5 (midway)
        self.assertAlmostEqual(state.progress, 0.5, places=2)
    
    def test_progress_calculation_at_start(self):
        """Test progress calculation just after tide event."""
        now = datetime.now()
        # Last event just happened (1 minute ago), next event 6 hours from now
        waterlevels = [
            WaterLevel(time=now - timedelta(minutes=1), flag=WaterLevelFlag.LOW),
            WaterLevel(time=now + timedelta(hours=6), flag=WaterLevelFlag.HIGH)
        ]
        self.mock_cache.get_waterlevels_in_range.return_value = waterlevels
        
        state = self.calculator.get_current_state()
        
        self.assertIsNotNone(state)
        # Progress should be close to 0.0
        self.assertLess(state.progress, 0.01)
    
    def test_progress_calculation_at_end(self):
        """Test progress calculation just before next tide event."""
        now = datetime.now()
        # Last event 6 hours ago, next event in 1 minute
        waterlevels = [
            WaterLevel(time=now - timedelta(hours=6), flag=WaterLevelFlag.LOW),
            WaterLevel(time=now + timedelta(minutes=1), flag=WaterLevelFlag.HIGH)
        ]
        self.mock_cache.get_waterlevels_in_range.return_value = waterlevels
        
        state = self.calculator.get_current_state()
        
        self.assertIsNotNone(state)
        # Progress should be close to 1.0
        self.assertGreater(state.progress, 0.99)
    
    def test_no_data_returns_none(self):
        """Test that None is returned when no data available."""
        self.mock_cache.get_waterlevels_in_range_current_location.return_value = []
        
        state = self.calculator.get_current_state()
        
        self.assertIsNone(state)
    
    def test_single_event_returns_none(self):
        """Test that None is returned with only one event."""
        now = datetime.now()
        waterlevels = [
            WaterLevel(time=now + timedelta(hours=1), flag=WaterLevelFlag.HIGH)
        ]
        self.mock_cache.get_waterlevels_in_range.return_value = waterlevels
        
        state = self.calculator.get_current_state()
        
        self.assertIsNone(state)
    
    def test_missing_past_event_returns_none(self):
        """Test that None is returned when no past event found."""
        now = datetime.now()
        # Only future events
        waterlevels = [
            WaterLevel(time=now + timedelta(hours=1), flag=WaterLevelFlag.LOW),
            WaterLevel(time=now + timedelta(hours=7), flag=WaterLevelFlag.HIGH)
        ]
        self.mock_cache.get_waterlevels_in_range.return_value = waterlevels
        
        state = self.calculator.get_current_state()
        
        self.assertIsNone(state)
    
    def test_missing_future_event_returns_none(self):
        """Test that None is returned when no future event found."""
        now = datetime.now()
        # Only past events
        waterlevels = [
            WaterLevel(time=now - timedelta(hours=7), flag=WaterLevelFlag.HIGH),
            WaterLevel(time=now - timedelta(hours=1), flag=WaterLevelFlag.LOW)
        ]
        self.mock_cache.get_waterlevels_in_range.return_value = waterlevels
        
        state = self.calculator.get_current_state()
        
        self.assertIsNone(state)
    
    def test_progress_clamping_at_boundaries(self):
        """Test that progress is clamped to [0.0, 1.0]."""
        now = datetime.now()
        waterlevels = [
            WaterLevel(time=now - timedelta(hours=3), flag=WaterLevelFlag.LOW),
            WaterLevel(time=now + timedelta(hours=3), flag=WaterLevelFlag.HIGH)
        ]
        self.mock_cache.get_waterlevels_in_range.return_value = waterlevels
        
        state = self.calculator.get_current_state()
        
        self.assertIsNotNone(state)
        self.assertGreaterEqual(state.progress, 0.0)
        self.assertLessEqual(state.progress, 1.0)
    
    def test_events_returned_in_state(self):
        """Test that last and next events are returned correctly."""
        now = datetime.now()
        last_event = WaterLevel(time=now - timedelta(hours=2), flag=WaterLevelFlag.LOW)
        next_event = WaterLevel(time=now + timedelta(hours=4), flag=WaterLevelFlag.HIGH)
        waterlevels = [last_event, next_event]
        self.mock_cache.get_waterlevels_in_range.return_value = waterlevels
        
        state = self.calculator.get_current_state()
        
        self.assertIsNotNone(state)
        self.assertEqual(state.last_event, last_event)
        self.assertEqual(state.next_event, next_event)
    
    def test_multiple_past_events_uses_most_recent(self):
        """Test that most recent past event is used."""
        now = datetime.now()
        waterlevels = [
            WaterLevel(time=now - timedelta(hours=12), flag=WaterLevelFlag.HIGH),
            WaterLevel(time=now - timedelta(hours=6), flag=WaterLevelFlag.LOW),
            WaterLevel(time=now - timedelta(hours=1), flag=WaterLevelFlag.HIGH),
            WaterLevel(time=now + timedelta(hours=5), flag=WaterLevelFlag.LOW)
        ]
        self.mock_cache.get_waterlevels_in_range.return_value = waterlevels
        
        state = self.calculator.get_current_state()
        
        self.assertIsNotNone(state)
        # Should use the event 1 hour ago as last event
        self.assertEqual(state.last_event.time, now - timedelta(hours=1))
        self.assertEqual(state.last_event.flag, WaterLevelFlag.HIGH)


if __name__ == "__main__":
    unittest.main()
