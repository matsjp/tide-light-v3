"""
Pattern Characteristic for Tide Light.

Handles LED pattern as a string ("none" or "wave").
UUID: 12345678-1234-5678-1234-56789abcdef3
Properties: Read, Write
"""

import logging
from pybleno import Characteristic
from ble.ble_data_utils import string_to_bytes, bytes_to_string


class PatternCharacteristic(Characteristic):
    """
    Characteristic for LED pattern.
    
    Format: String ("none" or "wave")
    """
    
    def __init__(self, config_handler):
        """
        Initialize pattern characteristic.
        
        Args:
            config_handler: BLEConfigHandler instance for validation/updates
        """
        Characteristic.__init__(self, {
            'uuid': '12345678-1234-5678-1234-56789abcdef3',
            'properties': ['read', 'write'],
            'value': None
        })
        self._handler = config_handler
    
    def onReadRequest(self, offset, callback):
        """
        Handle read request for pattern.
        
        Args:
            offset: Byte offset (must be 0)
            callback: Callback function(result_code, data)
        """
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG, None)
        else:
            try:
                pattern = self._handler.get_pattern()
                data = string_to_bytes(pattern)
                callback(Characteristic.RESULT_SUCCESS, data)
            except Exception as e:
                logging.exception(f"Pattern read error: {e}")
                callback(Characteristic.RESULT_UNLIKELY_ERROR, None)
    
    def onWriteRequest(self, data, offset, withoutResponse, callback):
        """
        Handle write request for pattern.
        
        Args:
            data: Byte array containing pattern string
            offset: Byte offset (must be 0)
            withoutResponse: Whether response is needed
            callback: Callback function(result_code)
        """
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG)
        else:
            try:
                pattern = bytes_to_string(data)
                error_code = self._handler.update_pattern(pattern)
                
                if error_code == 0:
                    callback(Characteristic.RESULT_SUCCESS)
                else:
                    callback(0x80 + error_code)
            except Exception as e:
                logging.exception(f"Pattern write error: {e}")
                callback(Characteristic.RESULT_UNLIKELY_ERROR)
