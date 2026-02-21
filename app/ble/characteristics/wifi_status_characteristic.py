"""
WiFi Status Characteristic for Tide Light.

Provides current WiFi connection status as JSON.
UUID: 12345678-1234-5678-1234-56789abcdefd
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
            'uuid': '12345678-1234-5678-1234-56789abcdefd',
            'properties': ['read', 'notify'],
            'value': None
        })
        self._wifi_handler = wifi_handler
        self._updateValueCallback = None
    
    def onReadRequest(self, offset, callback):
        """
        Handle read request for WiFi status.
        
        Args:
            offset: Byte offset (must be 0)
            callback: Callback function(result_code, data)
        """
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG, None)
        else:
            try:
                status_json = self._wifi_handler.get_wifi_status()
                data = json_to_bytes(status_json)
                callback(Characteristic.RESULT_SUCCESS, data)
            except Exception as e:
                logging.exception(f"WiFi status read error: {e}")
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
