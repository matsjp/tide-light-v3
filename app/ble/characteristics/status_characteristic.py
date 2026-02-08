"""
Status Characteristic for Tide Light.

Provides system status as JSON string with notifications.
UUID: 12345678-1234-5678-1234-56789abcdef8
Properties: Read, Notify
"""

import logging
import threading
import time
from pybleno import Characteristic
from ble.ble_data_utils import json_to_bytes


class StatusCharacteristic(Characteristic):
    """
    Characteristic for system status with periodic notifications.
    
    Format: JSON string containing:
    - tide_direction: "rising" | "falling" | "high" | "low" | "unknown"
    - tide_progress: float (0.0-1.0)
    - cache_info: dict with "cached", "age_hours"
    - system_uptime: float (seconds)
    
    Notifications sent every 10 seconds when subscribed.
    """
    
    def __init__(self, status_provider):
        """
        Initialize status characteristic.
        
        Args:
            status_provider: BLEStatusProvider instance
        """
        Characteristic.__init__(self, {
            'uuid': '12345678-1234-5678-1234-56789abcdef8',
            'properties': ['read', 'notify'],
            'value': None
        })
        self._status_provider = status_provider
        self._updateValueCallback = None
        self._notify_thread = None
        self._stop_notify = threading.Event()
    
    def onReadRequest(self, offset, callback):
        """
        Handle read request for status.
        
        Args:
            offset: Byte offset (must be 0)
            callback: Callback function(result_code, data)
        """
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG, None)
        else:
            try:
                status_json = self._status_provider.get_status_json()
                data = json_to_bytes(status_json)
                callback(Characteristic.RESULT_SUCCESS, data)
            except Exception as e:
                logging.exception(f"Status read error: {e}")
                callback(Characteristic.RESULT_UNLIKELY_ERROR, None)
    
    def onSubscribe(self, maxValueSize, updateValueCallback):
        """
        Handle client subscription for notifications.
        
        Args:
            maxValueSize: Maximum value size client can receive
            updateValueCallback: Callback to send notifications
        """
        logging.info("[Status Characteristic] Client subscribed to notifications")
        self._updateValueCallback = updateValueCallback
        self._start_notify_thread()
    
    def onUnsubscribe(self):
        """Handle client unsubscription from notifications."""
        logging.info("[Status Characteristic] Client unsubscribed from notifications")
        self._stop_notify_thread()
        self._updateValueCallback = None
    
    def _start_notify_thread(self):
        """Start background thread for periodic status notifications."""
        if self._notify_thread is not None and self._notify_thread.is_alive():
            return
        
        self._stop_notify.clear()
        self._notify_thread = threading.Thread(
            target=self._notify_loop,
            daemon=True
        )
        self._notify_thread.start()
        logging.info("[Status Characteristic] Notification thread started")
    
    def _stop_notify_thread(self):
        """Stop the notification thread."""
        self._stop_notify.set()
    
    def _notify_loop(self):
        """
        Background loop that sends status notifications every 10 seconds.
        Runs while client is subscribed.
        """
        while not self._stop_notify.is_set():
            if self._updateValueCallback is not None:
                try:
                    status_json = self._status_provider.get_status_json()
                    data = json_to_bytes(status_json)
                    self._updateValueCallback(data)
                    logging.debug("[Status Characteristic] Notification sent")
                except Exception as e:
                    logging.exception(f"Status notification error: {e}")
                    break
            
            # Wait 10 seconds or until stop event
            if self._stop_notify.wait(10):
                break
        
        logging.info("[Status Characteristic] Notification thread stopped")
