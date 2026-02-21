"""
Reset Characteristic for Tide Light.

Handles factory reset functionality as a write-only characteristic.
Writing 0x01 triggers a factory reset, restoring default configuration.
UUID: 12345678-1234-5678-1234-56789abcdf00
Properties: Write only
"""

import logging
from pybleno import Characteristic
from ble.ble_data_utils import bytes_to_uint8


class ResetCharacteristic(Characteristic):
    """
    Write-only characteristic for factory reset.
    
    Format: uint8 (0x01 = trigger reset)
    Writing any value triggers reset to defaults.
    """
    
    def __init__(self, config_manager):
        """
        Initialize reset characteristic.
        
        Args:
            config_manager: ConfigManager instance for reset operation
        """
        Characteristic.__init__(self, {
            'uuid': '12345678-1234-5678-1234-56789abcdf00',
            'properties': ['write'],
            'value': None
        })
        self._config_manager = config_manager
    
    def onWriteRequest(self, data, offset, withoutResponse, callback):
        """
        Handle write request for factory reset.
        
        Args:
            data: Byte array containing trigger value
            offset: Byte offset (must be 0)
            withoutResponse: Whether response is needed
            callback: Callback function(result_code)
        """
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG)
        else:
            try:
                value = bytes_to_uint8(data)
                
                # Any non-zero value triggers reset
                if value != 0:
                    logging.warning("Factory reset triggered via BLE")
                    self._config_manager.reset_to_defaults()
                    logging.info("Factory reset completed successfully")
                    callback(Characteristic.RESULT_SUCCESS)
                else:
                    # Writing 0 is a no-op
                    callback(Characteristic.RESULT_SUCCESS)
            except Exception as e:
                logging.exception(f"Factory reset error: {e}")
                callback(Characteristic.RESULT_UNLIKELY_ERROR)
