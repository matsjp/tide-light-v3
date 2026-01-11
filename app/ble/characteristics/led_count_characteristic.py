"""
LED Count Characteristic for Tide Light.

Handles number of LEDs as a uint8 value (3-255).
UUID: 12345678-1234-5678-1234-56789abcdef5
Properties: Read, Write
"""

import logging
from pybleno import Characteristic
from ble.ble_data_utils import uint8_to_bytes, bytes_to_uint8


class LEDCountCharacteristic(Characteristic):
    """
    Characteristic for LED count.
    
    Format: uint8 (3-255)
    """
    
    def __init__(self, config_handler):
        """
        Initialize LED count characteristic.
        
        Args:
            config_handler: BLEConfigHandler instance for validation/updates
        """
        Characteristic.__init__(self, {
            'uuid': '12345678-1234-5678-1234-56789abcdef5',
            'properties': ['read', 'write'],
            'value': None
        })
        self._handler = config_handler
    
    def onReadRequest(self, offset, callback):
        """
        Handle read request for LED count.
        
        Args:
            offset: Byte offset (must be 0)
            callback: Callback function(result_code, data)
        """
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG, None)
        else:
            try:
                led_count = self._handler.get_led_count()
                data = uint8_to_bytes(led_count)
                callback(Characteristic.RESULT_SUCCESS, data)
            except Exception as e:
                logging.exception(f"LED count read error: {e}")
                callback(Characteristic.RESULT_UNLIKELY_ERROR, None)
    
    def onWriteRequest(self, data, offset, withoutResponse, callback):
        """
        Handle write request for LED count.
        
        Args:
            data: Byte array containing uint8 LED count
            offset: Byte offset (must be 0)
            withoutResponse: Whether response is needed
            callback: Callback function(result_code)
        """
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG)
        else:
            try:
                led_count = bytes_to_uint8(data)
                error_code = self._handler.update_led_count(led_count)
                
                if error_code == 0:
                    callback(Characteristic.RESULT_SUCCESS)
                else:
                    callback(0x80 + error_code)
            except Exception as e:
                logging.exception(f"LED count write error: {e}")
                callback(Characteristic.RESULT_UNLIKELY_ERROR)
