# Tide Light v3

A Raspberry Pi application that visualizes real-time Norwegian tide data using a WS281x LED strip, with a mobile-friendly web configuration interface.

## Project Structure

This repository is organized into two main components:

```
tide-light-v3/
├── app/                    # Python application (Raspberry Pi)
├── web/                    # Web configuration interface
└── docs/                   # Shared documentation
```

### Components

- **[`app/`](app/README.md)** - Python application that runs on Raspberry Pi
  - Fetches tide data from Kartverket API
  - Controls WS281x LED strip to visualize tide state
  - Provides BLE configuration interface
  - SQLite cache for offline operation

- **[`web/`](web/README.md)** - Web-based configuration interface
  - Mobile-first responsive design
  - Web Bluetooth API for device configuration
  - Interactive map for location selection (Leaflet + OpenStreetMap)
  - Real-time tide data validation via Kartverket API
  - Deploy to Netlify for HTTPS access

- **[`docs/`](docs/)** - Shared documentation
  - [BLE API Reference](docs/BLE_API.md) - BLE characteristics specification
  - [Agent Guidelines](docs/AGENTS.md) - Development guidelines
  - [BLE Implementation](docs/BLE_README.md) - BLE server details

## Quick Start

### Python Application (Raspberry Pi)

```bash
cd app
pip install -r requirements.txt
python main.py
```

See [`app/README.md`](app/README.md) for detailed setup instructions.

### Web Interface (Development)

```bash
cd web
npm install
npm run dev
```

See [`web/README.md`](web/README.md) for deployment and usage instructions.

## Features

### LED Visualization
- Real-time tide direction (rising/falling) indicators
- Progressive tide level display
- Configurable wave animation
- Adjustable brightness and LED count
- Support for inverted LED strips

### Configuration
- **Web Interface**: Mobile-friendly configuration via Web Bluetooth
- **BLE Direct**: Connect with any BLE client (nRF Connect, LightBlue)
- **Local Testing**: File watcher mock for development without BLE hardware

### Data Management
- Automatic tide data fetching from Kartverket API
- SQLite caching for offline operation
- Location validation against available tide stations
- Periodic cache updates (weekly)

### System Features
- No restart required for configuration changes
- Thread-safe concurrent operation
- Status reporting (tide state, cache info, uptime)
- Comprehensive error handling

## Technology Stack

### Python Application
- **Runtime**: Python 3.7+
- **LED Control**: rpi-ws281x / rpi-ws281x-mock
- **BLE**: bluezero (real) / watchdog (mock)
- **API**: kartverket_tide_api
- **Database**: SQLite3
- **Platform**: Raspberry Pi (or any Linux with mock libraries)

### Web Interface
- **Build Tool**: Vite
- **Map**: Leaflet + OpenStreetMap
- **BLE**: Web Bluetooth API
- **Styling**: Vanilla CSS (mobile-first)
- **Deployment**: Netlify
- **Browser Support**: Chrome, Edge (Web Bluetooth required)

## Documentation

- **[Python App Setup](app/README.md)** - Installation, configuration, and usage
- **[Web Interface Guide](web/README.md)** - Development, deployment, and troubleshooting
- **[BLE API Reference](docs/BLE_API.md)** - Complete BLE characteristics specification
- **[BLE Implementation Details](docs/BLE_README.md)** - Server architecture and testing
- **[Development Guidelines](docs/AGENTS.md)** - Code style and patterns

## Hardware Requirements

### Minimum Setup
- Raspberry Pi (any model with GPIO and Bluetooth)
- WS281x-compatible LED strip (WS2811, WS2812, WS2812B, etc.)
- Power supply appropriate for LED strip
- MicroSD card (8GB+)

### Recommended Setup
- Raspberry Pi 3B+ or newer (better Bluetooth performance)
- 30-60 LED strip (adequate visualization detail)
- 5V power supply rated for full LED load
- Level shifter for 5V LED data line (recommended)

See [`app/README.md`](app/README.md) for detailed wiring instructions.

## Configuration Overview

Configuration is stored in `app/config.json`:

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

### Configuration Methods

1. **Web Interface** - User-friendly mobile configuration
2. **BLE Client** - Direct BLE connection (nRF Connect, etc.)
3. **File Edit** - Manual editing of `config.json` (requires restart or BLE mock)

## Use Cases

### Home Display
Mount LED strip in window or wall to show real-time tide information for sailors, kayakers, or beachgoers.

