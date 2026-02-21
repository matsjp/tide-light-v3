"""
LDR Active Characteristic for Tide Light.

Handles LDR enable/disable as a boolean (0x00 = disabled, 0x01 = enabled).
UUID: 12345678-1234-5678-1234-56789abcdefe
Properties: Read, Write
"""

import logging
from pybleno import Characteristic
from ble.ble_data_utils import uint8_to_bytes, bytes_to_uint8


class LdrActiveCharacteristic(Characteristic):
    """
    Characteristic for LDR enable/disable.
    
    Format: uint8 (0x00 = disabled, 0x01 = enabled)
    """
    
    def __init__(self, config_handler):
        """
        Initialize LDR active characteristic.
        
        Args:
            config_handler: BLEConfigHandler instance for validation/updates
        """
        Characteristic.__init__(self, {
            'uuid': '12345678-1234-5678-1234-56789abcdefe',
            'properties': ['read', 'write'],
            'value': None
        })
        self._handler = config_handler
    
    def onReadRequest(self, offset, callback):
        """
        Handle read request for LDR active state.
        
        Args:
            offset: Byte offset (must be 0)
            callback: Callback function(result_code, data)
        """
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG, None)
        else:
            try:
                enabled = self._handler.get_ldr_active()
                data = uint8_to_bytes(1 if enabled else 0)
                callback(Characteristic.RESULT_SUCCESS, data)
            except Exception as e:
                logging.exception(f"LDR active read error: {e}")
                callback(Characteristic.RESULT_UNLIKELY_ERROR, None)
    
    def onWriteRequest(self, data, offset, withoutResponse, callback):
        """
        Handle write request for LDR active state.
        
        Args:
            data: Byte array containing uint8 boolean value (0 or 1)
            offset: Byte offset (must be 0)
            withoutResponse: Whether response is needed
            callback: Callback function(result_code)
        """
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG)
        else:
            try:
                value = bytes_to_uint8(data)
                enabled = bool(value)
                error_code = self._handler.update_ldr_active(enabled)
                
                if error_code == 0:
                    callback(Characteristic.RESULT_SUCCESS)
                else:
                    callback(0x80 + error_code)
            except Exception as e:
                logging.exception(f"LDR active write error: {e}")
                callback(Characteristic.RESULT_UNLIKELY_ERROR)
