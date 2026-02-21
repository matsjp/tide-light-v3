"""
WiFi Password Characteristic for Tide Light.

Allows writing WiFi password (write-only for security).
UUID: 12345678-1234-5678-1234-56789abcdefc
Properties: Write (no read)
"""

import logging
from pybleno import Characteristic
from ble.ble_data_utils import bytes_to_string


class WiFiPasswordCharacteristic(Characteristic):
    """
    Characteristic for setting WiFi password.
    
    Format: String (WPA password)
    
    Write-only for security. Password is never readable.
    Writing password triggers connection attempt to previously set SSID.
    """
    
    def __init__(self, wifi_handler):
        """
        Initialize WiFi password characteristic.
        
        Args:
            wifi_handler: WiFiHandler instance with connect_wifi method
        """
        Characteristic.__init__(self, {
            'uuid': '12345678-1234-5678-1234-56789abcdefc',
            'properties': ['write'],
            'value': None
        })
        self._wifi_handler = wifi_handler
    
    def onWriteRequest(self, data, offset, withoutResponse, callback):
        """
        Handle write request for WiFi password.
        Triggers connection attempt.
        
        Args:
            data: Bytes containing password string
            offset: Byte offset (must be 0)
            withoutResponse: Whether response is expected
            callback: Callback function(result_code)
        """
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG)
        else:
            try:
                password = bytes_to_string(data)
                logging.info("[WiFi Password Characteristic] Password received, attempting connection...")
                
                # Connect to WiFi with stored SSID and provided password
                error_code = self._wifi_handler.connect_wifi(password)
                
                if error_code == 0:
                    logging.info("[WiFi Password Characteristic] Connection initiated successfully")
                    callback(Characteristic.RESULT_SUCCESS)
                else:
                    logging.error(f"[WiFi Password Characteristic] Connection failed with error code: {error_code}")
                    callback(0x80 + error_code)  # BLE error mapping
                    
            except Exception as e:
                logging.exception(f"WiFi password write error: {e}")
                callback(Characteristic.RESULT_UNLIKELY_ERROR)
