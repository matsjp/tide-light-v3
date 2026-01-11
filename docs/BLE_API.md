# BLE API Reference

Complete specification for Tide Light Bluetooth Low Energy (BLE) GATT service and characteristics.

## Service Overview

**Service Name**: Tide Light Config  
**Service UUID**: `12345678-1234-5678-1234-56789abcdef0`

The Tide Light BLE service provides runtime configuration of the LED visualization system. All configuration parameters are exposed as GATT characteristics with read/write or read-only access.

## Quick Reference Table

| Characteristic | UUID (last digit) | Type | Access | Format | Example |
|----------------|-------------------|------|--------|--------|---------|
| Tide Location | ...def1 | String | R/W | `"lat,lon"` | `"59.908559,10.73451"` |
| LED Brightness | ...def2 | Uint8 | R/W | 0-255 | `128` |
| LED Pattern | ...def3 | String | R/W | enum | `"wave"` |
| Wave Speed | ...def4 | String | R/W | float | `"0.5"` |
| LED Count | ...def5 | Uint8 | R/W | 3-255 | `30` |
| LED Invert | ...def6 | Uint8 | R/W | 0/1 | `0` |
| Full Config | ...def7 | String | R/W | JSON | (see below) |
| Status | ...def8 | String | R/NOTIFY | JSON | (see below) |
| Error Code | ...def9 | Uint8 | R | 0-4 | `0` |

## Characteristic Details

### 1. Tide Location

**UUID**: `12345678-1234-5678-1234-56789abcdef1`  
**Access**: Read, Write  
**Format**: UTF-8 String

**Description**: Geographic coordinates for tide data fetching.

**Write Format**:
```
"latitude,longitude"
```

**Validation**:
- Latitude: -90.0 to 90.0 (decimal degrees)
- Longitude: -180.0 to 180.0 (decimal degrees)
- Must be comma-separated
- Leading/trailing whitespace trimmed

**Examples**:
```
Valid:
"59.908559,10.73451"    // Oslo, Norway
"51.507351,-0.127758"   // London, UK
"-33.865143,151.209900" // Sydney, Australia

Invalid:
"91.0,0.0"              // Latitude out of range
"59.908559"             // Missing longitude
"abc,def"               // Not numeric
```

**Read Format**:
```
"59.908559,10.73451"
```

**Error Codes**:
- `1` (INVALID_FORMAT) - Not in "lat,lon" format
- `2` (OUT_OF_RANGE) - Coordinates outside valid range
- `4` (INTERNAL) - Failed to update configuration

**Side Effects**:
- Triggers cache invalidation
- Fetches new tide data from Kartverket API
- LEDs update within 1 second

---

### 2. LED Brightness

**UUID**: `12345678-1234-5678-1234-56789abcdef2`  
**Access**: Read, Write  
**Format**: Unsigned 8-bit integer (Uint8)

**Description**: Overall LED strip brightness.

**Range**: 0-255
- `0` = LEDs off
- `255` = Maximum brightness

**Default**: `128` (50% brightness)

**Examples**:
```
Valid:
0       // Off
64      // 25%
128     // 50%
192     // 75%
255     // 100%

Invalid:
256     // Out of range
-1      // Negative value
```

**Error Codes**:
- `2` (OUT_OF_RANGE) - Value not in 0-255 range

**Side Effects**:
- Applies immediately to LED strip
- No restart required

**Notes**:
- Lower brightness saves power
- Recommended: 50-150 for indoor use
- Maximum brightness can be visually uncomfortable

---

### 3. LED Pattern

**UUID**: `12345678-1234-5678-1234-56789abcdef3`  
**Access**: Read, Write  
**Format**: UTF-8 String

**Description**: Animation pattern for LED visualization.

**Valid Values**:
- `"none"` - Solid colors (no animation)
- `"wave"` - Animated wave effect

**Default**: `"wave"`

**Examples**:
```
Valid:
"none"
"wave"
"NONE"   // Case-insensitive
"Wave"

Invalid:
"pulse"  // Unknown pattern
"fade"   // Not implemented
""       // Empty string
```