### Marine Applications
Install on boat or dock for instant tide awareness without checking phone.

### Educational
Visualize tide cycles for science education or environmental awareness.

### Remote Monitoring
Configure remotely via web interface when away from physical device.

## Deployment Scenarios

### Scenario 1: Home Use (Simplest)
1. Deploy web interface to Netlify
2. Install Python app on Raspberry Pi at home
3. Configure via phone when at home (local BLE connection)

### Scenario 2: Remote Configuration
1. Deploy web interface to Netlify (HTTPS)
2. Install Python app on Raspberry Pi with internet access
3. Configure from anywhere (BLE range permitting)
4. Use BLE extenders for longer range if needed

### Scenario 3: Offline Installation
1. Install Python app on Raspberry Pi
2. Configure location in `config.json` manually
3. No web interface needed (standalone operation)

## Browser Compatibility

The web interface requires **Web Bluetooth API** support:

- ✅ Chrome (Desktop & Android)
- ✅ Edge (Desktop & Android)
- ❌ Firefox (not supported)
- ❌ Safari (not supported)

For configuration on iOS devices, use a native BLE app like LightBlue instead.

## Development Workflow

### Local Python Development
1. Use mock libraries (`rpi-ws281x-mock`, `watchdog`)
2. Set `"use_mock": true` and `"use_fake_library": true` in config
3. Edit `config.json` to trigger updates
4. Test with `python -m unittest` in `app/` directory

### Web Development
1. Run `npm run dev` in `web/` directory
2. Test UI without BLE hardware (mock connection)
3. Deploy to Netlify for real BLE testing on mobile

### Integration Testing
1. Deploy web interface to Netlify
2. Run Python app on Raspberry Pi
3. Connect from mobile browser (Chrome/Edge)
4. Test full workflow end-to-end

## Troubleshooting

### Python App Won't Start
- Check `requirements.txt` dependencies are installed
- Verify config.json is valid JSON
- Check GPIO permissions on Raspberry Pi
- Review logs for specific errors

### Web Interface Can't Connect
- Ensure browser supports Web Bluetooth (Chrome/Edge)
- Verify HTTPS connection (required for Web Bluetooth)
- Check Raspberry Pi Bluetooth is enabled
- Confirm device is advertising (check Python logs)

### LEDs Not Working
- Verify wiring (GPIO 18, GND, 5V power)
- Check LED count matches `config.json`
- Test with brightness at max (255)
- Try `invert: true` if order is reversed

### No Tide Data
- Check internet connection on Raspberry Pi
- Verify location has tide data (use web validator)
- Check Kartverket API status
- Review cache database: `app/tide_cache.db`

See component-specific READMEs for detailed troubleshooting:
- [Python App Troubleshooting](app/README.md#troubleshooting)
- [Web Interface Troubleshooting](web/README.md#troubleshooting)

## Contributing

This is a personal project, but suggestions and bug reports are welcome via issues.

### Development Guidelines
- Follow code style in [docs/AGENTS.md](docs/AGENTS.md)
- Test on both mock and real hardware
- Update documentation for new features
- Maintain backward compatibility for config.json

## License

MIT License - See LICENSE file for details

## Credits

- **Tide Data**: [Kartverket](https://www.kartverket.no/) - Norwegian Mapping Authority
- **Map Tiles**: [OpenStreetMap](https://www.openstreetmap.org/) contributors
- **LED Library**: [jgarff/rpi_ws281x](https://github.com/jgarff/rpi_ws281x)
- **BLE Library**: [ukBaz/python-bluezero](https://github.com/ukBaz/python-bluezero)

## Resources

- [Kartverket Tide API](https://www.kartverket.no/en/at-sea/se-havniva)
- [Web Bluetooth API Spec](https://webbluetoothcg.github.io/web-bluetooth/)
- [WS281x LED Guide](https://learn.adafruit.com/adafruit-neopixel-uberguide)
- [Raspberry Pi GPIO Pinout](https://pinout.xyz/)

## Version History

- **v3.0** - Complete restructure with web interface
  - Separated Python app and web interface
  - Added Web Bluetooth configuration
  - Mobile-first responsive design
  - Interactive map with location validation

- **v2.0** - BLE support added
  - Bluetooth Low Energy configuration
  - Mock mode for development
  - Status reporting characteristic

- **v1.0** - Initial release
  - Basic LED visualization
  - File-based configuration
  - Kartverket API integration
