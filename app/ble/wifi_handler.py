"""
WiFi Handler for BLE characteristics.

Wraps WiFi Manager and provides BLE-friendly interface
with proper error code handling.
"""

import json
import logging
from typing import Optional
from network.wifi_manager import WiFiManager
from ble.ble_characteristics import (
    BLE_ERROR_NONE,
    BLE_ERROR_WIFI_INVALID_SSID,
    BLE_ERROR_WIFI_INVALID_PASSWORD,
    BLE_ERROR_WIFI_CONNECTION_FAILED,
    BLE_ERROR_WIFI_NO_HARDWARE
)


class WiFiHandler:
    """
    Handles WiFi operations for BLE characteristics.
    Manages connection state and validates inputs.
    """
    
    def __init__(self, wifi_manager: WiFiManager):
        """
        Initialize WiFi handler.
        
        Args:
            wifi_manager: WiFiManager instance
        """
        self._wifi_manager = wifi_manager
        self._target_ssid = None
        self._wifi_status_characteristic = None  # Set by characteristic for notifications
    
    def set_status_characteristic(self, characteristic):
        """
        Set reference to WiFi status characteristic for notifications.
        
        Args:
            characteristic: WiFiStatusCharacteristic instance
        """
        self._wifi_status_characteristic = characteristic
    
    def scan_wifi_networks(self) -> str:
        """
        Scan for available WiFi networks.
        
        Returns:
            JSON string with array of network objects
        """
        if not self._wifi_manager.is_wifi_available():
            logging.warning("[WiFi Handler] WiFi hardware not available")
            return json.dumps([])
        
        networks = self._wifi_manager.scan_networks()
        return json.dumps(networks)
    
    def set_target_ssid(self, ssid: str) -> int:
        """
        Set target SSID for connection.
        
        Args:
            ssid: Network SSID
        
        Returns:
            Error code (0 = success)
        """
        # Validate SSID
        if not ssid or len(ssid) == 0:
            logging.error("[WiFi Handler] Empty SSID provided")
            return BLE_ERROR_WIFI_INVALID_SSID
        
        if len(ssid) > 32:
            logging.error(f"[WiFi Handler] SSID too long: {len(ssid)} characters")
            return BLE_ERROR_WIFI_INVALID_SSID
        
        self._target_ssid = ssid
        logging.info(f"[WiFi Handler] Target SSID set to: {ssid}")
        return BLE_ERROR_NONE
    
    def connect_wifi(self, password: str) -> int:
        """
        Connect to WiFi using stored SSID and provided password.
        
        Args:
            password: WPA password (empty string for open networks)
        
        Returns:
            Error code (0 = success)
        """
        # Check if WiFi is available
        if not self._wifi_manager.is_wifi_available():
            logging.error("[WiFi Handler] WiFi hardware not available")
            return BLE_ERROR_WIFI_NO_HARDWARE
        
        # Check if SSID was set
        if not self._target_ssid:
            logging.error("[WiFi Handler] No target SSID set")
            return BLE_ERROR_WIFI_INVALID_SSID
        
        # Validate password for secured networks
        # Note: Open networks can have empty password
        if password and len(password) < 8:
            logging.error("[WiFi Handler] Password too short (minimum 8 characters for WPA)")
            return BLE_ERROR_WIFI_INVALID_PASSWORD
        
        if len(password) > 63:
            logging.error(f"[WiFi Handler] Password too long: {len(password)} characters")
            return BLE_ERROR_WIFI_INVALID_PASSWORD
        
        # Attempt connection
        logging.info(f"[WiFi Handler] Attempting to connect to '{self._target_ssid}'")
        success = self._wifi_manager.connect_network(self._target_ssid, password)
        
        # Notify status change
        if self._wifi_status_characteristic:
            self._wifi_status_characteristic.notify_status_change()
        
        if success:
            logging.info(f"[WiFi Handler] Successfully connected to '{self._target_ssid}'")
            return BLE_ERROR_NONE
        else:
            logging.error(f"[WiFi Handler] Failed to connect to '{self._target_ssid}'")
            return BLE_ERROR_WIFI_CONNECTION_FAILED
    
    def get_wifi_status(self) -> str:
        """
        Get current WiFi connection status.
        
        Returns:
            JSON string with status object
        """
        if not self._wifi_manager.is_wifi_available():
            status = {
                'connected': False,
                'ssid': None,
                'signal': None,
                'ip': None,
                'status': 'unavailable'
            }
            return json.dumps(status)
        
        status = self._wifi_manager.get_connection_status()
        return json.dumps(status)
