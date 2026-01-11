"""
Wave Speed Characteristic for Tide Light.

Handles wave animation speed as a float string (0.1-5.0 seconds).
UUID: 12345678-1234-5678-1234-56789abcdef4
Properties: Read, Write
"""

import logging
from pybleno import Characteristic
from ble.ble_data_utils import string_to_bytes, bytes_to_string


class WaveSpeedCharacteristic(Characteristic):
    """
    Characteristic for wave animation speed.
    
    Format: Float as string (e.g., "1.5" for 1.5 seconds)
    Range: 0.1-5.0 seconds
    """
    
    def __init__(self, config_handler):
        """
        Initialize wave speed characteristic.
        
        Args:
            config_handler: BLEConfigHandler instance for validation/updates
        """
        Characteristic.__init__(self, {
            'uuid': '12345678-1234-5678-1234-56789abcdef4',
            'properties': ['read', 'write'],
            'value': None
        })
        self._handler = config_handler
    
    def onReadRequest(self, offset, callback):
        """
        Handle read request for wave speed.
        
        Args:
            offset: Byte offset (must be 0)
            callback: Callback function(result_code, data)
        """
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG, None)
        else:
            try:
                wave_speed = self._handler.get_wave_speed()
                wave_speed_str = str(wave_speed)
                data = string_to_bytes(wave_speed_str)
                callback(Characteristic.RESULT_SUCCESS, data)
            except Exception as e:
                logging.exception(f"Wave speed read error: {e}")
                callback(Characteristic.RESULT_UNLIKELY_ERROR, None)
    
    def onWriteRequest(self, data, offset, withoutResponse, callback):
        """
        Handle write request for wave speed.
        
        Args:
            data: Byte array containing float as string
            offset: Byte offset (must be 0)
            withoutResponse: Whether response is needed
            callback: Callback function(result_code)
        """
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG)
        else:
            try:
                wave_speed_str = bytes_to_string(data)
                error_code = self._handler.update_wave_speed(wave_speed_str)
                
                if error_code == 0:
                    callback(Characteristic.RESULT_SUCCESS)
                else:
                    callback(0x80 + error_code)
            except Exception as e:
                logging.exception(f"Wave speed write error: {e}")
                callback(Characteristic.RESULT_UNLIKELY_ERROR)