**Error Codes**:
- `3` (INVALID_VALUE) - Unknown pattern name

**Side Effects**:
- Changes apply on next visualization loop (~100ms)
- Wave direction follows tide direction (rising/falling)

**Pattern Descriptions**:

**"none"** (Solid):
- Static colors
- No moving effects
- Lower CPU usage
- Good for debugging

**"wave"** (Animated):
- 3-LED wave travels through middle LEDs
- Direction matches tide (up when rising, down when falling)
- Speed controlled by Wave Speed characteristic
- Wave wraps continuously

---

### 4. Wave Speed

**UUID**: `12345678-1234-5678-1234-56789abcdef4`  
**Access**: Read, Write  
**Format**: UTF-8 String (float representation)

**Description**: Speed of wave animation in seconds per LED step.

**Range**: 0.1 to 5.0 seconds
- `0.1` = Very fast (1 LED every 0.1s)
- `5.0` = Very slow (1 LED every 5s)

**Default**: `0.5` (1 LED every 0.5 seconds)

**Write Format**:
```
"0.5"
```

**Examples**:
```
Valid:
"0.1"     // Fast wave
"0.5"     // Default
"1.0"     // Slow wave
"2.5"     // Very slow

Invalid:
"0.05"    // Too fast (< 0.1)
"10.0"    // Too slow (> 5.0)
"abc"     // Not a number
```

**Error Codes**:
- `1` (INVALID_FORMAT) - Not a valid float
- `2` (OUT_OF_RANGE) - Value outside 0.1-5.0 range

**Side Effects**:
- Applies immediately to wave animation
- Only relevant when pattern is "wave"

**Notes**:
- Lower values increase CPU usage slightly
- Recommended: 0.3-1.0 for good visual effect
- Values >2.0 may appear static

---

### 5. LED Count

**UUID**: `12345678-1234-5678-1234-56789abcdef5`  
**Access**: Read, Write  
**Format**: Unsigned 8-bit integer (Uint8)

**Description**: Number of LEDs in the strip.

**Range**: 3-255
- Minimum 3 (top, bottom, 1 middle)
- Maximum 255 (hardware limit)

**Default**: `30`

**Examples**:
```
Valid:
3       // Minimum
30      // Common
60      // Common
150     // Maximum tested

Invalid:
2       // Too few
256     // Out of uint8 range
0       // Invalid
```

**Error Codes**:
- `2` (OUT_OF_RANGE) - Value not in 3-255 range

**Side Effects**:
- Recalculates LED positions
- Applies immediately
- Ensure physical LED count matches configuration

**LED Allocation**:
```
Total LEDs: N
- Top LED: 1 (direction indicator)
- Bottom LED: 1 (direction indicator)
- Middle LEDs: N-2 (tide progress)
  - Always-blue LED: 1
  - Dynamic LEDs: N-3
```

**Notes**:
- Must match actual hardware LED count
- Higher counts provide smoother visualization
- Power consumption scales with count (~60mA per LED)

---

### 6. LED Invert

**UUID**: `12345678-1234-5678-1234-56789abcdef6`  
**Access**: Read, Write  
**Format**: Unsigned 8-bit integer (Uint8)

**Description**: Flip LED strip orientation.

**Values**:
- `0` = Standard orientation (LED 0 = top)
- `1` = Inverted orientation (LED 0 = bottom)

**Default**: `0` (standard)

**Orientation Diagram**:

```
Standard (invert = 0):
┌─────────┐
│ LED 0   │ ← Top (direction indicator)
│ LED 1   │ ↑
│ LED 2   │ │ Middle LEDs (tide progress)
│  ...    │ ↓
│ LED N-1 │ ← Bottom (direction indicator)
└─────────┘

Inverted (invert = 1):
┌─────────┐
│ LED N-1 │ ← Top (direction indicator)
│ LED N-2 │ ↑
│ LED N-3 │ │ Middle LEDs (tide progress)
│  ...    │ ↓
│ LED 0   │ ← Bottom (direction indicator)
└─────────┘
```

