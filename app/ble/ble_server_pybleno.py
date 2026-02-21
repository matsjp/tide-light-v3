"""
BLE Server for Tide Light - Pybleno Implementation.

Uses pybleno library to create a GATT peripheral.
Exposes configuration characteristics for reading and writing.
Runs with event-driven callbacks.

Only imported when bluetooth.use_fake_library = false.
"""

import logging
from typing import Optional
from pybleno import Bleno
from ble.services.tide_light_service import TideLightService
from config_manager import ConfigManager
from ble.ble_config_handler import BLEConfigHandler
from ble.ble_status_provider import BLEStatusProvider
from ble.wifi_handler import WiFiHandler


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
        wifi_handler: Optional[WiFiHandler] = None
    ):
        """
        Initialize BLE server.
        
        Args:
            config_manager: ConfigManager instance
            config_handler: Handler for config validation and updates
            status_provider: Provider for status information
            wifi_handler: Optional handler for WiFi operations
        """
        self._config_manager = config_manager
        self._handler = config_handler
        self._status = status_provider
        self._wifi_handler = wifi_handler
        
        # Initialize Bleno
        self._bleno = Bleno()
        
        # Create service with optional WiFi handler
        self._service = TideLightService(config_handler, status_provider, wifi_handler)
        
        # Get device name from config
        config = self._config_manager.get_config()
        self._device_name = config.get('bluetooth', {}).get('device_name', 'Tide Light')
        
        # Service UUID for advertising
        self._service_uuid = '12345678-1234-5678-1234-56789abcdef0'
        
        # Register event handlers
        self._bleno.on('stateChange', self._on_state_change)
        self._bleno.on('advertisingStart', self._on_advertising_start)
        
        wifi_status = "enabled" if wifi_handler else "disabled"
        print(f"[BLE Server Pybleno] Initialized (WiFi {wifi_status})")
    
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
            def on_start_advertising(err):
                if err:
                    logging.error(f"[BLE Server Pybleno] Advertising error: {err}")
            
            self._bleno.startAdvertising(
                self._device_name,
                [self._service_uuid],
                on_start_advertising
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
            print(f"[BLE Server Pybleno] Advertising as '{self._device_name}'")
            print(f"[BLE Server Pybleno] Service UUID: {self._service_uuid}")
            
            # Register service
            self._bleno.setServices([self._service])
            print("[BLE Server Pybleno] Service registered successfully")
