"""
Status Characteristic for Tide Light.

Provides system status as JSON string.
UUID: ec08 (expands to 0000ec08-0000-1000-8000-00805f9b34fb)
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
            'uuid': 'ec08',
            'properties': ['read'],
            'value': None
        })
        self._status_provider = status_provider
    
    def onReadRequest(self, offset, callback):
        """
        Handle read request for status (supports offset-based reads for large JSON).
        
        Args:
            offset: Byte offset for chunked reads
            callback: Callback function(result_code, data)
        """
        try:
            status_json = self._status_provider.get_status_json()
            data = status_json.encode('utf-8')
            
            if offset == 0:
                callback(Characteristic.RESULT_SUCCESS, data)
            elif offset < len(data):
                callback(Characteristic.RESULT_SUCCESS, data[offset:])
            else:
                logging.warning(f"[Status] Offset {offset} beyond data length {len(data)}")
                callback(Characteristic.RESULT_INVALID_OFFSET, None)
        except Exception as e:
            logging.exception(f"Status read error: {e}")
            callback(Characteristic.RESULT_UNLIKELY_ERROR, None)
