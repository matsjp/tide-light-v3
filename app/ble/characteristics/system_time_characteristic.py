"""
System Time Characteristic for Tide Light.

Handles system time read/write in ISO 8601 format for RTC synchronization.
UUID: 12345678-1234-5678-1234-56789abcdeff
Properties: Read, Write
"""

import logging
from pybleno import Characteristic


class SystemTimeCharacteristic(Characteristic):
    """
    Characteristic for system time management via RTC.
    
    Format: UTF-8 string in ISO 8601 format (e.g., "2026-02-21T14:30:00")
    
    Read: Returns current system time
    Write: Sets system time and syncs to RTC if available
    """
    
    def __init__(self, rtc_manager):
        """
        Initialize system time characteristic.
        
        Args:
            rtc_manager: RTCManager instance for time operations
        """
        Characteristic.__init__(self, {
            'uuid': '12345678-1234-5678-1234-56789abcdeff',
            'properties': ['read', 'write'],
            'value': None
        })
        self._rtc = rtc_manager
    
    def onReadRequest(self, offset, callback):
        """
        Handle read request for current system time.
        
        Returns current system time in ISO 8601 format.
        
        Args:
            offset: Byte offset (must be 0)
            callback: Callback function(result_code, data)
        """
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG, None)
        else:
            try:
                iso_time = self._rtc.get_system_time_iso()
                data = iso_time.encode('utf-8')
                callback(Characteristic.RESULT_SUCCESS, data)
                logging.info(f"[BLE] System time read: {iso_time}")
            except Exception as e:
                logging.exception(f"System time read error: {e}")
                callback(Characteristic.RESULT_UNLIKELY_ERROR, None)
    
    def onWriteRequest(self, data, offset, withoutResponse, callback):
        """
        Handle write request for system time.
        
        Sets system time from ISO 8601 string and syncs to RTC if available.
        
        Args:
            data: Byte array containing UTF-8 ISO 8601 time string
            offset: Byte offset (must be 0)
            withoutResponse: Whether response is needed
            callback: Callback function(result_code)
        """
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG)
        else:
            try:
                # Decode ISO time string
                iso_time = data.decode('utf-8').strip()
                logging.info(f"[BLE] Setting system time to: {iso_time}")
                
                # Set system time
                success, error_msg = self._rtc.set_system_time(iso_time)
                
                if not success:
                    logging.error(f"[BLE] Failed to set system time: {error_msg}")
                    callback(Characteristic.RESULT_UNLIKELY_ERROR)
                    return
                
                # Sync to hardware RTC if available
                if self._rtc.is_available():
                    sync_success, sync_error = self._rtc.sync_system_to_rtc()
                    if sync_success:
                        logging.info("[BLE] System time synced to hardware RTC")
                    else:
                        logging.warning(f"[BLE] RTC sync failed: {sync_error}")
                        # Don't fail the whole operation - time was set successfully
                
                callback(Characteristic.RESULT_SUCCESS)
                
            except UnicodeDecodeError as e:
                logging.error(f"[BLE] Invalid UTF-8 in system time: {e}")
                callback(Characteristic.RESULT_UNLIKELY_ERROR)
            except Exception as e:
                logging.exception(f"System time write error: {e}")
                callback(Characteristic.RESULT_UNLIKELY_ERROR)