**Examples**:
```
Valid:
0       // Standard
1       // Inverted

Invalid:
2       // Unknown value
255     // Not boolean
```

**Error Codes**:
- `3` (INVALID_VALUE) - Value not 0 or 1

**Side Effects**:
- Recalculates all LED positions
- Applies immediately

**Use Cases**:
- LED strip installed upside down
- Data input at bottom instead of top
- Aesthetic preference

---

### 7. Full Config

**UUID**: `12345678-1234-5678-1234-56789abcdef7`  
**Access**: Read, Write  
**Format**: UTF-8 String (JSON)

**Description**: Complete configuration as JSON object. Allows atomic updates of multiple parameters.

**Read Format**:
```json
{
  "location": {
    "latitude": 59.908559,
    "longitude": 10.73451
  },
  "led_strip": {
    "count": 30,
    "brightness": 128,
    "invert": false
  },
  "color": {
    "pattern": "wave",
    "wave_speed": 0.5
  },
  "bluetooth": {
    "use_fake_library": false,
    "device_name": "Tide Light"
  },
  "use_mock": false
}
```

**Write Format**:
Same as read format. Can be partial (missing fields use current values).

**Partial Update Example**:
```json
{
  "led_strip": {
    "brightness": 200
  }
}
```

**Error Codes**:
- `1` (INVALID_FORMAT) - Invalid JSON syntax
- `3` (INVALID_VALUE) - Invalid configuration values
- `4` (INTERNAL) - Failed to apply configuration

**Side Effects**:
- All changed parameters apply according to their individual rules
- Atomic operation (all or nothing)

**Notes**:
- Useful for backup/restore
- Prefer individual characteristics for single-parameter updates
- Large payload (may require fragmented BLE writes)

---

### 8. Status

**UUID**: `12345678-1234-5678-1234-56789abcdef8`  
**Access**: Read, Notify  
**Format**: UTF-8 String (JSON)

**Description**: Real-time system status including tide state, cache info, and metrics.

**Notification Interval**: 10 seconds

**Read/Notify Format**:

**With Tide Data Available**:
```json
{
  "tide": {
    "available": true,
    "direction": "rising",
    "progress": 0.652,
    "next_event": {
      "time": "2026-01-10T18:30:00",
      "flag": "high"
    },
    "last_event": {
      "time": "2026-01-10T12:15:00",
      "flag": "low"
    }
  },
  "cache": {
    "has_data": true,
    "latitude": 59.908559,
    "longitude": 10.73451
  },
  "system": {
    "uptime_seconds": 3600,
    "last_update": "2026-01-10T15:30:00"
  }
}
```

**Without Tide Data**:
```json
{
  "tide": {
    "available": false,
    "reason": "No tide data available"
  },
  "cache": {
    "has_data": false,
    "latitude": null,
    "longitude": null
  },
  "system": {
    "uptime_seconds": 120,
    "last_update": "2026-01-10T15:00:00"
  }
}
```

**Field Descriptions**:

| Field | Type | Description |
|-------|------|-------------|
| `tide.available` | boolean | Whether tide data is available |
| `tide.direction` | string | `"rising"` or `"falling"` |
| `tide.progress` | float | Progress from last to next event (0.0-1.0) |
| `tide.next_event.time` | string | ISO 8601 timestamp of next tide event |
| `tide.next_event.flag` | string | `"high"` or `"low"` |
| `tide.last_event.time` | string | ISO 8601 timestamp of previous tide event |
| `tide.last_event.flag` | string | `"high"` or `"low"` |
| `tide.reason` | string | Error message if unavailable |
| `cache.has_data` | boolean | Whether cache contains data |
| `cache.latitude` | float/null | Cached location latitude |
| `cache.longitude` | float/null | Cached location longitude |
| `system.uptime_seconds` | integer | Time since app started (seconds) |
| `system.last_update` | string | ISO 8601 timestamp of last status update |

