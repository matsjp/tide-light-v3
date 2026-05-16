"""
BLE Server for Tide Light - Pybleno Implementation.

Uses pybleno library to create a GATT peripheral.
Exposes configuration characteristics for reading and writing.
Runs with event-driven callbacks.

Only imported when bluetooth.use_fake_library = false.
"""

import logging
from typing import Optional
from pybleno import Bleno, BlenoPrimaryService
from ble.services.tide_light_service import TideLightService
from config_manager import ConfigManager
from ble.ble_config_handler import BLEConfigHandler
from ble.ble_status_provider import BLEStatusProvider
from ble.wifi_handler import WiFiHandler
from rtc_manager import RTCManager


class BLEServerPybleno:
    """
    Real BLE GATT server using pybleno.
    Exposes Tide Light configuration as BLE characteristics.
    """
    
    def __init__(
        self,
        config_manager: ConfigManager,
        config_handler: BLEConfigHandler,
        status_provider: BLEStatusProvider,
        wifi_handler: Optional[WiFiHandler] = None,
        rtc_manager: Optional[RTCManager] = None
    ):
        """
        Initialize BLE server.
        
        Args:
            config_manager: ConfigManager instance
            config_handler: Handler for config validation and updates
            status_provider: Provider for status information
            wifi_handler: Optional handler for WiFi operations
            rtc_manager: Optional handler for RTC operations
        """
        self._config_manager = config_manager
        self._handler = config_handler
        self._status = status_provider
        self._wifi_handler = wifi_handler
        self._rtc_manager = rtc_manager
        
        # Get device name and UUID from config FIRST
        config = self._config_manager.get_config()
        self._device_name = config.get('bluetooth', {}).get('device_name', 'Tide Light')
        self._service_uuid = 'ec00'  # SHORT UUID (works with multiple characteristics!)
        
        # Initialize Bleno
        self._bleno = Bleno()
        
        # Build characteristics list using SHORT UUIDs
        from ble.characteristics import (
            LocationCharacteristic,
            BrightnessCharacteristic,
            PatternCharacteristic,
            WaveSpeedCharacteristic,
            LEDCountCharacteristic,
            LEDInvertCharacteristic,
            StatusCharacteristic,
        )
        from ble.characteristics.wifi_networks_characteristic import WiFiNetworksCharacteristic
        from ble.characteristics.wifi_ssid_characteristic import WiFiSsidCharacteristic
        from ble.characteristics.wifi_password_characteristic import WiFiPasswordCharacteristic
        from ble.characteristics.wifi_status_characteristic import WiFiStatusCharacteristic
        from ble.characteristics.ldr_active_characteristic import LdrActiveCharacteristic
        from ble.characteristics.system_time_characteristic import SystemTimeCharacteristic
        from ble.characteristics.reset_characteristic import ResetCharacteristic
        
        # TESTING: Enable location, brightness, pattern, wave speed, LED count, LED invert, LDR active, status, WiFi
        characteristics = [
            LocationCharacteristic(self._handler),          # ec01
            BrightnessCharacteristic(self._handler),        # ec02
            PatternCharacteristic(self._handler),           # ec03
            WaveSpeedCharacteristic(self._handler),         # ec04
            LEDCountCharacteristic(self._handler),          # ec05
            LEDInvertCharacteristic(self._handler),         # ec06
            StatusCharacteristic(self._status),             # ec08
            LdrActiveCharacteristic(self._handler),         # ec0e
        ]
        
        # Enable RTC characteristic
        if self._rtc_manager:
            characteristics.append(SystemTimeCharacteristic(self._rtc_manager))  # ec0f
        
        # Enable Reset characteristic
        if self._config_manager:
            characteristics.append(ResetCharacteristic(self._config_manager))    # ec10
        
        # Enable WiFi characteristics
        if self._wifi_handler:
            wifi_status_char = WiFiStatusCharacteristic(self._wifi_handler)     # ec0d
            self._wifi_handler.set_status_characteristic(wifi_status_char)
            
            characteristics.extend([
                WiFiNetworksCharacteristic(self._wifi_handler),  # ec0a
                WiFiSsidCharacteristic(self._wifi_handler),      # ec0b
                WiFiPasswordCharacteristic(self._wifi_handler),  # ec0c
                wifi_status_char,                                 # ec0d
            ])
        
        # Create service
        self._service = BlenoPrimaryService({
            'uuid': self._service_uuid,
            'characteristics': characteristics
        })
        
        print(f"[BLE Server Pybleno] Created service with {len(characteristics)} characteristics (SHORT UUIDs)")
        
        # Register event handlers
        self._bleno.on('stateChange', self._on_state_change)
        self._bleno.on('advertisingStart', self._on_advertising_start)
        
        wifi_status = "enabled" if wifi_handler else "disabled"
        rtc_status = "enabled" if rtc_manager else "disabled"
        print(f"[BLE Server Pybleno] Initialized (WiFi {wifi_status}, RTC {rtc_status})")
    
    def start(self):
        """Start BLE server."""
        print("[BLE Server Pybleno] Starting...")
        self._bleno.start()
    
    def stop(self):
        """Stop BLE server and cleanup."""
        print("[BLE Server Pybleno] Stopping...")
        self._bleno.stopAdvertising()
        self._bleno.disconnect()
        print("[BLE Server Pybleno] Stopped")
    
    def _on_state_change(self, state):
        """
        Handle Bluetooth adapter state changes.
        
        Args:
            state: New state ('poweredOn', 'poweredOff', etc.)
        """
        print(f"[BLE Server Pybleno] State changed: {state}")
        
        if state == 'poweredOn':
            # Start advertising when Bluetooth is ready
            self._bleno.startAdvertising(
                self._device_name,
                [self._service_uuid]
            )
        else:
            # Stop advertising if Bluetooth is not ready
            self._bleno.stopAdvertising()
    
    def _on_advertising_start(self, error):
        """
        Handle advertising start event.
        
        Args:
            error: Error object if advertising failed, None otherwise
        """
        if error:
            logging.error(f"[BLE Server Pybleno] Failed to start advertising: {error}")
        else:
            print(f"[BLE Server Pybleno] Advertising started successfully")
            print(f"[BLE Server Pybleno] Device name: '{self._device_name}'")
            print(f"[BLE Server Pybleno] Service UUID: {self._service_uuid}")
            
            # Register service AFTER advertising (like V2 does)
            print(f"[BLE Server Pybleno] Registering service (created in __init__)...")
            self._bleno.setServices([self._service])
            
            print("[BLE Server Pybleno] Ready for connections")
