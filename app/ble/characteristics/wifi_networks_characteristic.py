"""
WiFi Networks List Characteristic for Tide Light.

Provides list of available WiFi networks via notifications.
UUID: ec0a (expands to 0000ec0a-0000-1000-8000-00805f9b34fb)
Properties: Notify

Protocol:
1. Client subscribes to notifications
2. Subscription triggers WiFi scan (2-5 seconds)
3. Networks sent as JSON batches (3 networks per notification)
4. Empty array [] signals scan completion
5. Client unsubscribes after receiving completion signal
"""

import logging
import threading
import time
import json
from pybleno import Characteristic
from ble.ble_data_utils import json_to_bytes


class WiFiNetworksCharacteristic(Characteristic):
    """
    Characteristic for available WiFi networks list.
    
    Uses notification-based protocol to stream all available networks
    without 512-byte BLE limit restrictions.
    
    Notification Format: JSON array of 0-3 network objects:
    [
        {
            "ssid": "NetworkName",
            "signal": -45,
            "security": "WPA2"
        },
        ...
    ]
    
    Completion signal: Empty array []
    """
    
    def __init__(self, wifi_handler):
        """
        Initialize WiFi networks characteristic.
        
        Args:
            wifi_handler: WiFiHandler instance with scan_wifi_networks method
        """
        Characteristic.__init__(self, {
            'uuid': 'ec0a',
            'properties': ['notify'],  # Notify-only, no read
            'value': None
        })
        self._wifi_handler = wifi_handler
        self._updateValueCallback = None
        self._scan_thread = None
    
    def onSubscribe(self, maxValueSize, updateValueCallback):
        """
        Handle client subscription - trigger WiFi scan.
        
        Subscription automatically triggers a fresh WiFi scan.
        Results are sent as notifications as they become available.
        
        Args:
            maxValueSize: Maximum value size client can receive
            updateValueCallback: Callback to send notifications
        """
        logging.info("[WiFi Networks Characteristic] Client subscribed - starting scan")
        self._updateValueCallback = updateValueCallback
        self._start_scan()
    
    def onUnsubscribe(self):
        """
        Handle client unsubscription.
        
        Cleans up callback reference. Scan thread will complete naturally.
        """
        logging.info("[WiFi Networks Characteristic] Client unsubscribed")
        self._updateValueCallback = None
    
    def _start_scan(self):
        """
        Start background WiFi scan and send results via notifications.
        
        Runs in separate thread to avoid blocking BLE operations.
        Sends networks in batches of 3 to fit within BLE packet size limits.
        Final notification is empty array to signal completion.
        """
        def scan_worker():
            try:
                logging.info("[WiFi Networks Characteristic] Starting WiFi scan...")
                
                # Get all networks from WiFi handler
                networks_json = self._wifi_handler.scan_wifi_networks()
                networks = json.loads(networks_json)
                
                logging.info(f"[WiFi Networks Characteristic] Scan complete - found {len(networks)} networks")
                
                if len(networks) == 0:
                    # No networks found - send empty array and we're done
                    if self._updateValueCallback is not None:
                        self._updateValueCallback(json_to_bytes('[]'))
                        logging.info("[WiFi Networks Characteristic] Sent completion (no networks)")
                    return
                
                # Send networks in batches of 3
                batch_size = 3
                batch_count = 0
                
                for i in range(0, len(networks), batch_size):
                    # Check if client unsubscribed
                    if self._updateValueCallback is None:
                        logging.info("[WiFi Networks Characteristic] Client unsubscribed - stopping scan")
                        return
                    
                    # Get batch of networks
                    batch = networks[i:i+batch_size]
                    batch_count += 1
                    
                    # Convert to JSON and send
                    batch_json = json.dumps(batch, separators=(',', ':'))
                    data = json_to_bytes(batch_json)
                    
                    logging.info(f"[WiFi Networks Characteristic] Sending batch {batch_count} with {len(batch)} networks ({len(data)} bytes)")
                    self._updateValueCallback(data)
                    
                    # Small delay to prevent BLE throttling
                    time.sleep(0.1)
                
                # Send completion signal (empty array)
                if self._updateValueCallback is not None:
                    self._updateValueCallback(json_to_bytes('[]'))
                    logging.info(f"[WiFi Networks Characteristic] Sent completion signal ({batch_count} batches total)")
                
            except Exception as e:
                logging.exception(f"[WiFi Networks Characteristic] Scan error: {e}")
                # Send empty array to signal completion even on error
                if self._updateValueCallback is not None:
                    self._updateValueCallback(json_to_bytes('[]'))
        
        # Start scan in background thread
        self._scan_thread = threading.Thread(target=scan_worker, daemon=True)
        self._scan_thread.start()
