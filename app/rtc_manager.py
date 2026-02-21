"""Real-Time Clock (RTC) manager for offline time synchronization.

Supports DS3231/DS1307 RTC modules for maintaining accurate time
when internet/NTP is unavailable. Critical for tide calculations.
"""

import subprocess
import logging
import os
from datetime import datetime
from typing import Optional, Tuple


class RTCManager:
    """
    Manages hardware RTC (Real-Time Clock) synchronization.
    
    Features:
    - Read/write system time
    - Sync to/from hardware RTC
    - Detect RTC availability
    - Boot-time synchronization
    """
    
    def __init__(self):
        """Initialize RTC manager."""
        self._rtc_available = self._detect_rtc()
        
        if self._rtc_available:
            logging.info("[RTC] Hardware RTC detected")
        else:
            logging.info("[RTC] No hardware RTC detected (NTP required)")
    
    def _detect_rtc(self) -> bool:
        """
        Detect if RTC hardware is available.
        
        Checks for /dev/rtc0 device file.
        
        Returns:
            True if RTC is available, False otherwise
        """
        return os.path.exists('/dev/rtc0')
    
    def is_available(self) -> bool:
        """Check if RTC hardware is available."""
        return self._rtc_available
    
    def get_system_time(self) -> datetime:
        """
        Get current system time.
        
        Returns:
            Current system datetime
        """
        return datetime.now()
    
    def get_system_time_iso(self) -> str:
        """
        Get current system time in ISO 8601 format.
        
        Returns:
            ISO 8601 formatted string (e.g., "2026-02-21T14:30:00")
        """
        return datetime.now().isoformat()
    
    def set_system_time(self, iso_time: str) -> Tuple[bool, str]:
        """
        Set system time from ISO 8601 string.
        
        Args:
            iso_time: Time in ISO 8601 format (e.g., "2026-02-21T14:30:00")
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Parse ISO time
            dt = datetime.fromisoformat(iso_time)
            
            # Format for 'date' command: "YYYY-MM-DD HH:MM:SS"
            time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            
            # Set system time using 'date' command (requires sudo)
            result = subprocess.run(
                ['sudo', 'date', '-s', time_str],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                logging.info(f"[RTC] System time set to: {time_str}")
                return (True, "")
            else:
                error_msg = result.stderr.strip() or "Unknown error"
                logging.error(f"[RTC] Failed to set system time: {error_msg}")
                return (False, error_msg)
                
        except ValueError as e:
            error_msg = f"Invalid time format: {e}"
            logging.error(f"[RTC] {error_msg}")
            return (False, error_msg)
        except subprocess.TimeoutExpired:
            error_msg = "Command timeout"
            logging.error(f"[RTC] {error_msg}")
            return (False, error_msg)
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            logging.error(f"[RTC] {error_msg}")
            return (False, error_msg)
    
    def sync_system_to_rtc(self) -> Tuple[bool, str]:
        """
        Sync current system time to hardware RTC.
        
        Call this after setting system time via NTP or BLE
        to persist the time in hardware.
        
        Returns:
            Tuple of (success, error_message)
        """
        if not self._rtc_available:
            return (False, "RTC hardware not available")
        
        try:
            # Write system time to RTC using hwclock
            result = subprocess.run(
                ['sudo', 'hwclock', '--systohc'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                logging.info("[RTC] System time synced to hardware RTC")
                return (True, "")
            else:
                error_msg = result.stderr.strip() or "Unknown error"
                logging.error(f"[RTC] Failed to sync to RTC: {error_msg}")
                return (False, error_msg)
                
        except subprocess.TimeoutExpired:
            error_msg = "Command timeout"
            logging.error(f"[RTC] {error_msg}")
            return (False, error_msg)
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            logging.error(f"[RTC] {error_msg}")
            return (False, error_msg)
    
    def sync_rtc_to_system(self) -> Tuple[bool, str]:
        """
        Sync hardware RTC time to system time.
        
        Call this at boot to restore time from RTC
        when NTP is unavailable.
        
        Returns:
            Tuple of (success, error_message)
        """
        if not self._rtc_available:
            return (False, "RTC hardware not available")
        
        try:
            # Read RTC time and set system time using hwclock
            result = subprocess.run(
                ['sudo', 'hwclock', '--hctosys'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                logging.info("[RTC] Hardware RTC synced to system time")
                return (True, "")
            else:
                error_msg = result.stderr.strip() or "Unknown error"
                logging.error(f"[RTC] Failed to sync from RTC: {error_msg}")
                return (False, error_msg)
                
        except subprocess.TimeoutExpired:
            error_msg = "Command timeout"
            logging.error(f"[RTC] {error_msg}")
            return (False, error_msg)
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            logging.error(f"[RTC] {error_msg}")
            return (False, error_msg)
    
    def get_rtc_time(self) -> Optional[datetime]:
        """
        Read time directly from hardware RTC.
        
        Returns:
            Datetime from RTC, or None if unavailable/error
        """
        if not self._rtc_available:
            return None
        
        try:
            result = subprocess.run(
                ['sudo', 'hwclock', '--show'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                # Parse output (format varies, but usually parseable)
                time_str = result.stdout.strip()
                # Try to parse with multiple formats
                for fmt in ['%Y-%m-%d %H:%M:%S', '%a %b %d %H:%M:%S %Y']:
                    try:
                        return datetime.strptime(time_str, fmt)
                    except ValueError:
                        continue
                
                logging.warning(f"[RTC] Could not parse RTC time: {time_str}")
                return None
            else:
                logging.error(f"[RTC] Failed to read RTC: {result.stderr}")
                return None
                
        except Exception as e:
            logging.error(f"[RTC] Error reading RTC: {e}")
            return None
    
    def get_status(self) -> dict:
        """
        Get RTC status for diagnostics.
        
        Returns:
            Status dictionary with availability and current times
        """
        status = {
            "rtc_available": self._rtc_available,
            "system_time": self.get_system_time_iso()
        }
        
        if self._rtc_available:
            rtc_time = self.get_rtc_time()
            status["rtc_time"] = rtc_time.isoformat() if rtc_time else None
            
            # Calculate drift if both times available
            if rtc_time:
                drift_seconds = (self.get_system_time() - rtc_time).total_seconds()
                status["drift_seconds"] = drift_seconds
        
        return status
