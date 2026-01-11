"""
LED Invert Characteristic for Tide Light.

Handles LED inversion flag as a boolean (uint8: 0 or 1).
UUID: 12345678-1234-5678-1234-56789abcdef6
Properties: Read, Write
"""

import logging
from pybleno import Characteristic
from ble.ble_data_utils import uint8_to_bytes, bytes_to_uint8


class LEDInvertCharacteristic(Characteristic):
    """
    Characteristic for LED inversion.
    
    Format: uint8 (0=false, 1=true)
    """
    
    def __init__(self, config_handler):
        """
        Initialize LED invert characteristic.
        
        Args:
            config_handler: BLEConfigHandler instance for validation/updates
        """
        Characteristic.__init__(self, {
            'uuid': '12345678-1234-5678-1234-56789abcdef6',
            'properties': ['read', 'write'],
            'value': None
        })
        self._handler = config_handler
    
    def onReadRequest(self, offset, callback):
        """
        Handle read request for LED invert.
        
        Args:
            offset: Byte offset (must be 0)
            callback: Callback function(result_code, data)
        """
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG, None)
        else:
            try:
                led_invert = self._handler.get_led_invert()
                # Convert bool to uint8: True->1, False->0
                data = uint8_to_bytes(1 if led_invert else 0)
                callback(Characteristic.RESULT_SUCCESS, data)
            except Exception as e:
                logging.exception(f"LED invert read error: {e}")
                callback(Characteristic.RESULT_UNLIKELY_ERROR, None)
    
    def onWriteRequest(self, data, offset, withoutResponse, callback):
        """
        Handle write request for LED invert.
        
        Args:
            data: Byte array containing uint8 (0 or 1)
            offset: Byte offset (must be 0)
            withoutResponse: Whether response is needed
            callback: Callback function(result_code)
        """
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG)
        else:
            try:
                invert_value = bytes_to_uint8(data)
                error_code = self._handler.update_led_invert(invert_value)
                
                if error_code == 0:
                    callback(Characteristic.RESULT_SUCCESS)
                else:
                    callback(0x80 + error_code)
            except Exception as e:
                logging.exception(f"LED invert write error: {e}")
                callback(Characteristic.RESULT_UNLIKELY_ERROR)
