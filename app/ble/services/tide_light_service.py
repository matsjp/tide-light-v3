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
    """
    
    def __init__(self, config_handler, status_provider):
        """
        Initialize Tide Light service with all characteristics.
        
        Args:
            config_handler: BLEConfigHandler instance
            status_provider: BLEStatusProvider instance
        """
        BlenoPrimaryService.__init__(self, {
            'uuid': '12345678-1234-5678-1234-56789abcdef0',
            'characteristics': [
                LocationCharacteristic(config_handler),
                BrightnessCharacteristic(config_handler),
                PatternCharacteristic(config_handler),
                WaveSpeedCharacteristic(config_handler),
                LEDCountCharacteristic(config_handler),
                LEDInvertCharacteristic(config_handler),
                FullConfigCharacteristic(config_handler),
                StatusCharacteristic(status_provider),
                ErrorCharacteristic(config_handler),
            ]
        })
