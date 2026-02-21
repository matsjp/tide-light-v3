/**
 * BLE Service and Characteristic UUIDs for Tide Light
 * Mirrors Python ble_characteristics.py
 */

// Service UUID
export const SERVICE_UUID = "12345678-1234-5678-1234-56789abcdef0";
export const SERVICE_NAME = "Tide Light Config";

// Characteristic UUIDs
export const CHAR_UUIDS = {
  LOCATION: "12345678-1234-5678-1234-56789abcdef1",
  BRIGHTNESS: "12345678-1234-5678-1234-56789abcdef2",
  PATTERN: "12345678-1234-5678-1234-56789abcdef3",
  WAVE_SPEED: "12345678-1234-5678-1234-56789abcdef4",
  LED_COUNT: "12345678-1234-5678-1234-56789abcdef5",
  LED_INVERT: "12345678-1234-5678-1234-56789abcdef6",
  FULL_CONFIG: "12345678-1234-5678-1234-56789abcdef7",
  STATUS: "12345678-1234-5678-1234-56789abcdef8",
  ERROR: "12345678-1234-5678-1234-56789abcdef9",
  WIFI_NETWORKS: "12345678-1234-5678-1234-56789abcdefa",
  WIFI_SSID: "12345678-1234-5678-1234-56789abcdefb",
  WIFI_PASSWORD: "12345678-1234-5678-1234-56789abcdefc",
  WIFI_STATUS: "12345678-1234-5678-1234-56789abcdefd",
  LDR_ACTIVE: "12345678-1234-5678-1234-56789abcdefe",
  SYSTEM_TIME: "12345678-1234-5678-1234-56789abcdeff",
  RESET: "12345678-1234-5678-1234-56789abcdf00"
};

// Error Codes
export const ERROR_CODES = {
  NONE: 0,
  INVALID_FORMAT: 1,
  OUT_OF_RANGE: 2,
  INVALID_VALUE: 3,
  INTERNAL: 4,
  INVALID_SSID: 5,
  INVALID_PASSWORD: 6,
  CONNECTION_FAILED: 7,
  NO_WIFI_HARDWARE: 8
};

export const ERROR_MESSAGES = {
  [ERROR_CODES.NONE]: "Success",
  [ERROR_CODES.INVALID_FORMAT]: "Invalid format",
  [ERROR_CODES.OUT_OF_RANGE]: "Value out of range",
  [ERROR_CODES.INVALID_VALUE]: "Invalid value",
  [ERROR_CODES.INTERNAL]: "Internal error",
  [ERROR_CODES.INVALID_SSID]: "Invalid SSID",
  [ERROR_CODES.INVALID_PASSWORD]: "Invalid password",
  [ERROR_CODES.CONNECTION_FAILED]: "WiFi connection failed",
  [ERROR_CODES.NO_WIFI_HARDWARE]: "No WiFi hardware"
};

// Validation Constants
export const VALIDATION = {
  LAT_MIN: -90.0,
  LAT_MAX: 90.0,
  LON_MIN: -180.0,
  LON_MAX: 180.0,
  BRIGHTNESS_MIN: 0,
  BRIGHTNESS_MAX: 255,
  LED_COUNT_MIN: 3,
  LED_COUNT_MAX: 255,
  WAVE_SPEED_MIN: 0.1,
  WAVE_SPEED_MAX: 5.0,
  VALID_PATTERNS: ["none", "wave"]
};

// Characteristic Metadata
export const CHAR_METADATA = {
  LOCATION: {
    name: "Tide Location",
    format: "string",
    example: "59.908559,10.73451"
  },
  BRIGHTNESS: {
    name: "LED Brightness",
    format: "uint8",
    range: "0-255"
  },
  PATTERN: {
    name: "LED Pattern",
    format: "string",
    values: ["none", "wave"]
  },
  WAVE_SPEED: {
    name: "Wave Speed",
    format: "float_string",
    example: "0.5"
  },
  LED_COUNT: {
    name: "LED Count",
    format: "uint8",
    range: "3-255"
  },
  LED_INVERT: {
    name: "LED Invert",
    format: "bool_uint8",
    values: [0, 1]
  },
  STATUS: {
    name: "Status",
    format: "json_string",
    readonly: true
  },
  ERROR: {
    name: "Error Code",
    format: "uint8",
    readonly: true
  },
  WIFI_NETWORKS: {
    name: "WiFi Networks",
    format: "json_string",
    readonly: true
  },
  WIFI_SSID: {
    name: "WiFi SSID",
    format: "string",
    readonly: false
  },
  WIFI_PASSWORD: {
    name: "WiFi Password",
    format: "string",
    readonly: false
  },
  WIFI_STATUS: {
    name: "WiFi Status",
    format: "json_string",
    readonly: true
  },
  LDR_ACTIVE: {
    name: "LDR Active",
    format: "bool_uint8",
    values: [0, 1]
  },
  SYSTEM_TIME: {
    name: "System Time",
    format: "iso8601_string",
    example: "2026-02-21T14:30:00",
    readonly: false
  },
  RESET: {
    name: "Factory Reset",
    format: "uint8",
    readonly: false
  }
};
