"""
WiFi Networks List Characteristic for Tide Light.

Provides list of available WiFi networks as JSON.
UUID: 12345678-1234-5678-1234-56789abcdefa
Properties: Read
"""

import logging
from pybleno import Characteristic
from ble.ble_data_utils import json_to_bytes


class WiFiNetworksCharacteristic(Characteristic):
    """
    Characteristic for available WiFi networks list.
    
    Format: JSON array of network objects:
    [
        {
            "ssid": "NetworkName",
            "signal": -45,
            "security": "WPA2"
        },
        ...
    ]
    
    Reading this characteristic triggers a fresh WiFi scan (may take 2-5 seconds).
    """
    
    def __init__(self, wifi_handler):
        """
        Initialize WiFi networks characteristic.
        
        Args:
            wifi_handler: WiFiHandler instance with scan_networks method
        """
        Characteristic.__init__(self, {
            'uuid': '12345678-1234-5678-1234-56789abcdefa',
            'properties': ['read'],
            'value': None
        })
        self._wifi_handler = wifi_handler
    
    def onReadRequest(self, offset, callback):
        """
        Handle read request for WiFi networks.
        Triggers a fresh scan and returns results.
        
        Args:
            offset: Byte offset (must be 0)
            callback: Callback function(result_code, data)
        """
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG, None)
        else:
            try:
                logging.info("[WiFi Networks Characteristic] Scanning for networks...")
                networks_json = self._wifi_handler.scan_wifi_networks()
                data = json_to_bytes(networks_json)
                logging.info(f"[WiFi Networks Characteristic] Returning {len(networks_json)} bytes")
                callback(Characteristic.RESULT_SUCCESS, data)
            except Exception as e:
                logging.exception(f"WiFi networks read error: {e}")
                callback(Characteristic.RESULT_UNLIKELY_ERROR, None)