**Usage**:
```javascript
// Subscribe to notifications (Web Bluetooth API)
await characteristic.startNotifications();
characteristic.addEventListener('characteristicvaluechanged', (event) => {
  const status = JSON.parse(decoder.decode(event.target.value));
  console.log('Tide Direction:', status.tide.direction);
  console.log('Progress:', (status.tide.progress * 100).toFixed(1) + '%');
});
```

**Notes**:
- Read-only (write attempts return error)
- Updates automatically every 10 seconds
- Large payload (~200-300 bytes)
- JSON parsing required client-side

---

### 9. Error Code

**UUID**: `12345678-1234-5678-1234-56789abcdef9`  
**Access**: Read  
**Format**: Unsigned 8-bit integer (Uint8)

**Description**: Last error code from write operations.

**Values**:

| Code | Name | Description |
|------|------|-------------|
| 0 | `BLE_ERROR_NONE` | Success (no error) |
| 1 | `BLE_ERROR_INVALID_FORMAT` | Invalid data format or syntax |
| 2 | `BLE_ERROR_OUT_OF_RANGE` | Value outside valid range |
| 3 | `BLE_ERROR_INVALID_VALUE` | Invalid value (e.g., unknown enum) |
| 4 | `BLE_ERROR_INTERNAL` | Internal server error |

**Read Format**:
```
0
```

**Usage Pattern**:
```python
# Write a characteristic
write_characteristic(BRIGHTNESS_UUID, bytes([200]))

# Check for errors
error_code = read_characteristic(ERROR_UUID)
if error_code != 0:
    print(f"Error: {error_code}")
```

**Notes**:
- Resets to 0 on successful write
- Persists until next write operation
- Check after each write for validation feedback

---

## Error Codes Reference

### 0 - BLE_ERROR_NONE
**Meaning**: Success, no error  
**Action**: None

### 1 - BLE_ERROR_INVALID_FORMAT
**Meaning**: Data format is invalid  
**Examples**:
- Location missing comma: `"59.908559"`
- Wave speed not numeric: `"abc"`
- Full config invalid JSON: `{invalid}`

**Action**: Check data format and retry

### 2 - BLE_ERROR_OUT_OF_RANGE
**Meaning**: Value outside valid range  
**Examples**:
- Brightness > 255
- Latitude > 90.0
- Wave speed < 0.1 or > 5.0
- LED count < 3

**Action**: Check validation ranges and retry

### 3 - BLE_ERROR_INVALID_VALUE
**Meaning**: Value not in allowed set  
**Examples**:
- Pattern: `"pulse"` (not "none" or "wave")
- LED Invert: `2` (not 0 or 1)

**Action**: Use valid enum value

### 4 - BLE_ERROR_INTERNAL
**Meaning**: Internal server error  
**Examples**:
- Failed to update config.json
- Database write error
- Exception during processing

**Action**: Check server logs, retry operation

---

## Usage Examples

### Python (bluezero)

```python
from bluezero import central

# Connect to device
devices = central.Scanner().discover()
tide_light = [d for d in devices if d.name == "Tide Light"][0]
tide_light.connect()

# Read brightness
brightness_char = tide_light.get_characteristic("12345678-1234-5678-1234-56789abcdef2")
brightness = brightness_char.read_value()[0]
print(f"Current brightness: {brightness}")

# Write brightness
brightness_char.write_value([200])

# Check error
error_char = tide_light.get_characteristic("12345678-1234-5678-1234-56789abcdef9")
error_code = error_char.read_value()[0]
if error_code != 0:
    print(f"Error: {error_code}")
```

### JavaScript (Web Bluetooth API)

