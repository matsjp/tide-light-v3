# BLE Configuration Interface

Complete BLE GATT server implementation for Tide Light configuration with mock support for local testing.

## Overview

The BLE subsystem allows runtime configuration of the Tide Light via Bluetooth Low Energy. It supports both real hardware (Raspberry Pi with bluezero) and mock mode (file watcher) for development.

### Key Features

- ✅ **No BLE imports when mocked** - Lazy loading prevents unnecessary dependencies
- ✅ **File watcher for local testing** - Edit config.json to trigger updates
- ✅ **All config parameters exposed** - Full control via BLE
- ✅ **Status reporting** - Real-time tide state information
- ✅ **Error codes** - Clear feedback on invalid inputs
- ✅ **Thread-safe** - BLE runs in separate thread

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    main.py                          │
│  ┌──────────────────────────────────────────────┐   │
│  │  BLEManager (ble/ble_manager.py)             │   │
│  │  - Factory/dispatcher                        │   │
│  │  - Creates real or mock server               │   │
│  └──────────────────────────────────────────────┘   │
│       │                                              │
│       ├──────────────────┬───────────────────────┐   │
│       ▼                  ▼                       ▼   │
│  ┌────────────┐   ┌──────────────┐   ┌──────────┐   │
│  │BLEServer   │   │ConfigHandler │   │StatusProv│   │
│  │(bluezero)  │   │(validation)  │   │(tide info│   │
│  └────────────┘   └──────────────┘   └──────────┘   │
│       OR                                             │
│  ┌────────────┐                                      │
│  │BLEMockServ │                                      │
│  │(file watch)│                                      │
│  └────────────┘                                      │
└─────────────────────────────────────────────────────┘
```

---

## Module Structure

```
ble/
├── __init__.py              # Module exports (BLEManager only)
├── ble_manager.py           # Factory - creates real or mock server
├── ble_server.py            # Real BLE GATT server (bluezero)
├── ble_mock_server.py       # File watcher mock for testing
├── ble_config_handler.py    # Validation and config updates
├── ble_status_provider.py   # Tide state status provider
└── ble_characteristics.py   # UUIDs, constants, error codes
```

---

## Configuration

Set in `config.json`:

```json
{
  "bluetooth": {
    "use_fake_library": true,    // true = mock (file watcher), false = real (bluezero)
    "device_name": "Tide Light"  // BLE advertising name (not used in mock)
  }
}
```

---

## Mock Mode (Local Testing)

### How It Works

When `use_fake_library: true`:
1. BLE Manager creates `BLEMockServer`
2. Mock server watches `config.json` with `watchdog` library
3. File changes trigger debounced updates (500ms)
4. Updates applied via `ConfigManager.update_config()`
5. Existing listener system propagates changes

### Testing Mock Mode

1. **Run application:**
   ```bash
   python main.py
   ```

2. **Edit config.json manually:**
   ```json
   {
     "led_strip": {
       "brightness": 100  // Change from 50 to 100
     }
   }
   ```

3. **Observe:**
   ```
   [BLE Mock] Config file changed, reading...
   [BLE Mock] Applying config update from file watcher
   Configuration updated:
     LED brightness: 100
   [BLE Mock] Config update applied successfully
   ```

4. **LEDs update immediately** - No restart required

### Test Script

Run `test_ble_mock.py` for automated testing:
```bash
python test_ble_mock.py
```

Tests:
- ✅ File watcher initialization
- ✅ Brightness change detection
- ✅ Pattern change detection
- ✅ Config restoration
- ✅ No infinite loops

---

## Real Mode (Raspberry Pi)

### Prerequisites

1. **Install bluezero:**
   ```bash
   pip install bluezero
   ```

2. **Verify BlueZ version:**
   ```bash
   bluetoothctl --version
   # Should be >= 5.55
   ```

3. **Configure D-Bus permissions:**

   Create `/etc/dbus-1/system.d/tide-light-ble.conf`:
   ```xml
   <!DOCTYPE busconfig PUBLIC "-//freedesktop//DTD D-BUS Bus Configuration 1.0//EN"
    "http://www.freedesktop.org/standards/dbus/1.0/busconfig.dtd">
   <busconfig>
     <policy user="pi">
       <allow own="org.bluez.TideLight"/>
       <allow send_destination="org.bluez"/>
       <allow send_interface="org.bluez.GattManager1"/>
       <allow send_interface="org.bluez.GattService1"/>
       <allow send_interface="org.bluez.GattCharacteristic1"/>
       <allow send_interface="org.freedesktop.DBus.ObjectManager"/>
       <allow send_interface="org.freedesktop.DBus.Properties"/>
     </policy>
   </busconfig>
   ```

   Replace `"pi"` with your username.

4. **Restart services:**
   ```bash
   sudo systemctl restart dbus
   sudo systemctl restart bluetooth
   ```

5. **Enable BLE advertising:**
   ```bash
   sudo hciconfig hci0 up
   hciconfig hci0  # Should show "UP RUNNING"
   ```

### Usage

1. **Set config:**
   ```json
   {
     "bluetooth": {
       "use_fake_library": false
     }
   }
   ```

2. **Run application:**
   ```bash
   python main.py
   ```

3. **Connect with BLE client:**
   - Use nRF Connect (mobile app)
   - Use LightBlue (iOS/macOS)
   - Scan for "Tide Light"

---

## BLE Service Structure

### Service

- **Name:** Tide Light Config
- **UUID:** `12345678-1234-5678-1234-56789abcdef0`

### Characteristics

| Name | UUID | Type | Format | Description |
|------|------|------|--------|-------------|
| Tide Location | ...def1 | R/W | String | `"lat,lon"` e.g. `"59.908559,10.73451"` |
| LED Brightness | ...def2 | R/W | Uint8 | 0-255 |
| LED Pattern | ...def3 | R/W | String | `"none"` or `"wave"` |
| Wave Speed | ...def4 | R/W | String | Float as string, e.g. `"0.5"` |
| LED Count | ...def5 | R/W | Uint8 | 3-255 |
| LED Invert | ...def6 | R/W | Uint8 | 0 (false) or 1 (true) |
| Full Config | ...def7 | R/W | String | Full JSON config |
| Status | ...def8 | R/NOTIFY | String | JSON tide state (notifies every 10s) |
| Error Code | ...def9 | R | Uint8 | Last error (0 = success) |

### Error Codes

| Code | Name | Description |
|------|------|-------------|
| 0 | `BLE_ERROR_NONE` | Success |
| 1 | `BLE_ERROR_INVALID_FORMAT` | Invalid data format |
| 2 | `BLE_ERROR_OUT_OF_RANGE` | Value out of valid range |
| 3 | `BLE_ERROR_INVALID_VALUE` | Invalid value (e.g., unknown pattern) |
| 4 | `BLE_ERROR_INTERNAL` | Internal error |

---

## Status Characteristic Format

JSON format with tide state, cache info, and system metrics:

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

If no tide data available:
```json
{
  "tide": {
    "available": false,
    "reason": "No tide data available"
  },
  "cache": {...},
  "system": {...}
}
```

---

## Usage Examples

### nRF Connect (Mobile App)

1. **Scan for devices** → Find "Tide Light"
2. **Connect**
3. **Discover services** → Select "Tide Light Config"
4. **Read brightness:**
   - Tap "LED Brightness" → Read → Shows current value
5. **Write brightness:**
   - Tap "LED Brightness" → Write → Enter `100` → Send
   - LEDs update immediately
6. **Subscribe to status:**
   - Tap "Status" → Enable Notifications
   - Receives updates every 10 seconds

### Python Example (if writing a custom client)

```python
from bluezero import central

# Scan for device
devices = central.Scanner().discover()
tide_light = [d for d in devices if d.name == "Tide Light"][0]

# Connect
tide_light.connect()

# Read brightness
brightness_char = tide_light.get_characteristic("...def2")
brightness = brightness_char.read_value()[0]
print(f"Current brightness: {brightness}")

# Write brightness
brightness_char.write_value([100])
print("Brightness set to 100")

# Read status
status_char = tide_light.get_characteristic("...def8")
status_json = bytes(status_char.read_value()).decode('utf-8')
print(f"Status: {status_json}")
```

---

## Validation Rules

### Location
- Format: `"latitude,longitude"`
- Latitude: -90.0 to 90.0
- Longitude: -180.0 to 180.0
- Example: `"59.908559,10.73451"`

### Brightness
- Range: 0-255
- Type: Unsigned 8-bit integer

### Pattern
- Values: `"none"` or `"wave"`
- Case-insensitive

### Wave Speed
- Range: 0.1 to 5.0 seconds
- Format: Float as string
- Example: `"0.5"`

### LED Count
- Range: 3-255
- Minimum 3 (top, bottom, 1 middle)

### LED Invert
- Values: 0 (false) or 1 (true)

---

## Troubleshooting

### Mock Mode

**Problem:** File changes not detected

**Solutions:**
- Check `"use_fake_library": true` in config
- Verify file watcher started (look for `[BLE Mock] Watching...` log)
- Ensure config.json is valid JSON
- Try larger changes (e.g., brightness 50 → 100)

**Problem:** Infinite loop (constant updates)

**Solution:** Check for `_updating` flag in mock server - should prevent loops

---

### Real Mode (Pi)

**Problem:** `ImportError: No module named 'bluezero'`

**Solution:**
```bash
pip install bluezero
```

**Problem:** `org.freedesktop.DBus.Error.AccessDenied`

**Solutions:**
- Verify D-Bus config exists: `/etc/dbus-1/system.d/tide-light-ble.conf`
- Check username in config matches your user
- Restart D-Bus: `sudo systemctl restart dbus bluetooth`

**Problem:** Device not advertising

**Solutions:**
```bash
# Check Bluetooth status
sudo systemctl status bluetooth

# Enable HCI interface
sudo hciconfig hci0 up

# Check for errors
journalctl -u bluetooth -f
```

**Problem:** Connection drops frequently

**Solutions:**
- Check BlueZ version: `bluetoothctl --version` (need >= 5.55)
- Update firmware: `sudo rpi-update`
- Check power supply (undervoltage can cause BT issues)

---

## Development Notes

### Adding New Characteristics

1. **Add UUID to `ble_characteristics.py`:**
   ```python
   CHAR_MY_PARAM_UUID = "12345678-1234-5678-1234-56789abcdefA"
   ```

2. **Add validation to `ble_config_handler.py`:**
   ```python
   def validate_my_param(self, value: str) -> Tuple[bool, int, Optional[Any]]:
       # Validation logic
       return (True, BLE_ERROR_NONE, parsed_value)
   
   def update_my_param(self, value: str) -> int:
       # Update logic
       pass
   ```

3. **Add characteristic to `ble_server.py`:**
   ```python
   self._peripheral.add_characteristic(
       srv_id=1, chr_id=10,
       uuid=CHAR_MY_PARAM_UUID,
       value=[], notifying=False,
       flags=['read', 'write'],
       read_callback=self._read_my_param,
       write_callback=self._write_my_param
   )
   ```

4. **Update documentation**

### Testing Changes

1. Test in mock mode first
2. Use `test_ble_mock.py` as template
3. Deploy to Pi for real BLE testing
4. Test with nRF Connect app

---

## Dependencies

### Mock Mode
- `watchdog` - File system event monitoring

### Real Mode (Pi Only)
- `bluezero` - BlueZ D-Bus interface wrapper
- `dbus-python` - Python D-Bus bindings (installed with bluezero)
- BlueZ >= 5.55 (system package)

### Install All
```bash
pip install -r requirements.txt
```

---

## Performance Notes

### Mock Mode
- **CPU Usage:** Minimal (file watcher is event-driven)
- **Debounce:** 500ms prevents rapid-fire updates
- **Overhead:** ~1-2 MB RAM for watchdog

### Real Mode
- **CPU Usage:** ~2-5% on Pi 3B+ (GLib main loop)
- **RAM:** ~10-15 MB for BLE stack
- **Notifications:** 10-second interval for status updates
- **Power:** Minimal impact on Pi power consumption

---

## Security Considerations

### Current Implementation
- **No authentication** - Any BLE client can connect
- **No encryption** - Data transmitted in plaintext
- **No pairing** - Open access

### Recommendations for Production
1. Implement BLE pairing/bonding
2. Add passkey authentication
3. Enable encrypted characteristics
4. Implement access control lists

**Note:** Current implementation prioritizes ease of use for development. Add security for production deployments.

---

## Future Enhancements

### Potential Additions
- [ ] BLE pairing/security
- [ ] Custom client app (mobile)
- [ ] OTA firmware updates via BLE
- [ ] Historical tide data via BLE
- [ ] Scheduled configuration changes
- [ ] BLE mesh support for multiple devices

---

## References

- [BlueZ Documentation](https://github.com/bluez/bluez/blob/master/doc/)
- [Bluezero GitHub](https://github.com/ukBaz/python-bluezero)
- [Watchdog Documentation](https://python-watchdog.readthedocs.io/)
- [GATT Specification](https://www.bluetooth.com/specifications/gatt/)

---

## Summary

The BLE configuration interface provides:
- ✅ **Easy local testing** with file watcher mock
- ✅ **Full remote control** via BLE on Raspberry Pi
- ✅ **Real-time status** with tide state information
- ✅ **Robust validation** with clear error codes
- ✅ **No restart required** for config changes
- ✅ **Thread-safe** concurrent operation

**Quick Start:**
```bash
# Local testing
python test_ble_mock.py

# Or run full app
python main.py
# Edit config.json → LEDs update!
```
