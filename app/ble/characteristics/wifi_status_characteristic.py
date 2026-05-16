"""
WiFi Status Characteristic for Tide Light.

Provides current WiFi connection status as JSON.
UUID: ec0d (expands to 0000ec0d-0000-1000-8000-00805f9b34fb)
Properties: Read, Notify
"""

import logging
from pybleno import Characteristic
from ble.ble_data_utils import json_to_bytes


class WiFiStatusCharacteristic(Characteristic):
    """
    Characteristic for WiFi connection status.
    
    Format: JSON object:
    {
        "connected": true,
        "ssid": "NetworkName",
        "signal": -45,
        "ip": "192.168.1.100",
        "status": "connected"
    }
    
    Status values: "disconnected", "connecting", "connected", "failed", "unavailable"
    """
    
    def __init__(self, wifi_handler):
        """
        Initialize WiFi status characteristic.
        
        Args:
            wifi_handler: WiFiHandler instance with get_wifi_status method
        """
        Characteristic.__init__(self, {
            'uuid': 'ec0d',
            'properties': ['read', 'notify'],
            'value': None
        })
        self._wifi_handler = wifi_handler
        self._updateValueCallback = None
        self._last_status_data = b''  # Cache for offset-based reads
    
    def onReadRequest(self, offset, callback):
        """
        Handle read request for WiFi status (supports offset-based reads).
        
        Args:
            offset: Byte offset for chunked reads
            callback: Callback function(result_code, data)
        """
        logging.info(f"[WiFi Status Characteristic] onReadRequest called! offset={offset}")
        try:
            if offset == 0:
                # First read - get fresh status and cache
                status_json = self._wifi_handler.get_wifi_status()
                self._last_status_data = json_to_bytes(status_json)
                logging.info(f"[WiFi Status Characteristic] Status size: {len(self._last_status_data)} bytes")
                callback(Characteristic.RESULT_SUCCESS, self._last_status_data)
            elif offset < len(self._last_status_data):
                # Subsequent read - return cached data from offset
                chunk = self._last_status_data[offset:]
                logging.info(f"[WiFi Status Characteristic] Offset {offset} - returning remaining {len(chunk)} bytes")
                callback(Characteristic.RESULT_SUCCESS, chunk)
            else:
                # Offset beyond data length
                logging.warning(f"[WiFi Status Characteristic] Offset {offset} beyond data length")
                callback(Characteristic.RESULT_INVALID_OFFSET, None)
        except Exception as e:
            logging.exception(f"[WiFi Status Characteristic] Read error: {e}")
            callback(Characteristic.RESULT_UNLIKELY_ERROR, None)
    
    def onSubscribe(self, maxValueSize, updateValueCallback):
        """
        Handle client subscription for notifications.
        
        Args:
            maxValueSize: Maximum value size client can receive
            updateValueCallback: Callback to send notifications
        """
        logging.info("[WiFi Status Characteristic] Client subscribed to notifications")
        self._updateValueCallback = updateValueCallback
    
    def onUnsubscribe(self):
        """Handle client unsubscription from notifications."""
        logging.info("[WiFi Status Characteristic] Client unsubscribed from notifications")
        self._updateValueCallback = None
    
    def notify_status_change(self):
        """
        Send status update notification to subscribed clients.
        Called by WiFiHandler when status changes.
        """
        if self._updateValueCallback is not None:
            try:
                status_json = self._wifi_handler.get_wifi_status()
                data = json_to_bytes(status_json)
                self._updateValueCallback(data)
                logging.debug("[WiFi Status Characteristic] Status notification sent")
            except Exception as e:
                logging.exception(f"WiFi status notification error: {e}")
