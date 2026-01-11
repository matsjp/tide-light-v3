"""
BLE characteristic definitions, UUIDs, and constants for Tide Light.

Defines the GATT service structure:
- Service UUID
- Characteristic UUIDs  
- Error codes
- Data format helpers
"""

# -----------------------------
# Service and Characteristic UUIDs
# -----------------------------

# Main service UUID
SERVICE_UUID = "12345678-1234-5678-1234-56789abcdef0"
SERVICE_NAME = "Tide Light Config"

# Characteristic UUIDs
CHAR_LOCATION_UUID = "12345678-1234-5678-1234-56789abcdef1"
CHAR_BRIGHTNESS_UUID = "12345678-1234-5678-1234-56789abcdef2"
CHAR_PATTERN_UUID = "12345678-1234-5678-1234-56789abcdef3"
CHAR_WAVE_SPEED_UUID = "12345678-1234-5678-1234-56789abcdef4"
CHAR_LED_COUNT_UUID = "12345678-1234-5678-1234-56789abcdef5"
CHAR_LED_INVERT_UUID = "12345678-1234-5678-1234-56789abcdef6"
CHAR_FULL_CONFIG_UUID = "12345678-1234-5678-1234-56789abcdef7"
CHAR_STATUS_UUID = "12345678-1234-5678-1234-56789abcdef8"
CHAR_ERROR_UUID = "12345678-1234-5678-1234-56789abcdef9"

# -----------------------------
# Error Codes
# -----------------------------

BLE_ERROR_NONE = 0
BLE_ERROR_INVALID_FORMAT = 1
BLE_ERROR_OUT_OF_RANGE = 2
BLE_ERROR_INVALID_VALUE = 3
BLE_ERROR_INTERNAL = 4

ERROR_MESSAGES = {
    BLE_ERROR_NONE: "Success",
    BLE_ERROR_INVALID_FORMAT: "Invalid format",
    BLE_ERROR_OUT_OF_RANGE: "Value out of range",
    BLE_ERROR_INVALID_VALUE: "Invalid value",
    BLE_ERROR_INTERNAL: "Internal error"
}

# -----------------------------
# Characteristic Metadata
# -----------------------------

CHARACTERISTICS = {
    "location": {
        "uuid": CHAR_LOCATION_UUID,
        "name": "Tide Location",
        "format": "string",
        "example": "59.908559,10.73451",
        "description": "Comma-separated latitude,longitude"
    },
    "brightness": {
        "uuid": CHAR_BRIGHTNESS_UUID,
        "name": "LED Brightness",
        "format": "uint8",
        "range": "0-255",
        "description": "LED strip brightness level"
    },
    "pattern": {
        "uuid": CHAR_PATTERN_UUID,
        "name": "LED Pattern",
        "format": "string",
        "values": ["none", "wave"],
        "description": "LED animation pattern"
    },
    "wave_speed": {
        "uuid": CHAR_WAVE_SPEED_UUID,
        "name": "Wave Speed",
        "format": "float_string",
        "example": "0.5",
        "description": "Wave animation speed in seconds per step"
    },
    "led_count": {
        "uuid": CHAR_LED_COUNT_UUID,
        "name": "LED Count",
        "format": "uint8",
        "range": "1-255",
        "description": "Number of LEDs in strip"
    },
    "led_invert": {
        "uuid": CHAR_LED_INVERT_UUID,
        "name": "LED Invert",
        "format": "bool_uint8",
        "values": [0, 1],
        "description": "Invert LED strip orientation"
    },
    "full_config": {
        "uuid": CHAR_FULL_CONFIG_UUID,
        "name": "Full Config JSON",
        "format": "json_string",
        "description": "Complete configuration as JSON"
    },
    "status": {
        "uuid": CHAR_STATUS_UUID,
        "name": "Status",
        "format": "json_string",
        "readonly": True,
        "description": "Current tide state and system status"
    },
    "error": {
        "uuid": CHAR_ERROR_UUID,
        "name": "Error Code",
        "format": "uint8",
        "readonly": True,
        "description": "Last error code (0 = success)"
    }
}

# -----------------------------
# Constants
# -----------------------------

# Latitude/Longitude valid ranges
LAT_MIN = -90.0
LAT_MAX = 90.0
LON_MIN = -180.0
LON_MAX = 180.0

# Brightness range
BRIGHTNESS_MIN = 0
BRIGHTNESS_MAX = 255

# LED count range
LED_COUNT_MIN = 3  # Minimum: top, bottom, and at least 1 middle
LED_COUNT_MAX = 255

# Valid pattern values
VALID_PATTERNS = ["none", "wave"]

# Wave speed range (seconds per step)
WAVE_SPEED_MIN = 0.1
WAVE_SPEED_MAX = 5.0
