import unittest
from unittest.mock import MagicMock, patch
import threading
import time

from ldr_controller import LdrController


class TestLdrController(unittest.TestCase):
    """Test suite for LDR (Light Dependent Resistor) controller."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            "ldr": {
                "enabled": False,
                "pin": 11
            },
            "led_strip": {
                "brightness": 128
            }
        }
        self.brightness_callback = MagicMock()
        
    def test_initialization_disabled(self):
        """Test that LDR initializes correctly when disabled."""
        controller = LdrController(self.config, self.brightness_callback)
        
        self.assertFalse(controller._enabled)
        self.assertEqual(controller._pin, 11)
        self.assertEqual(controller._configured_brightness, 128)
        self.assertIsNone(controller._thread)
        
    def test_initialization_enabled_without_hardware(self):
        """Test that LDR initializes but doesn't start without hardware."""
        config_enabled = {
            "ldr": {
                "enabled": True,
                "pin": 11
            },
            "led_strip": {
                "brightness": 128
            }
        }
        controller = LdrController(config_enabled, self.brightness_callback)
        
        # LDR_AVAILABLE will be False since we don't have RPi.GPIO
        # Controller should be created but not functional
        self.assertTrue(controller._enabled)
        
    def test_start_when_disabled(self):
        """Test that start() does nothing when LDR is disabled."""
        controller = LdrController(self.config, self.brightness_callback)
        controller.start()
        
        self.assertIsNone(controller._thread)
        
    def test_stop_when_not_running(self):
        """Test that stop() handles case where thread is not running."""
        controller = LdrController(self.config, self.brightness_callback)
        
        # Should not raise an exception
        controller.stop()
        
    def test_get_status_disabled(self):
        """Test status retrieval when disabled."""
        controller = LdrController(self.config, self.brightness_callback)
        status = controller.get_status()
        
        self.assertIsInstance(status, dict)
        self.assertFalse(status["enabled"])
        self.assertEqual(status["current_brightness"], 128)
        self.assertEqual(status["configured_brightness"], 128)
        self.assertFalse(status["thread_alive"])
        
    def test_config_update_enable(self):
        """Test enabling LDR through config update."""
        controller = LdrController(self.config, self.brightness_callback)
        
        # Initially disabled
        self.assertFalse(controller._enabled)
        
        # Update config to enable
        new_config = {
            "ldr": {
                "enabled": True,
                "pin": 11
            },
            "led_strip": {
                "brightness": 128
            }
        }
        controller.on_config_updated(new_config)
        
        # Should be enabled now (though won't start without hardware)
        self.assertTrue(controller._enabled)
        
    def test_config_update_disable_restores_brightness(self):
        """Test disabling LDR restores configured brightness."""
        config_enabled = {
            "ldr": {
                "enabled": True,
                "pin": 11
            },
            "led_strip": {
                "brightness": 200
            }
        }
        controller = LdrController(config_enabled, self.brightness_callback)
        
        # Update config to disable
        new_config = {
            "ldr": {
                "enabled": False,
                "pin": 11
            },
            "led_strip": {
                "brightness": 200
            }
        }
        controller.on_config_updated(new_config)
        
        # Should be disabled and brightness callback called with configured value
        self.assertFalse(controller._enabled)
        self.brightness_callback.assert_called_with(200)
        
    def test_config_update_brightness_while_enabled(self):
        """Test that configured brightness is updated even when LDR is active."""
        config_enabled = {
            "ldr": {
                "enabled": True,
                "pin": 11
            },
            "led_strip": {
                "brightness": 100
            }
        }
        controller = LdrController(config_enabled, self.brightness_callback)
        
        # Update brightness in config
        new_config = {
            "ldr": {
                "enabled": True,
                "pin": 11
            },
            "led_strip": {
                "brightness": 150
            }
        }
        controller.on_config_updated(new_config)
        
        # Configured brightness should be updated
        self.assertEqual(controller._configured_brightness, 150)
        # But LDR should still be controlling actual brightness (no callback)
        
    def test_scale_and_invert_dark(self):
        """Test brightness mapping for dark environment (high count)."""
        controller = LdrController(self.config, self.brightness_callback)
        
        # Dark room (high RC count) should give high brightness
        # Max count (250000) → scaled to 255 → inverted to 5
        # So we want a high count to produce high brightness
        brightness = controller._scale_and_invert(250000)
        # High count = dark = bright LEDs
        self.assertGreater(brightness, 200)
        
    def test_scale_and_invert_bright(self):
        """Test brightness mapping for bright environment (low count)."""
        controller = LdrController(self.config, self.brightness_callback)
        
        # Bright room (low RC count) should give low brightness
        brightness = controller._scale_and_invert(1)
        # Low count = bright = dim LEDs
        self.assertLess(brightness, 50)
        
    def test_scale_and_invert_midpoint(self):
        """Test brightness mapping for medium light level."""
        controller = LdrController(self.config, self.brightness_callback)
        
        # Midpoint count should give mid-range brightness
        mid_count = 125000
        brightness = controller._scale_and_invert(mid_count)
        
        # Should be approximately in the middle of the range (5-255)
        self.assertGreater(brightness, 100)
        self.assertLess(brightness, 160)
        
    def test_brightness_clamping_upper(self):
        """Test that brightness is clamped to max value."""
        controller = LdrController(self.config, self.brightness_callback)
        
        # Beyond max count should still clamp properly
        brightness = controller._scale_and_invert(500000)
        self.assertLessEqual(brightness, 255)
        self.assertGreaterEqual(brightness, 5)
        
    def test_brightness_clamping_lower(self):
        """Test that brightness is clamped to min value."""
        controller = LdrController(self.config, self.brightness_callback)
        
        # Negative/zero count should still clamp properly
        brightness = controller._scale_and_invert(0)
        self.assertLessEqual(brightness, 255)
        self.assertGreaterEqual(brightness, 5)


if __name__ == '__main__':
    unittest.main()