```javascript
// Connect to device
const device = await navigator.bluetooth.requestDevice({
  filters: [{ name: 'Tide Light' }],
  optionalServices: ['12345678-1234-5678-1234-56789abcdef0']
});

const server = await device.gatt.connect();
const service = await server.getPrimaryService('12345678-1234-5678-1234-56789abcdef0');

// Read location
const locationChar = await service.getCharacteristic('12345678-1234-5678-1234-56789abcdef1');
const locationData = await locationChar.readValue();
const location = new TextDecoder().decode(locationData);
console.log('Location:', location);

// Write location
const newLocation = new TextEncoder().encode('59.908559,10.73451');
await locationChar.writeValue(newLocation);

// Subscribe to status
const statusChar = await service.getCharacteristic('12345678-1234-5678-1234-56789abcdef8');
await statusChar.startNotifications();
statusChar.addEventListener('characteristicvaluechanged', (event) => {
  const status = JSON.parse(new TextDecoder().decode(event.target.value));
  console.log('Tide Direction:', status.tide.direction);
});
```

### nRF Connect (Mobile App)

1. **Scan and Connect**:
   - Open nRF Connect
   - Scan for devices
   - Select "Tide Light"
   - Tap "Connect"

2. **Read Characteristic**:
   - Expand "Tide Light Config" service
   - Tap "LED Brightness" characteristic
   - Tap ↓ (download icon) to read
   - Value displayed in decimal/hex

3. **Write Characteristic**:
   - Tap "LED Brightness"
   - Tap ↑ (upload icon) to write
   - Select "UINT8"
   - Enter value (e.g., `200`)
   - Tap "Send"

4. **Subscribe to Notifications**:
   - Tap "Status" characteristic
   - Tap 🔔 (bell icon) to enable notifications
   - Notifications appear every 10 seconds

---

## Implementation Notes

### Thread Safety
All BLE operations are thread-safe. The BLE server runs in a separate thread from the main visualization loop.

### Performance
- Read operations: ~10-50ms
- Write operations: ~50-100ms + processing time
- Notifications: 10-second interval (low overhead)

### Power Consumption
- BLE advertising: ~10mA
- Active connection: ~15mA
- Negligible impact on overall system power

### Range
- Typical BLE range: 10-30 meters (open space)
- Walls reduce range significantly
- Use BLE extenders for longer range

### Compatibility
- BLE 4.0+ required
- GATT server mode required
- Tested with:
  - nRF Connect (Android/iOS)
  - LightBlue (iOS/macOS)
  - Web Bluetooth API (Chrome/Edge)

---

## Troubleshooting

### Cannot Connect
- Check device is powered on
- Verify BLE is enabled on client
- Ensure device is advertising (check Python logs)
- Try restarting Bluetooth on both sides

### Write Fails
- Check error code characteristic for details
- Verify value is in valid range/format
- Ensure characteristic supports write operation
- Check Python logs for exceptions

### Notifications Not Received
- Verify notifications are enabled (`startNotifications()`)
- Check connection is still active
- Verify Python app is running
- Check 10-second update interval

### Invalid Data Format
- Check examples in this document
- Verify string encoding (UTF-8)
- Check byte order (little-endian for integers)
- Use hexadecimal view in BLE tools for debugging

---

## Version History

- **v1.0** - Initial BLE implementation
  - Basic characteristics (location, brightness, pattern)
  - Status reporting
  - Error codes

- **v2.0** - Enhanced configuration
  - Added wave speed control
  - Added LED count configuration
  - Added LED invert flag
  - Full config characteristic

- **v3.0** - Web interface support
  - Improved status JSON format
  - Better error messages
  - localStorage persistence in web client

---

## References

- [Bluetooth GATT Specification](https://www.bluetooth.com/specifications/gatt/)
- [Web Bluetooth API](https://webbluetoothcg.github.io/web-bluetooth/)
- [Bluezero Documentation](https://github.com/ukBaz/python-bluezero)
- [nRF Connect](https://www.nordicsemi.com/Products/Development-tools/nrf-connect-for-mobile)

---

**See Also**:
- [Python App Documentation](../app/README.md) - BLE server implementation
- [Web Interface Documentation](../web/README.md) - Web Bluetooth client
- [BLE Implementation Details](BLE_README.md) - Architecture and testing
