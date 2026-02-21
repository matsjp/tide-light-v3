"""
WiFi SSID Characteristic for Tide Light.

Allows writing the target WiFi network SSID to connect to.
UUID: 12345678-1234-5678-1234-56789abcdefb
Properties: Write
"""

import logging
from pybleno import Characteristic
from ble.ble_data_utils import bytes_to_string


class WiFiSsidCharacteristic(Characteristic):
    """
    Characteristic for setting target WiFi SSID.
    
    Format: String (SSID name)
    
    Write the SSID, then write password, to initiate connection.
    """
    
    def __init__(self, wifi_handler):
        """
        Initialize WiFi SSID characteristic.
        
        Args:
            wifi_handler: WiFiHandler instance with set_target_ssid method
        """
        Characteristic.__init__(self, {
            'uuid': '12345678-1234-5678-1234-56789abcdefb',
            'properties': ['write'],
            'value': None
        })
        self._wifi_handler = wifi_handler
    
    def onWriteRequest(self, data, offset, withoutResponse, callback):
        """
        Handle write request for WiFi SSID.
        
        Args:
            data: Bytes containing SSID string
            offset: Byte offset (must be 0)
            withoutResponse: Whether response is expected
            callback: Callback function(result_code)
        """
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG)
        else:
            try:
                ssid = bytes_to_string(data)
                logging.info(f"[WiFi SSID Characteristic] Setting target SSID: {ssid}")
                
                error_code = self._wifi_handler.set_target_ssid(ssid)
                
                if error_code == 0:
                    callback(Characteristic.RESULT_SUCCESS)
                else:
                    callback(0x80 + error_code)  # BLE error mapping
                    
            except Exception as e:
                logging.exception(f"WiFi SSID write error: {e}")
                callback(Characteristic.RESULT_UNLIKELY_ERROR)
