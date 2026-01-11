"""
Location Characteristic for Tide Light.

Handles tide location as a "latitude,longitude" string.
UUID: 12345678-1234-5678-1234-56789abcdef1
Properties: Read, Write
"""

import logging
from pybleno import Characteristic
from ble.ble_data_utils import string_to_bytes, bytes_to_string


class LocationCharacteristic(Characteristic):
    """
    Characteristic for tide location (latitude,longitude).
    
    Format: "lat,lon" string (e.g., "59.123,-122.456")
    """
    
    def __init__(self, config_handler):
        """
        Initialize location characteristic.
        
        Args:
            config_handler: BLEConfigHandler instance for validation/updates
        """
        Characteristic.__init__(self, {
            'uuid': '12345678-1234-5678-1234-56789abcdef1',
            'properties': ['read', 'write'],
            'value': None
        })
        self._handler = config_handler
    
    def onReadRequest(self, offset, callback):
        """
        Handle read request for location.
        
        Args:
            offset: Byte offset (must be 0)
            callback: Callback function(result_code, data)
        """
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG, None)
        else:
            try:
                location_str = self._handler.get_location()
                data = string_to_bytes(location_str)
                callback(Characteristic.RESULT_SUCCESS, data)
            except Exception as e:
                logging.exception(f"Location read error: {e}")
                callback(Characteristic.RESULT_UNLIKELY_ERROR, None)
    
    def onWriteRequest(self, data, offset, withoutResponse, callback):
        """
        Handle write request for location.
        
        Args:
            data: Byte array containing "lat,lon" string
            offset: Byte offset (must be 0)
            withoutResponse: Whether response is needed
            callback: Callback function(result_code)
        """
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG)
        else:
            try:
                location_str = bytes_to_string(data)
                error_code = self._handler.update_location(location_str)
                
                if error_code == 0:
                    callback(Characteristic.RESULT_SUCCESS)
                else:
                    # Map error codes to BLE error range (0x80+)
                    callback(0x80 + error_code)
            except Exception as e:
                logging.exception(f"Location write error: {e}")
                callback(Characteristic.RESULT_UNLIKELY_ERROR)
