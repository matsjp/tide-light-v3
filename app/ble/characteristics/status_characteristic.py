"""
Status Characteristic for Tide Light.

Provides system status as JSON string.
UUID: 12345678-1234-5678-1234-56789abcdef8
Properties: Read
"""

import logging
from pybleno import Characteristic


class StatusCharacteristic(Characteristic):
    """
    Characteristic for system status (read-only).
    
    Format: JSON string containing:
    - tide: dict with direction, progress, events, availability
    - cache: dict with location and data availability
    - system: dict with uptime and last update time
    
    Web client polls this characteristic periodically.
    """
    
    def __init__(self, status_provider):
        """
        Initialize status characteristic.
        
        Args:
            status_provider: BLEStatusProvider instance
        """
        Characteristic.__init__(self, {
            'uuid': '12345678-1234-5678-1234-56789abcdef8',
            'properties': ['read'],
            'value': None
        })
        self._status_provider = status_provider
        logging.info("[Status Characteristic] Initialized (read-only)")
    
    def onReadRequest(self, offset, callback):
        """
        Handle read request for status.
        
        Args:
            offset: Byte offset (must be 0)
            callback: Callback function(result_code, data)
        """
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG, None)
        else:
            try:
                status_json = self._status_provider.get_status_json()
                # Use .encode('utf-8') directly like System Time characteristic
                data = status_json.encode('utf-8')
                callback(Characteristic.RESULT_SUCCESS, data)
                logging.info(f"[Status Characteristic] Read success ({len(data)} bytes)")
            except Exception as e:
                logging.exception(f"[Status Characteristic] Read error: {e}")
                callback(Characteristic.RESULT_UNLIKELY_ERROR, None)
