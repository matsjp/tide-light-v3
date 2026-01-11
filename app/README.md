# Tide Light - Python Application

Python application that visualizes Norwegian tide data on a WS281x LED strip running on Raspberry Pi.

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Hardware Setup](#hardware-setup)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [API Reference](#api-reference)

## Features

- Real-time tide visualization on WS281x LED strip
- Fetches tide data from Kartverket API (Norwegian Mapping Authority)
- SQLite cache for offline operation
- Bluetooth Low Energy (BLE) configuration interface
- Mock mode for development without hardware
- Runtime configuration updates (no restart required)
- Animated wave pattern option
- Configurable brightness, LED count, and orientation

## Requirements

### Hardware (Production)
- Raspberry Pi (any model with GPIO and Bluetooth)
- WS281x LED strip (WS2811, WS2812, WS2812B, etc.)
- 5V power supply (rated for LED strip)
- Jumper wires
- Optional: Logic level shifter (3.3V → 5V)

### Software
- Python 3.7 or newer
- Raspbian/Raspberry Pi OS (for production)
- Internet connection (for tide data fetching)

### Development (Optional)
- Any OS (Windows, macOS, Linux) with Python 3.7+
- Mock libraries for LED and BLE simulation

## Installation

### 1. Clone Repository

```bash
cd ~
git clone https://github.com/yourusername/tide-light-v3.git
cd tide-light-v3/app
```

### 2. Install Dependencies

#### Production (Raspberry Pi with real hardware)

```bash
pip install -r requirements.txt
pip install rpi_ws281x
pip install bluezero
```

#### Development (Mock mode - any OS)

```bash
pip install -r requirements.txt
pip install rpi-ws281x-mock
pip install watchdog
```

**Note**: Cannot install both `rpi_ws281x` and `rpi-ws281x-mock` simultaneously. They both provide the `rpi_ws281x` module.

### 3. Configure Application

Edit `config.json` to match your setup:

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

For development, set:
```json
{
  "use_mock": true,
  "bluetooth": {
    "use_fake_library": true
  }
}
```

### 4. (Production Only) Configure Bluetooth Permissions

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

Replace `"pi"` with your username, then restart services:

```bash
sudo systemctl restart dbus
sudo systemctl restart bluetooth
```

## Configuration

### Configuration File: `config.json`

#### Location Settings

```json
{
  "location": {
    "latitude": 59.908559,   // Decimal degrees (-90 to 90)
    "longitude": 10.73451    // Decimal degrees (-180 to 180)
  }
}
```

Validate your location has tide data at: https://vannstand.kartverket.no/tideapi.php

#### LED Strip Settings

```json
{
  "led_strip": {
    "count": 30,        // Number of LEDs (minimum 3)
    "brightness": 128,  // Brightness 0-255
    "invert": false     // Flip orientation (true/false)
  }
}
```

**LED Layout:**
- Top LED: Tide direction indicator (rising = green)
- Middle LEDs: Tide progress visualization
- Bottom LED: Tide direction indicator (falling = red)

**Invert Flag:**
- `false`: LED 0 = top, LED (count-1) = bottom
- `true`: LED 0 = bottom, LED (count-1) = top

#### Color Settings

```json
{
  "color": {
    "pattern": "wave",    // "none" or "wave"
    "wave_speed": 0.5     // Seconds per LED step (0.1-5.0)
  }
}
```

**Patterns:**
- `"none"`: Solid colors (static)
- `"wave"`: Animated wave effect traveling up/down

#### Bluetooth Settings

```json
{
  "bluetooth": {
    "use_fake_library": false,  // true = file watcher mock, false = real BLE
    "device_name": "Tide Light" // BLE advertising name
  }
}
```

#### System Settings

```json
{
  "use_mock": false  // true = LED mock (console output), false = real LEDs
}
```

### Configuration Methods

1. **Direct File Edit**: Edit `config.json` manually (requires restart or BLE mock mode)
2. **BLE Client**: Use nRF Connect or LightBlue app to configure via Bluetooth
3. **Web Interface**: Use the web configuration tool (see [`../web/README.md`](../web/README.md))

## Usage

### Running the Application

```bash
cd app
python main.py
```

**Expected Output:**

```
[ConfigManager] Configuration loaded successfully
[TideFetcher] Fetching waterlevels for location (59.908559, 10.73451)
[TideFetcher] Successfully fetched 1234 waterlevels
[TideCacheManager] Inserted 1234 waterlevels for location (59.908559, 10.73451)
[TideUpdateScheduler] Initial tide data fetch complete
[BLE Manager] Starting BLE server (mode: real)
[TideVisualizer] Starting tide visualization...
[TideVisualizer] Tide Direction: RISING, Progress: 45.2%
```

### Running as System Service

Create `/etc/systemd/system/tide-light.service`:

```ini
[Unit]
Description=Tide Light Visualization
After=network.target bluetooth.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/tide-light-v3/app
ExecStart=/usr/bin/python3 /home/pi/tide-light-v3/app/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable tide-light
sudo systemctl start tide-light
```

Check status:

```bash
sudo systemctl status tide-light
sudo journalctl -u tide-light -f  # Follow logs
```

### Mock Mode (Development)

Set in `config.json`:

```json
{
  "use_mock": true,
  "bluetooth": {
    "use_fake_library": true
  }
}
```

Then run:

```bash
python main.py
```

**Mock Mode Features:**
- Console output instead of LED hardware
- File watcher instead of BLE server
- Edit `config.json` → changes apply automatically
- No Raspberry Pi or hardware required

## Hardware Setup

### Wiring Diagram

```
Raspberry Pi          WS281x LED Strip
┌──────────┐         ┌──────────────┐
│          │         │              │
│  GPIO 18 ├────────►│ Data In (DI) │
│          │         │              │
│      GND ├────────►│ Ground (GND) │
│          │         │              │
│          │         │ +5V ◄────────┼──── External 5V Power Supply
│      GND ├─────────┴──────────────┘     (GND connected to Pi GND)
└──────────┘
```

**Important Notes:**

1. **Power Supply**: DO NOT power LED strip from Raspberry Pi 5V pin
   - Use external 5V power supply rated for LED current
   - Connect power supply GND to Raspberry Pi GND (common ground)
   - Calculate power: ~60mA per LED at full white brightness
   - Example: 30 LEDs × 60mA = 1.8A minimum

2. **GPIO Pin**: GPIO 18 (Pin 12) - PWM-capable pin required
   - Do not change without updating `light_controller.py`

3. **Logic Level**: WS281x expects 5V logic, Pi outputs 3.3V
   - Usually works without level shifter for short cables
   - For reliability, use 74AHCT125 or similar level shifter

4. **Strip Orientation**: Note which end is "input" (arrows on strip)
   - Connect to input end (DI or Data In)
   - Use `invert` flag in config if needed

### LED Strip Compatibility

Tested and compatible:
- WS2811
- WS2812
- WS2812B
- SK6812

Not compatible:
- APA102 (different protocol)
- Analog RGB strips (require different driver)

## Testing

### Run Unit Tests

```bash
cd app
python -m unittest discover tests
```

### Run Specific Test

```bash
# Test tide calculator
python -m unittest tests.tide_calculator_test

# Test scheduler
python -m unittest tests.tide_scheduler_test

# Test specific method
python -m unittest tests.tide_calculator_test.TestTideCalculator.test_calculate_rising_tide
```

### Test BLE Mock

```bash
python test_ble_mock.py
```

This tests file watcher functionality without needing BLE hardware.

## Troubleshooting

### Application Won't Start

**Problem**: `ModuleNotFoundError: No module named 'kartverket_tide_api'`

**Solution**:
```bash
pip install -r requirements.txt
```

---

**Problem**: `ImportError: No module named 'rpi_ws281x'`

**Solution**: Install LED library
```bash
# For real hardware:
pip install rpi_ws281x

# For mock/development:
pip install rpi-ws281x-mock
```

---

**Problem**: `PermissionError: [Errno 13] Permission denied: '/dev/mem'`

**Solution**: Run with sudo or add user to gpio group
```bash
# Option 1: Run with sudo
sudo python main.py

# Option 2: Add user to gpio group
sudo usermod -a -G gpio pi
# Log out and back in
```

### No Tide Data

**Problem**: `[TideFetcher] No tide data available for location`

**Solutions**:
1. Verify location has tide data: https://vannstand.kartverket.no/tideapi.php
2. Check internet connection: `ping 8.8.8.8`
3. Try different coordinates (closer to coast)
4. Check API status: `curl "https://vannstand.kartverket.no/tideapi.php?lat=59.908559&lon=10.73451&fromtime=2024-01-01T00:00&totime=2024-01-02T00:00&datatype=all&refcode=cd&place=&file=&lang=en&interval=10&dst=0&tzone=0&tide_request=locationdata"`

---

**Problem**: LEDs blink red (error state)

**Reasons**:
- No cached tide data for current location
- Unable to fetch data from API
- Database query failed

**Solutions**:
1. Check internet connection
2. Delete cache: `rm tide_cache.db` (will re-fetch on startup)
3. Review logs for error messages
4. Verify location is valid

### BLE Not Working

**Problem**: `org.freedesktop.DBus.Error.AccessDenied`

**Solution**: Configure D-Bus permissions (see [Installation](#installation))

---

**Problem**: Device not advertising

**Solutions**:
```bash
# Check Bluetooth status
sudo systemctl status bluetooth

# Enable HCI interface
sudo hciconfig hci0 up

# Verify BlueZ version (need >= 5.55)
bluetoothctl --version
```

---

**Problem**: Cannot connect from phone

**Solutions**:
1. Ensure `use_fake_library: false` in config
2. Restart Bluetooth: `sudo systemctl restart bluetooth`
3. Check Python logs for BLE errors
4. Try different BLE app (nRF Connect, LightBlue)

### LED Strip Issues

**Problem**: LEDs not lighting up

**Solutions**:
1. Check wiring (GPIO 18, GND, 5V power)
2. Verify power supply is adequate and connected
3. Set brightness to max: `"brightness": 255`
4. Test with mock mode first: `"use_mock": true`
5. Verify LED count matches config

---

**Problem**: Wrong colors or random flickering

**Solutions**:
1. Check common ground between Pi and power supply
2. Add level shifter (3.3V → 5V)
3. Shorten data cable
4. Add 470Ω resistor on data line
5. Add 1000µF capacitor across power supply

---

**Problem**: LEDs in wrong order (upside down)

**Solution**: Set `"invert": true` in config

---

**Problem**: Only first LED works

**Solutions**:
1. Check if LED strip is damaged
2. Verify you're connected to input end (DI)
3. Test with different section of strip

### Configuration Issues

**Problem**: Changes not applying

**Solutions**:
1. Verify `config.json` is valid JSON (use `jsonlint`)
2. Check file permissions: `ls -la config.json`
3. For file edits, restart app or use BLE mock mode
4. Use BLE or web interface for runtime updates

---

**Problem**: `JSONDecodeError: Expecting property name`

**Solution**: Fix JSON syntax
```bash
# Validate JSON
python -c "import json; json.load(open('config.json'))"
```

Common issues:
- Trailing comma in last item
- Missing quotes around strings
- Single quotes instead of double quotes

### Performance Issues

**Problem**: High CPU usage

**Solutions**:
1. Increase `wave_speed` (slower animation)
2. Use `"pattern": "none"` (disable animation)
3. Reduce LED count
4. Check for stuck threads: `top -H -p $(pgrep -f main.py)`

---

**Problem**: Delayed updates

**Solutions**:
1. Check network latency to Kartverket API
2. Verify cache is working: `ls -lh tide_cache.db`
3. Review scheduler logs for fetch times

## API Reference

### Main Components

#### `TideVisualizer`
Main visualization controller

```python
from tide_visualizer import TideVisualizer

visualizer = TideVisualizer(config_manager, tide_calculator, light_controller)
visualizer.start()  # Start visualization loop
visualizer.stop()   # Stop gracefully
```

#### `TideCalculator`
Calculate current tide state

```python
from tide_calculator import TideCalculator

calculator = TideCalculator(cache_manager)
state = calculator.calculate_tide_state()

if state:
    print(f"Direction: {state.direction}")
    print(f"Progress: {state.progress * 100:.1f}%")
```

#### `TideCacheManager`
Manage SQLite cache

```python
from tide_cache_manager import TideCacheManager

cache = TideCacheManager("tide_cache.db")
waterlevels = cache.get_waterlevels_in_range(start_time, end_time)
cache.insert_waterlevels(waterlevels, lat, lon)
```

#### `ConfigManager`
Manage configuration

```python
from config_manager import ConfigManager

config = ConfigManager("config.json")
config.register_listener(on_config_change)
config.update_config({"led_strip": {"brightness": 200}})
```

#### `LightController`
Control LED strip

```python
from light_controller import LightController

controller = LightController(led_count=30, brightness=128, invert=False, use_mock=False)
controller.update_leds(colors)  # colors = [(r, g, b), ...]
controller.set_brightness(200)
controller.cleanup()
```

### BLE Characteristics

See [BLE API Reference](../docs/BLE_API.md) for complete BLE characteristic specification.

**Quick Reference:**

| Characteristic | UUID | Type | Format |
|----------------|------|------|--------|
| Location | ...def1 | R/W | "lat,lon" |
| Brightness | ...def2 | R/W | 0-255 |
| Pattern | ...def3 | R/W | "none"/"wave" |
| Wave Speed | ...def4 | R/W | "0.5" (float as string) |
| LED Count | ...def5 | R/W | 3-255 |
| LED Invert | ...def6 | R/W | 0/1 |
| Status | ...def8 | R/NOTIFY | JSON |
| Error Code | ...def9 | R | 0-4 |

## Files Overview

```
app/
├── main.py                      # Application entry point
├── config.json                  # Configuration file
├── requirements.txt             # Python dependencies
│
├── config_manager.py            # Configuration management
├── tide_fetcher.py             # Kartverket API client
├── tide_parser.py              # XML parsing
├── tide_models.py              # Data models
├── tide_cache_manager.py       # SQLite cache
├── tide_calculator.py          # Tide state calculation
├── tide_update_scheduler.py    # Periodic data updates
├── tide_visualizer.py          # Main visualization loop
├── light_controller.py         # LED strip control
├── gpio_manager.py             # GPIO cleanup
├── led_mock_visualizer.py      # Console mock for LEDs
│
├── ble/                        # BLE subsystem
│   ├── __init__.py
│   ├── ble_manager.py          # BLE factory
│   ├── ble_server.py           # Real BLE server
│   ├── ble_mock_server.py      # File watcher mock
│   ├── ble_config_handler.py   # Validation
│   ├── ble_status_provider.py  # Status reporting
│   └── ble_characteristics.py  # UUIDs and constants
│
└── tests/                      # Unit tests
    ├── tide_calculator_test.py
    └── tide_scheduler_test.py
```

## Resources

- [Kartverket Tide API](https://www.kartverket.no/en/at-sea/se-havniva)
- [rpi_ws281x Library](https://github.com/jgarff/rpi_ws281x)
- [Bluezero Documentation](https://github.com/ukBaz/python-bluezero)
- [WS281x LED Guide](https://learn.adafruit.com/adafruit-neopixel-uberguide)
- [Raspberry Pi GPIO Pinout](https://pinout.xyz/)

## Next Steps

- Configure via web interface: See [`../web/README.md`](../web/README.md)
- Deploy as system service for automatic startup
- Set up log rotation: `sudo nano /etc/logrotate.d/tide-light`
- Monitor with: `sudo journalctl -u tide-light -f`

---

**Need help?** Check the [main documentation](../README.md) or [troubleshooting guide](#troubleshooting).
