"""
Error Characteristic for Tide Light.

Provides last error code as a uint8 value.
UUID: 12345678-1234-5678-1234-56789abcdef9
Properties: Read-only
"""

import logging
from pybleno import Characteristic
from ble.ble_data_utils import uint8_to_bytes


class ErrorCharacteristic(Characteristic):
    """
    Characteristic for last error code.
    
    Format: uint8
    Error codes:
    - 0: Success (no error)
    - 1: Invalid format
    - 2: Out of range
    - 3: Invalid value
    - 4: Internal error
    """
    
    def __init__(self, config_handler):
        """
        Initialize error characteristic.
        
        Args:
            config_handler: BLEConfigHandler instance
        """
        Characteristic.__init__(self, {
            'uuid': '12345678-1234-5678-1234-56789abcdef9',
            'properties': ['read'],
            'value': None
        })
        self._handler = config_handler
    
    def onReadRequest(self, offset, callback):
        """
        Handle read request for error code.
        
        Args:
            offset: Byte offset (must be 0)
            callback: Callback function(result_code, data)
        """
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG, None)
        else:
            try:
                error_code = self._handler.get_last_error()
                data = uint8_to_bytes(error_code)
                callback(Characteristic.RESULT_SUCCESS, data)
            except Exception as e:
                logging.exception(f"Error code read error: {e}")
                callback(Characteristic.RESULT_UNLIKELY_ERROR, None)
