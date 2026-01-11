"""
Brightness Characteristic for Tide Light.

Handles LED brightness as a uint8 value (0-255).
UUID: 12345678-1234-5678-1234-56789abcdef2
Properties: Read, Write
"""

import logging
from pybleno import Characteristic
from ble.ble_data_utils import uint8_to_bytes, bytes_to_uint8


class BrightnessCharacteristic(Characteristic):
    """
    Characteristic for LED brightness.
    
    Format: uint8 (0-255)
    """
    
    def __init__(self, config_handler):
        """
        Initialize brightness characteristic.
        
        Args:
            config_handler: BLEConfigHandler instance for validation/updates
        """
        Characteristic.__init__(self, {
            'uuid': '12345678-1234-5678-1234-56789abcdef2',
            'properties': ['read', 'write'],
            'value': None
        })
        self._handler = config_handler
    
    def onReadRequest(self, offset, callback):
        """
        Handle read request for brightness.
        
        Args:
            offset: Byte offset (must be 0)
            callback: Callback function(result_code, data)
        """
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG, None)
        else:
            try:
                brightness = self._handler.get_brightness()
                data = uint8_to_bytes(brightness)
                callback(Characteristic.RESULT_SUCCESS, data)
            except Exception as e:
                logging.exception(f"Brightness read error: {e}")
                callback(Characteristic.RESULT_UNLIKELY_ERROR, None)
    
    def onWriteRequest(self, data, offset, withoutResponse, callback):
        """
        Handle write request for brightness.
        
        Args:
            data: Byte array containing uint8 brightness value
            offset: Byte offset (must be 0)
            withoutResponse: Whether response is needed
            callback: Callback function(result_code)
        """
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG)
        else:
            try:
                brightness = bytes_to_uint8(data)
                error_code = self._handler.update_brightness(brightness)
                
                if error_code == 0:
                    callback(Characteristic.RESULT_SUCCESS)
                else:
                    callback(0x80 + error_code)
            except Exception as e:
                logging.exception(f"Brightness write error: {e}")
                callback(Characteristic.RESULT_UNLIKELY_ERROR)
