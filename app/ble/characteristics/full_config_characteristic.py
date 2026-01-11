"""
Full Config Characteristic for Tide Light.

Handles complete configuration as a JSON string.
UUID: 12345678-1234-5678-1234-56789abcdef7
Properties: Read, Write
"""

import logging
from pybleno import Characteristic
from ble.ble_data_utils import json_to_bytes, bytes_to_json


class FullConfigCharacteristic(Characteristic):
    """
    Characteristic for complete configuration.
    
    Format: JSON string containing all configuration
    """
    
    def __init__(self, config_handler):
        """
        Initialize full config characteristic.
        
        Args:
            config_handler: BLEConfigHandler instance for validation/updates
        """
        Characteristic.__init__(self, {
            'uuid': '12345678-1234-5678-1234-56789abcdef7',
            'properties': ['read', 'write'],
            'value': None
        })
        self._handler = config_handler
    
    def onReadRequest(self, offset, callback):
        """
        Handle read request for full config.
        
        Args:
            offset: Byte offset (must be 0)
            callback: Callback function(result_code, data)
        """
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG, None)
        else:
            try:
                config_json = self._handler.get_full_config()
                data = json_to_bytes(config_json)
                callback(Characteristic.RESULT_SUCCESS, data)
            except Exception as e:
                logging.exception(f"Full config read error: {e}")
                callback(Characteristic.RESULT_UNLIKELY_ERROR, None)
    
    def onWriteRequest(self, data, offset, withoutResponse, callback):
        """
        Handle write request for full config.
        
        Args:
            data: Byte array containing JSON string
            offset: Byte offset (must be 0)
            withoutResponse: Whether response is needed
            callback: Callback function(result_code)
        """
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG)
        else:
            try:
                config_json = bytes_to_json(data)
                error_code = self._handler.update_full_config(config_json)
                
                if error_code == 0:
                    callback(Characteristic.RESULT_SUCCESS)
                else:
                    callback(0x80 + error_code)
            except Exception as e:
                logging.exception(f"Full config write error: {e}")
                callback(Characteristic.RESULT_UNLIKELY_ERROR)
