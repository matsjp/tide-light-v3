"""
BLE configuration handler for Tide Light.

Validates BLE write requests and applies configuration updates.
Handles partial config updates (single field changes) and full config writes.
Returns appropriate error codes for invalid inputs.
"""

import json
import threading
from typing import Tuple, Optional, Dict, Any
from copy import deepcopy

from config_manager import ConfigManager
from ble.ble_characteristics import (
    BLE_ERROR_NONE,
    BLE_ERROR_INVALID_FORMAT,
    BLE_ERROR_OUT_OF_RANGE,
    BLE_ERROR_INVALID_VALUE,
    BLE_ERROR_INTERNAL,
    LAT_MIN, LAT_MAX,
    LON_MIN, LON_MAX,
    BRIGHTNESS_MIN, BRIGHTNESS_MAX,
    LED_COUNT_MIN, LED_COUNT_MAX,
    WAVE_SPEED_MIN, WAVE_SPEED_MAX,
    VALID_PATTERNS
)


class BLEConfigHandler:
    """
    Handles validation and application of BLE configuration updates.
    Thread-safe for concurrent BLE and main thread access.
    """
    
    def __init__(self, config_manager: ConfigManager):
        """
        Initialize config handler.
        
        Args:
            config_manager: ConfigManager instance for applying updates
        """
        self._config_manager = config_manager
        self._lock = threading.Lock()
        self._last_error = BLE_ERROR_NONE
    
    # -----------------------------
    # Error Code Management
    # -----------------------------
    
    def get_last_error(self) -> int:
        """Get the last error code."""
        with self._lock:
            return self._last_error
    
    def _set_error(self, error_code: int) -> int:
        """Set error code and return it."""
        with self._lock:
            self._last_error = error_code
        return error_code
    
    def clear_error(self) -> None:
        """Clear error code (set to NONE)."""
        with self._lock:
            self._last_error = BLE_ERROR_NONE
    
    # -----------------------------
    # Validation Functions
    # -----------------------------
    
    def validate_location(self, lat_lon_str: str) -> Tuple[bool, int, Optional[Tuple[float, float]]]:
        """
        Validate location string format and ranges.
        
        Args:
            lat_lon_str: String in format "latitude,longitude"
            
        Returns:
            Tuple of (is_valid, error_code, parsed_tuple)
            If valid: (True, 0, (lat, lon))
            If invalid: (False, error_code, None)
        """
        try:
            parts = lat_lon_str.strip().split(',')
            if len(parts) != 2:
                return (False, BLE_ERROR_INVALID_FORMAT, None)
            
            lat = float(parts[0].strip())
            lon = float(parts[1].strip())
            
            if not (LAT_MIN <= lat <= LAT_MAX):
                return (False, BLE_ERROR_OUT_OF_RANGE, None)
            
            if not (LON_MIN <= lon <= LON_MAX):
                return (False, BLE_ERROR_OUT_OF_RANGE, None)
            
            return (True, BLE_ERROR_NONE, (lat, lon))
            
        except (ValueError, AttributeError):
            return (False, BLE_ERROR_INVALID_FORMAT, None)
    
    def validate_brightness(self, value: int) -> Tuple[bool, int]:
        """
        Validate brightness value.
        
        Args:
            value: Brightness (0-255)
            
        Returns:
            (is_valid, error_code)
        """
        if not isinstance(value, int):
            return (False, BLE_ERROR_INVALID_FORMAT)
        
        if not (BRIGHTNESS_MIN <= value <= BRIGHTNESS_MAX):
            return (False, BLE_ERROR_OUT_OF_RANGE)
        
        return (True, BLE_ERROR_NONE)
    
    def validate_pattern(self, pattern: str) -> Tuple[bool, int]:
        """
        Validate pattern value.
        
        Args:
            pattern: Pattern name ("none" or "wave")
            
        Returns:
            (is_valid, error_code)
        """
        if not isinstance(pattern, str):
            return (False, BLE_ERROR_INVALID_FORMAT)
        
        if pattern.lower() not in VALID_PATTERNS:
            return (False, BLE_ERROR_INVALID_VALUE)
        
        return (True, BLE_ERROR_NONE)
    
    def validate_wave_speed(self, speed_str: str) -> Tuple[bool, int, Optional[float]]:
        """
        Validate wave speed value.
        
        Args:
            speed_str: String representation of float
            
        Returns:
            Tuple of (is_valid, error_code, parsed_float)
        """
        try:
            speed = float(speed_str.strip())
            
            if not (WAVE_SPEED_MIN <= speed <= WAVE_SPEED_MAX):
                return (False, BLE_ERROR_OUT_OF_RANGE, None)
            
            return (True, BLE_ERROR_NONE, speed)
            
        except (ValueError, AttributeError):
            return (False, BLE_ERROR_INVALID_FORMAT, None)
    
    def validate_led_count(self, value: int) -> Tuple[bool, int]:
        """
        Validate LED count value.
        
        Args:
            value: Number of LEDs (3-255)
            
        Returns:
            (is_valid, error_code)
        """
        if not isinstance(value, int):
            return (False, BLE_ERROR_INVALID_FORMAT)
        
        if not (LED_COUNT_MIN <= value <= LED_COUNT_MAX):
            return (False, BLE_ERROR_OUT_OF_RANGE)
        
        return (True, BLE_ERROR_NONE)
    
    def validate_led_invert(self, value: int) -> Tuple[bool, int, Optional[bool]]:
        """
        Validate LED invert value.
        
        Args:
            value: 0 (false) or 1 (true)
            
        Returns:
            Tuple of (is_valid, error_code, parsed_bool)
        """
        if not isinstance(value, int):
            return (False, BLE_ERROR_INVALID_FORMAT, None)
        
        if value not in [0, 1]:
            return (False, BLE_ERROR_INVALID_VALUE, None)
        
        return (True, BLE_ERROR_NONE, bool(value))
    
    def validate_full_config(self, json_str: str) -> Tuple[bool, int, Optional[Dict[str, Any]]]:
        """
        Validate full config JSON.
        
        Args:
            json_str: JSON string of full configuration
            
        Returns:
            Tuple of (is_valid, error_code, parsed_config)
        """
        try:
            config = json.loads(json_str)
            
            if not isinstance(config, dict):
                return (False, BLE_ERROR_INVALID_FORMAT, None)
            
            # Basic structure validation
            required_keys = ["config_version", "bluetooth", "tide", "led_strip", "color"]
            for key in required_keys:
                if key not in config:
                    return (False, BLE_ERROR_INVALID_FORMAT, None)
            
            return (True, BLE_ERROR_NONE, config)
            
        except (json.JSONDecodeError, TypeError):
            return (False, BLE_ERROR_INVALID_FORMAT, None)
    
    # -----------------------------
    # Configuration Update Functions
    # -----------------------------
    
    def update_location(self, lat_lon_str: str) -> int:
        """
        Update tide location.
        
        Args:
            lat_lon_str: String in format "latitude,longitude"
            
        Returns:
            Error code (0 = success)
        """
        is_valid, error_code, parsed = self.validate_location(lat_lon_str)
        
        if not is_valid:
            return self._set_error(error_code)
        
        lat, lon = parsed
        
        try:
            config = self._config_manager.get_config()
            config["tide"]["location"]["latitude"] = lat
            config["tide"]["location"]["longitude"] = lon
            self._config_manager.update_config(config)
            return self._set_error(BLE_ERROR_NONE)
        except Exception as e:
            print(f"[BLEConfigHandler] Error updating location: {e}")
            return self._set_error(BLE_ERROR_INTERNAL)
    
    def update_brightness(self, value: int) -> int:
        """
        Update LED brightness.
        
        Args:
            value: Brightness (0-255)
            
        Returns:
            Error code (0 = success)
        """
        is_valid, error_code = self.validate_brightness(value)
        
        if not is_valid:
            return self._set_error(error_code)
        
        try:
            config = self._config_manager.get_config()
            config["led_strip"]["brightness"] = value
            self._config_manager.update_config(config)
            return self._set_error(BLE_ERROR_NONE)
        except Exception as e:
            print(f"[BLEConfigHandler] Error updating brightness: {e}")
            return self._set_error(BLE_ERROR_INTERNAL)
    
    def update_pattern(self, pattern: str) -> int:
        """
        Update LED pattern.
        
        Args:
            pattern: Pattern name ("none" or "wave")
            
        Returns:
            Error code (0 = success)
        """
        is_valid, error_code = self.validate_pattern(pattern)
        
        if not is_valid:
            return self._set_error(error_code)
        
        try:
            config = self._config_manager.get_config()
            config["color"]["pattern"] = pattern.lower()
            self._config_manager.update_config(config)
            return self._set_error(BLE_ERROR_NONE)
        except Exception as e:
            print(f"[BLEConfigHandler] Error updating pattern: {e}")
            return self._set_error(BLE_ERROR_INTERNAL)
    
    def update_wave_speed(self, speed_str: str) -> int:
        """
        Update wave animation speed.
        
        Args:
            speed_str: String representation of float
            
        Returns:
            Error code (0 = success)
        """
        is_valid, error_code, parsed = self.validate_wave_speed(speed_str)
        
        if not is_valid:
            return self._set_error(error_code)
        
        try:
            config = self._config_manager.get_config()
            config["color"]["wave_speed"] = parsed
            self._config_manager.update_config(config)
            return self._set_error(BLE_ERROR_NONE)
        except Exception as e:
            print(f"[BLEConfigHandler] Error updating wave speed: {e}")
            return self._set_error(BLE_ERROR_INTERNAL)
    
    def update_led_count(self, value: int) -> int:
        """
        Update LED count.
        
        Args:
            value: Number of LEDs (3-255)
            
        Returns:
            Error code (0 = success)
        """
        is_valid, error_code = self.validate_led_count(value)
        
        if not is_valid:
            return self._set_error(error_code)
        
        try:
            config = self._config_manager.get_config()
            config["led_strip"]["count"] = value
            self._config_manager.update_config(config)
            return self._set_error(BLE_ERROR_NONE)
        except Exception as e:
            print(f"[BLEConfigHandler] Error updating LED count: {e}")
            return self._set_error(BLE_ERROR_INTERNAL)
    
    def update_led_invert(self, value: int) -> int:
        """
        Update LED invert flag.
        
        Args:
            value: 0 (false) or 1 (true)
            
        Returns:
            Error code (0 = success)
        """
        is_valid, error_code, parsed = self.validate_led_invert(value)
        
        if not is_valid:
            return self._set_error(error_code)
        
        try:
            config = self._config_manager.get_config()
            config["led_strip"]["invert"] = parsed
            self._config_manager.update_config(config)
            return self._set_error(BLE_ERROR_NONE)
        except Exception as e:
            print(f"[BLEConfigHandler] Error updating LED invert: {e}")
            return self._set_error(BLE_ERROR_INTERNAL)
    
    def update_full_config(self, json_str: str) -> int:
        """
        Update full configuration.
        
        Args:
            json_str: JSON string of full configuration
            
        Returns:
            Error code (0 = success)
        """
        is_valid, error_code, parsed = self.validate_full_config(json_str)
        
        if not is_valid:
            return self._set_error(error_code)
        
        try:
            self._config_manager.update_config(parsed)
            return self._set_error(BLE_ERROR_NONE)
        except Exception as e:
            print(f"[BLEConfigHandler] Error updating full config: {e}")
            return self._set_error(BLE_ERROR_INTERNAL)
    
    # -----------------------------
    # Read Functions
    # -----------------------------
    
    def get_location(self) -> str:
        """
        Get current location as string.
        
        Returns:
            String in format "latitude,longitude"
        """
        config = self._config_manager.get_config()
        lat = config["tide"]["location"]["latitude"]
        lon = config["tide"]["location"]["longitude"]
        return f"{lat},{lon}"
    
    def get_brightness(self) -> int:
        """Get current brightness value."""
        config = self._config_manager.get_config()
        return config["led_strip"]["brightness"]
    
    def get_pattern(self) -> str:
        """Get current pattern."""
        config = self._config_manager.get_config()
        return config["color"]["pattern"]
    
    def get_wave_speed(self) -> str:
        """Get current wave speed as string."""
        config = self._config_manager.get_config()
        return str(config["color"]["wave_speed"])
    
    def get_led_count(self) -> int:
        """Get current LED count."""
        config = self._config_manager.get_config()
        return config["led_strip"]["count"]
    
    def get_led_invert(self) -> int:
        """Get current LED invert as int (0 or 1)."""
        config = self._config_manager.get_config()
        return 1 if config["led_strip"]["invert"] else 0
    
    def get_full_config(self) -> str:
        """Get full configuration as JSON string."""
        config = self._config_manager.get_config()
        return json.dumps(config, indent=2)
