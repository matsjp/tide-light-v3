"""
BLE Server for Tide Light - Real Hardware Implementation.

Uses bluezero library to create a GATT server on Raspberry Pi.
Exposes configuration characteristics for reading and writing.
Runs GLib main loop in separate thread.

Only imported when bluetooth.use_fake_library = false.
"""

import threading
import time
from typing import Any

# Lazy imports - only import bluezero when this module is loaded
from bluezero import peripheral
from bluezero import async_tools

from config_manager import ConfigManager
from ble.ble_config_handler import BLEConfigHandler
from ble.ble_status_provider import BLEStatusProvider
from ble.ble_characteristics import (
    SERVICE_UUID,
    SERVICE_NAME,
    CHAR_LOCATION_UUID,
    CHAR_BRIGHTNESS_UUID,
    CHAR_PATTERN_UUID,
    CHAR_WAVE_SPEED_UUID,
    CHAR_LED_COUNT_UUID,
    CHAR_LED_INVERT_UUID,
    CHAR_FULL_CONFIG_UUID,
    CHAR_STATUS_UUID,
    CHAR_ERROR_UUID
)


class BLEServer:
    """
    Real BLE GATT server using bluezero.
    Exposes Tide Light configuration as BLE characteristics.
    """
    
    def __init__(
        self,
        config_manager: ConfigManager,
        config_handler: BLEConfigHandler,
        status_provider: BLEStatusProvider
    ):
        """
        Initialize BLE server.
        
        Args:
            config_manager: ConfigManager instance
            config_handler: Handler for config validation and updates
            status_provider: Provider for status information
        """
        self._config_manager = config_manager
        self._handler = config_handler
        self._status = status_provider
        self._peripheral = None
        self._thread = None
        self._stop_event = threading.Event()
        self._status_notify_thread = None
        
        print("[BLE Server] Initializing bluezero peripheral...")
    
    def start(self):
        """Start BLE server in background thread."""
        if self._thread is not None:
            print("[BLE Server] Already started")
            return
        
        print("[BLE Server] Starting...")
        
        # Create peripheral and add service/characteristics
        self._setup_peripheral()
        
        # Start GLib main loop in thread
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        
        # Start status notification thread
        self._status_notify_thread = threading.Thread(
            target=self._status_notify_loop,
            daemon=True
        )
        self._status_notify_thread.start()
        
        print("[BLE Server] Started successfully")
        print("[BLE Server] Advertising as 'Tide Light'")
    
    def stop(self):
        """Stop BLE server and cleanup."""
        if self._thread is None:
            return
        
        print("[BLE Server] Stopping...")
        
        self._stop_event.set()
        
        if self._peripheral:
            try:
                self._peripheral.stop()
            except Exception as e:
                print(f"[BLE Server] Error stopping peripheral: {e}")
        
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
        
        if self._status_notify_thread:
            self._status_notify_thread.join(timeout=1.0)
            self._status_notify_thread = None
        
        print("[BLE Server] Stopped")
    
    def _setup_peripheral(self):
        """Setup bluezero peripheral with service and characteristics."""
        # Create peripheral
        self._peripheral = peripheral.Peripheral(
            'DC:A6:32:01:02:03',  # Dummy MAC, will be overridden by adapter
            local_name='Tide Light'
        )
        
        # Add service
        self._peripheral.add_service(
            srv_id=1,
            uuid=SERVICE_UUID,
            primary=True
        )
        
        # Add characteristics
        self._add_characteristics()
    
    def _add_characteristics(self):
        """Add all GATT characteristics to service."""
        # Characteristic 1: Tide Location (read/write)
        self._peripheral.add_characteristic(
            srv_id=1,
            chr_id=1,
            uuid=CHAR_LOCATION_UUID,
            value=[],
            notifying=False,
            flags=['read', 'write'],
            read_callback=self._read_location,
            write_callback=self._write_location
        )
        
        # Characteristic 2: LED Brightness (read/write)
        self._peripheral.add_characteristic(
            srv_id=1,
            chr_id=2,
            uuid=CHAR_BRIGHTNESS_UUID,
            value=[],
            notifying=False,
            flags=['read', 'write'],
            read_callback=self._read_brightness,
            write_callback=self._write_brightness
        )
        
        # Characteristic 3: LED Pattern (read/write)
        self._peripheral.add_characteristic(
            srv_id=1,
            chr_id=3,
            uuid=CHAR_PATTERN_UUID,
            value=[],
            notifying=False,
            flags=['read', 'write'],
            read_callback=self._read_pattern,
            write_callback=self._write_pattern
        )
        
        # Characteristic 4: Wave Speed (read/write)
        self._peripheral.add_characteristic(
            srv_id=1,
            chr_id=4,
            uuid=CHAR_WAVE_SPEED_UUID,
            value=[],
            notifying=False,
            flags=['read', 'write'],
            read_callback=self._read_wave_speed,
            write_callback=self._write_wave_speed
        )
        
        # Characteristic 5: LED Count (read/write)
        self._peripheral.add_characteristic(
            srv_id=1,
            chr_id=5,
            uuid=CHAR_LED_COUNT_UUID,
            value=[],
            notifying=False,
            flags=['read', 'write'],
            read_callback=self._read_led_count,
            write_callback=self._write_led_count
        )
        
        # Characteristic 6: LED Invert (read/write)
        self._peripheral.add_characteristic(
            srv_id=1,
            chr_id=6,
            uuid=CHAR_LED_INVERT_UUID,
            value=[],
            notifying=False,
            flags=['read', 'write'],
            read_callback=self._read_led_invert,
            write_callback=self._write_led_invert
        )
        
        # Characteristic 7: Full Config JSON (read/write)
        self._peripheral.add_characteristic(
            srv_id=1,
            chr_id=7,
            uuid=CHAR_FULL_CONFIG_UUID,
            value=[],
            notifying=False,
            flags=['read', 'write'],
            read_callback=self._read_full_config,
            write_callback=self._write_full_config
        )
        
        # Characteristic 8: Status (read/notify)
        self._peripheral.add_characteristic(
            srv_id=1,
            chr_id=8,
            uuid=CHAR_STATUS_UUID,
            value=[],
            notifying=True,
            flags=['read', 'notify'],
            read_callback=self._read_status
        )
        
        # Characteristic 9: Error Code (read-only)
        self._peripheral.add_characteristic(
            srv_id=1,
            chr_id=9,
            uuid=CHAR_ERROR_UUID,
            value=[],
            notifying=False,
            flags=['read'],
            read_callback=self._read_error
        )
    
    # -----------------------------
    # Read Callbacks
    # -----------------------------
    
    def _read_location(self) -> list:
        """Read location characteristic."""
        location_str = self._handler.get_location()
        return self._string_to_bytes(location_str)
    
    def _read_brightness(self) -> list:
        """Read brightness characteristic."""
        brightness = self._handler.get_brightness()
        return [brightness]
    
    def _read_pattern(self) -> list:
        """Read pattern characteristic."""
        pattern = self._handler.get_pattern()
        return self._string_to_bytes(pattern)
    
    def _read_wave_speed(self) -> list:
        """Read wave speed characteristic."""
        speed_str = self._handler.get_wave_speed()
        return self._string_to_bytes(speed_str)
    
    def _read_led_count(self) -> list:
        """Read LED count characteristic."""
        count = self._handler.get_led_count()
        return [count]
    
    def _read_led_invert(self) -> list:
        """Read LED invert characteristic."""
        invert = self._handler.get_led_invert()
        return [invert]
    
    def _read_full_config(self) -> list:
        """Read full config JSON characteristic."""
        config_json = self._handler.get_full_config()
        return self._string_to_bytes(config_json)
    
    def _read_status(self) -> list:
        """Read status characteristic."""
        status_json = self._status.get_status_json()
        return self._string_to_bytes(status_json)
    
    def _read_error(self) -> list:
        """Read error code characteristic."""
        error_code = self._handler.get_last_error()
        return [error_code]
    
    # -----------------------------
    # Write Callbacks
    # -----------------------------
    
    def _write_location(self, value: list):
        """Write location characteristic."""
        location_str = self._bytes_to_string(value)
        error_code = self._handler.update_location(location_str)
        print(f"[BLE Server] Location write: {location_str} (error={error_code})")
    
    def _write_brightness(self, value: list):
        """Write brightness characteristic."""
        if len(value) < 1:
            return
        brightness = value[0]
        error_code = self._handler.update_brightness(brightness)
        print(f"[BLE Server] Brightness write: {brightness} (error={error_code})")
    
    def _write_pattern(self, value: list):
        """Write pattern characteristic."""
        pattern = self._bytes_to_string(value)
        error_code = self._handler.update_pattern(pattern)
        print(f"[BLE Server] Pattern write: {pattern} (error={error_code})")
    
    def _write_wave_speed(self, value: list):
        """Write wave speed characteristic."""
        speed_str = self._bytes_to_string(value)
        error_code = self._handler.update_wave_speed(speed_str)
        print(f"[BLE Server] Wave speed write: {speed_str} (error={error_code})")
    
    def _write_led_count(self, value: list):
        """Write LED count characteristic."""
        if len(value) < 1:
            return
        count = value[0]
        error_code = self._handler.update_led_count(count)
        print(f"[BLE Server] LED count write: {count} (error={error_code})")
    
    def _write_led_invert(self, value: list):
        """Write LED invert characteristic."""
        if len(value) < 1:
            return
        invert = value[0]
        error_code = self._handler.update_led_invert(invert)
        print(f"[BLE Server] LED invert write: {invert} (error={error_code})")
    
    def _write_full_config(self, value: list):
        """Write full config JSON characteristic."""
        config_json = self._bytes_to_string(value)
        error_code = self._handler.update_full_config(config_json)
        print(f"[BLE Server] Full config write (error={error_code})")
    
    # -----------------------------
    # Helper Methods
    # -----------------------------
    
    def _string_to_bytes(self, s: str) -> list:
        """Convert string to list of bytes for BLE."""
        return list(s.encode('utf-8'))
    
    def _bytes_to_string(self, data: list) -> str:
        """Convert list of bytes to string from BLE."""
        return bytes(data).decode('utf-8')
    
    # -----------------------------
    # Background Threads
    # -----------------------------
    
    def _run_loop(self):
        """Run GLib main loop for BLE peripheral."""
        try:
            print("[BLE Server] Starting GLib main loop...")
            self._peripheral.publish()
            print("[BLE Server] Peripheral published and advertising")
        except Exception as e:
            print(f"[BLE Server] Error in main loop: {e}")
    
    def _status_notify_loop(self):
        """
        Periodically update status characteristic with notifications.
        Updates every 10 seconds.
        """
        print("[BLE Server] Starting status notification loop (10s interval)")
        
        while not self._stop_event.is_set():
            try:
                # Wait 10 seconds (or until stop)
                if self._stop_event.wait(timeout=10.0):
                    break
                
                # Update status characteristic
                # Note: Bluezero will automatically notify subscribed clients
                # when the characteristic value changes
                status_json = self._status.get_status_json()
                status_bytes = self._string_to_bytes(status_json)
                
                # Update characteristic value
                if self._peripheral:
                    try:
                        self._peripheral.update_characteristic(
                            srv_id=1,
                            chr_id=8,
                            value=status_bytes
                        )
                    except AttributeError:
                        # update_characteristic may not exist in older bluezero
                        # In that case, notifications happen via read_callback
                        pass
                
            except Exception as e:
                print(f"[BLE Server] Error in status notify loop: {e}")
        
        print("[BLE Server] Status notification loop stopped")
