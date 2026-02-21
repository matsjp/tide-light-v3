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
        logging.info("[Status Characteristic] __init__ called, creating characteristic...")
        Characteristic.__init__(self, {
            'uuid': '12345678-1234-5678-1234-56789abcdef8',
            'properties': ['read'],
            'value': None
        })
        self._status_provider = status_provider
        logging.info("[Status Characteristic] Initialized (read-only)")
        logging.info(f"[Status Characteristic] UUID: {self['uuid']}")
        logging.info(f"[Status Characteristic] Properties: {self['properties']}")
        logging.info(f"[Status Characteristic] Status provider: {status_provider}")
    
    def onReadRequest(self, offset, callback):
        """
        Handle read request for status.
        
        Args:
            offset: Byte offset (must be 0)
            callback: Callback function(result_code, data)
        """
        logging.info(f"[Status Characteristic] onReadRequest called! offset={offset}")
        if offset:
            logging.warning(f"[Status Characteristic] Non-zero offset {offset}, rejecting")
            callback(Characteristic.RESULT_ATTR_NOT_LONG, None)
        else:
            try:
                logging.info("[Status Characteristic] Getting status JSON...")
                status_json = self._status_provider.get_status_json()
                logging.info(f"[Status Characteristic] Status JSON: {status_json[:100]}...")
                
                # Use .encode('utf-8') directly like System Time characteristic
                data = status_json.encode('utf-8')
                logging.info(f"[Status Characteristic] Encoded to {len(data)} bytes")
                
                callback(Characteristic.RESULT_SUCCESS, data)
                logging.info(f"[Status Characteristic] Read success!")
            except Exception as e:
                logging.exception(f"[Status Characteristic] Read error: {e}")
                callback(Characteristic.RESULT_UNLIKELY_ERROR, None)
