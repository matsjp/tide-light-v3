"""
Tide Light Service for Pybleno.

Primary GATT service containing all Tide Light characteristics.
"""

from pybleno import BlenoPrimaryService
from ble.characteristics import (
    LocationCharacteristic,
    BrightnessCharacteristic,
    PatternCharacteristic,
    WaveSpeedCharacteristic,
    LEDCountCharacteristic,
    LEDInvertCharacteristic,
    FullConfigCharacteristic,
    StatusCharacteristic,
    ErrorCharacteristic,
)
from ble.characteristics.wifi_networks_characteristic import WiFiNetworksCharacteristic
from ble.characteristics.wifi_ssid_characteristic import WiFiSsidCharacteristic
from ble.characteristics.wifi_password_characteristic import WiFiPasswordCharacteristic
from ble.characteristics.wifi_status_characteristic import WiFiStatusCharacteristic
from ble.characteristics.ldr_active_characteristic import LdrActiveCharacteristic
from ble.characteristics.system_time_characteristic import SystemTimeCharacteristic
from ble.characteristics.reset_characteristic import ResetCharacteristic


class TideLightService(BlenoPrimaryService):
    """
    Primary GATT service for Tide Light configuration.
    
    UUID: 12345678-1234-5678-1234-56789abcdef0
    Characteristics:
    - Location (lat,lon)
    - Brightness (0-255)
    - Pattern (none/wave)
    - Wave Speed (0.1-5.0)
    - LED Count (3-255)
    - LED Invert (0/1)
    - Full Config (JSON)
    - Status (JSON, notify)
    - Error Code (0-4)
    - WiFi Networks (JSON array)
    - WiFi SSID (write)
    - WiFi Password (write)
    - WiFi Status (JSON, notify)
    - LDR Active (0/1)
    - System Time (ISO 8601 string)
    - Reset (write-only trigger)
    """
    
    def __init__(self, config_handler, status_provider, config_manager=None, wifi_handler=None, rtc_manager=None):
        """
        Initialize Tide Light service with all characteristics.
        
        Args:
            config_handler: BLEConfigHandler instance
            status_provider: BLEStatusProvider instance
            config_manager: ConfigManager instance (optional, for reset)
            wifi_handler: WiFiHandler instance (optional)
            rtc_manager: RTCManager instance (optional)
        """
        characteristics = [
            LocationCharacteristic(config_handler),
            BrightnessCharacteristic(config_handler),
            PatternCharacteristic(config_handler),
            WaveSpeedCharacteristic(config_handler),
            LEDCountCharacteristic(config_handler),
            LEDInvertCharacteristic(config_handler),
            FullConfigCharacteristic(config_handler),
            StatusCharacteristic(status_provider),
            ErrorCharacteristic(config_handler),
            LdrActiveCharacteristic(config_handler),
        ]
        
        # Add RTC characteristic if RTC manager provided
        if rtc_manager:
            characteristics.append(SystemTimeCharacteristic(rtc_manager))
        
        # Add Reset characteristic if config manager provided
        if config_manager:
            characteristics.append(ResetCharacteristic(config_manager))
        
        # Always add WiFi characteristics (handler reports unavailable if no hardware)
        # This ensures web interface can show WiFi section and communicate unavailability
        if wifi_handler:
            wifi_status_char = WiFiStatusCharacteristic(wifi_handler)
            wifi_handler.set_status_characteristic(wifi_status_char)
            
            characteristics.extend([
                WiFiNetworksCharacteristic(wifi_handler),
                WiFiSsidCharacteristic(wifi_handler),
                WiFiPasswordCharacteristic(wifi_handler),
                wifi_status_char,
            ])
        
        BlenoPrimaryService.__init__(self, {
            'uuid': '12345678-1234-5678-1234-56789abcdef0',
            'characteristics': characteristics
        })
