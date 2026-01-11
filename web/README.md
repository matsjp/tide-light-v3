# Tide Light - Web Configuration Interface

Mobile-first web application for configuring Tide Light via Web Bluetooth API.

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Development](#development)
- [Deployment](#deployment)
- [Usage](#usage)
- [Architecture](#architecture)
- [Troubleshooting](#troubleshooting)
- [Browser Compatibility](#browser-compatibility)

## Features

- **Web Bluetooth**: Direct device configuration from mobile browser
- **Interactive Map**: Location selection with Leaflet + OpenStreetMap
- **Live Validation**: Real-time tide data availability checking (Kartverket API)
- **Real-time Status**: Subscribe to device status updates via BLE notifications
- **Mobile-First**: Responsive design optimized for phones and tablets
- **Offline-Capable**: Progressive Web App (PWA) ready
- **No Backend**: Pure static site, deploy anywhere

## Requirements

### Browser Support

The Web Bluetooth API is **required** and only supported by:

- ✅ Chrome (Desktop & Android) - Recommended
- ✅ Edge (Desktop & Android)
- ❌ Firefox (not supported)
- ❌ Safari (not supported)

**iOS Users**: Use a native BLE app like [LightBlue](https://apps.apple.com/us/app/lightblue/id557428110) instead.

### Prerequisites

- Node.js 16+ and npm
- Modern browser with Web Bluetooth API
- HTTPS connection (required by Web Bluetooth API)
  - Localhost exempted for development
  - Use Netlify or similar for production

## Installation

```bash
cd web
npm install
```

This installs:
- `vite` - Build tool and dev server
- `leaflet` - Interactive map library

## Development

### Start Dev Server

```bash
npm run dev
```

Opens at `http://localhost:5173`

**Development Features:**
- Hot module replacement (instant updates)
- Source maps for debugging
- Localhost exemption for Web Bluetooth (no HTTPS needed)

### Project Structure

```
web/
├── index.html                      # Main HTML
├── package.json                    # Dependencies
├── vite.config.js                  # Vite configuration
├── netlify.toml                    # Netlify deploy config
│
├── src/
│   ├── css/
│   │   └── main.css               # All styles (mobile-first)
│   │
│   └── js/
│       ├── main.js                # Application controller
│       │
│       ├── ble/
│       │   ├── constants.js       # UUIDs, error codes, validation
│       │   └── ble-manager.js     # Web Bluetooth wrapper
│       │
│       ├── map/
│       │   ├── map-manager.js     # Leaflet wrapper
│       │   └── validator.js       # Kartverket API integration
│       │
│       └── utils/
│           └── notifications.js   # Toast notification system
│
└── dist/                          # Build output (generated)
```

### Development Workflow

1. **Start dev server**: `npm run dev`
2. **Edit files**: Changes reflect instantly
3. **Test in browser**: Open DevTools → Console
4. **Check BLE**: Chrome → `chrome://bluetooth-internals`

### Testing Without Hardware

The web interface can be developed and tested without a real Tide Light device:

1. **UI Testing**: All UI elements render and function
2. **Map Testing**: Location selection and validation work
3. **BLE Mock**: Connection will fail gracefully with error messages

**To test with real device:**
- Run Python app on Raspberry Pi
- Deploy web app to Netlify (HTTPS required)
- Connect from mobile browser

## Deployment

### Deploy to Netlify (Recommended)

#### Option 1: GitHub Integration (Automatic)

1. **Push code to GitHub**:
   ```bash
   git add .
   git commit -m "Add web interface"
   git push
   ```

2. **Connect to Netlify**:
   - Go to [netlify.com](https://www.netlify.com/)
   - Click "Add new site" → "Import from Git"
   - Select your repository
   - Configure build settings:
     - **Base directory**: `web`
     - **Build command**: `npm run build`
     - **Publish directory**: `web/dist`
   - Click "Deploy"

3. **Automatic Deploys**: Every push to `main` triggers rebuild

#### Option 2: Manual Deploy

```bash
# Build production files
npm run build

# Deploy dist/ folder
npm install -g netlify-cli
netlify deploy --prod --dir=dist
```

### Deploy to Other Platforms

#### Vercel

```bash
npm install -g vercel
vercel --prod
```

Configure:
- Root directory: `web`
- Build command: `npm run build`
- Output directory: `dist`

#### GitHub Pages

```bash
npm run build
# Copy dist/ contents to gh-pages branch
```

**Note**: Requires HTTPS custom domain (GitHub Pages uses HTTPS by default)

### Deployment Checklist

- ✅ HTTPS enabled (required for Web Bluetooth)
- ✅ Build completes without errors
- ✅ Test on mobile device (Chrome/Edge)
- ✅ Verify map loads (check OpenStreetMap tiles)
- ✅ Test BLE connection to real device

## Usage

### First-Time Setup

1. **Open Web App**: Navigate to deployed URL (e.g., `https://your-app.netlify.app`)
2. **Check Browser**: Warning banner appears if browser doesn't support Web Bluetooth
3. **Click "Connect to Tide Light"**: Triggers BLE device scan
4. **Select Device**: Choose "Tide Light" from list
5. **Wait for Load**: Configuration loads from device

### Configuring Location

1. **Use Map**:
   - Click "Enable Location Selection"
   - Click on map to place marker
   - Click "Use Current Location" for GPS position

2. **Manual Entry**:
   - Enter latitude and longitude in input fields
   - Click "Validate Location"

3. **Validation**:
   - Green checkmark: Tide data available
   - Red X: No tide data for location
   - Shows station name if available

### Adjusting Settings

All settings update in real-time as you adjust them:

- **Brightness**: Slider (0-255)
- **LED Count**: Number input (3-255)
- **Pattern**: Dropdown (None / Wave)
- **Wave Speed**: Number input (0.1-5.0 seconds)
- **Invert LED Order**: Checkbox

### Applying Changes

1. **Make Changes**: Adjust any configuration settings
2. **Click "Apply Changes"**: Writes all changes to device via BLE
3. **Wait for Confirmation**: Success/error notification appears
4. **LEDs Update**: Changes apply immediately on device (no restart)

### Monitoring Status

The "Device Status" section shows real-time information:

- **Tide State**: Current direction (rising/falling) and progress
- **Next Event**: Time and type of next tide event (high/low)
- **Cache Info**: Cached location coordinates
- **System Metrics**: Uptime and last update time

Status updates automatically every 10 seconds via BLE notifications.

### Disconnecting

- Click "Disconnect" button
- Or close browser tab (connection closes automatically)
- Or device goes out of BLE range

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────┐
│              TideLightApp (main.js)             │
│         Main application controller             │
└─────────────────┬───────────────────────────────┘
                  │
        ┌─────────┼─────────┐
        │         │         │
        ▼         ▼         ▼
   ┌────────┐ ┌──────┐ ┌──────────┐
   │  BLE   │ │ Map  │ │   UI     │
   │Manager │ │Mgr   │ │ Events   │
   └────────┘ └──────┘ └──────────┘
        │         │
        │         ▼
        │    ┌──────────┐
        │    │Validator │
        │    │(Kartverket)
        │    └──────────┘
        │
        ▼
   ┌─────────────┐
   │Web Bluetooth│
   │     API     │
   └─────────────┘
```

### Key Classes

#### **TideLightApp** (`main.js`)
Main application controller that orchestrates all components.

**Responsibilities:**
- Initialize BLE, map, and UI
- Handle connection flow
- Coordinate configuration updates
- Display status updates

**Key Methods:**
- `handleConnect()` - Connect to BLE device
- `loadConfiguration()` - Read all BLE characteristics
- `validateCurrentLocation()` - Check tide data availability
- `applyChanges()` - Write all changes to device
- `updateStatus()` - Display real-time status

#### **BLEManager** (`ble/ble-manager.js`)
Web Bluetooth API wrapper for device communication.

**Responsibilities:**
- Device connection/disconnection
- Read/write BLE characteristics
- Subscribe to notifications
- Error handling

**Key Methods:**
- `connect()` / `disconnect()`
- `readLocation()` / `writeLocation(lat, lon)`
- `readBrightness()` / `writeBrightness(value)`
- `subscribeToStatus(callback)` - Real-time status updates
- `readAll()` - Read all characteristics at once

#### **MapManager** (`map/map-manager.js`)
Leaflet wrapper for location selection.

**Responsibilities:**
- Render OpenStreetMap
- Handle click events for location selection
- Manage marker placement
- Geolocation API integration

**Key Methods:**
- `setMarker(lat, lon)` - Place marker
- `enableLocationSelection()` - Enable click-to-select
- `useCurrentLocation()` - Use GPS position

#### **LocationValidator** (`map/validator.js`)
Kartverket API integration for tide data validation.

**Responsibilities:**
- Check if location has tide data
- Parse Kartverket API responses
- Debounce API calls (rate limiting)

**Key Methods:**
- `validateLocation(lat, lon)` - Returns `{valid, error, stationName}`

### Data Flow

#### Reading Configuration

```
User clicks "Connect"
    ↓
TideLightApp.handleConnect()
    ↓
BLEManager.connect()
    ↓
Web Bluetooth API (device picker)
    ↓
BLEManager.readAll()
    ↓
TideLightApp.loadConfiguration()
    ↓
UI elements populated
```

#### Writing Configuration

```
User clicks "Apply Changes"
    ↓
TideLightApp.applyChanges()
    ↓
BLEManager.writeLocation()
BLEManager.writeBrightness()
... (all characteristics)
    ↓
Web Bluetooth API (write)
    ↓
Device receives updates
    ↓
Python app applies changes
    ↓
LEDs update (no restart)
```

#### Status Updates

```
BLEManager.subscribeToStatus(callback)
    ↓
Web Bluetooth API (enable notifications)
    ↓
Device sends status every 10s
    ↓
BLEManager calls callback
    ↓
TideLightApp.updateStatus()
    ↓
UI status section updates
```

### API Integration

#### Kartverket Tide API

**Endpoint**: `https://vannstand.kartverket.no/tideapi.php`

**Parameters**:
- `lat` - Latitude (decimal degrees)
- `lon` - Longitude (decimal degrees)
- `fromtime` - Start time (ISO 8601)
- `totime` - End time (ISO 8601)
- `datatype` - "all" (includes tide events)
- `refcode` - "cd" (chart datum reference)
- `lang` - "en" (English responses)
- `interval` - "10" (10-minute intervals)

**Response**: XML format with tide predictions

**CORS**: ✅ Supported (`Access-Control-Allow-Origin: *`)

**Rate Limiting**: Be respectful, use debouncing (500ms implemented)

## Troubleshooting

### Connection Issues

**Problem**: "Web Bluetooth API not supported"

**Solution**: Use Chrome or Edge browser
- Desktop: Download [Chrome](https://www.google.com/chrome/)
- Mobile: Use Chrome or Edge (not in-app browsers)

---

**Problem**: "No devices found" when scanning

**Solutions**:
1. Ensure Python app is running on Raspberry Pi
2. Check Bluetooth is enabled on phone
3. Verify device is in range (BLE range ~10-30 meters)
4. Check Python logs for BLE errors
5. Restart Bluetooth on Raspberry Pi: `sudo systemctl restart bluetooth`

---

**Problem**: "Connection failed"

**Solutions**:
1. Check HTTPS (required for Web Bluetooth, except localhost)
2. Verify device isn't already connected to another client
3. Try forgetting device: Chrome Settings → Privacy → Site Settings → Bluetooth
4. Clear browser cache and reload page

---

**Problem**: "Connection lost" during use

**Solutions**:
1. Move closer to device (improve signal strength)
2. Check Python app is still running
3. Verify power supply is stable
4. Reduce phone battery optimization for Chrome

### Map Issues

**Problem**: Map not loading (gray tiles)

**Solutions**:
1. Check internet connection
2. Verify OpenStreetMap is accessible: `curl https://tile.openstreetmap.org/0/0/0.png`
3. Check browser console for CORS errors
4. Try different network (some corporate networks block tile servers)

---

**Problem**: Location validation fails

**Solutions**:
1. Check internet connection
2. Try location closer to coast (inland locations don't have tide data)
3. Verify Kartverket API is accessible: `curl "https://vannstand.kartverket.no/tideapi.php?lat=59.908559&lon=10.73451&fromtime=2024-01-01T00:00&totime=2024-01-02T00:00&datatype=all&refcode=cd&lang=en&interval=10"`
4. Check browser console for error details

### UI Issues

**Problem**: Touch events not working on mobile

**Solutions**:
1. Ensure minimum tap target size (44px implemented)
2. Check for JavaScript errors in console
3. Try disabling browser zoom
4. Clear cache and reload

---

**Problem**: Notifications not appearing

**Solution**: Check browser console for errors

---

**Problem**: Status not updating

**Solutions**:
1. Check connection is active (status indicator shows "Connected")
2. Verify Python app is running
3. Check browser console for notification errors
4. Disconnect and reconnect

### Deployment Issues

**Problem**: Site loads but can't connect to BLE

**Solution**: HTTPS required (check URL starts with `https://`)
- Netlify provides HTTPS automatically
- Custom domains need SSL certificate

---

**Problem**: Build fails on Netlify

**Solutions**:
1. Check build logs for specific error
2. Verify `package.json` dependencies are correct
3. Ensure Node version is compatible (Netlify uses Node 16+)
4. Check `netlify.toml` configuration

---

**Problem**: Map tiles don't load in production

**Solution**: Check Content Security Policy (CSP) allows OpenStreetMap:
```html
<meta http-equiv="Content-Security-Policy" content="img-src 'self' https://*.openstreetmap.org data:;">
```

## Browser Compatibility

### Web Bluetooth API Support

| Browser | Desktop | Mobile |
|---------|---------|--------|
| Chrome | ✅ 56+ | ✅ Android only |
| Edge | ✅ 79+ | ✅ Android only |
| Firefox | ❌ Not supported | ❌ Not supported |
| Safari | ❌ Not supported | ❌ Not supported |

### Alternative for Unsupported Browsers

**iOS Users**: Use native BLE apps
- [LightBlue](https://apps.apple.com/us/app/lightblue/id557428110) - Free, feature-rich
- [nRF Connect](https://apps.apple.com/us/app/nrf-connect-for-mobile/id1054362403) - Free, Nordic Semiconductor

**Desktop (non-Chrome)**: Use BLE dongles with native apps

### Feature Detection

The app checks for Web Bluetooth support and displays a warning banner if unsupported:

```javascript
if (!navigator.bluetooth) {
  // Show warning banner
  alert("Web Bluetooth not supported. Please use Chrome or Edge.");
}
```

## Performance Optimization

### Implemented Optimizations

1. **Debounced Validation**: API calls limited to 500ms intervals
2. **Lazy Loading**: Map tiles load on demand
3. **Efficient Rendering**: CSS animations use `transform` (GPU-accelerated)
4. **Minimal Dependencies**: Only Leaflet required (no frameworks)
5. **Code Splitting**: Vite automatically splits bundles

### Lighthouse Scores (Target)

- Performance: 90+
- Accessibility: 100
- Best Practices: 100
- SEO: 90+

### Mobile Performance Tips

- Reduce map zoom/pan during BLE writes (prevent UI lag)
- Avoid rapid configuration changes (give device time to process)
- Use "Apply Changes" button (batch writes) instead of individual writes

## Security Considerations

### Current Implementation

- **No Authentication**: Any device in range can be configured
- **No Encryption**: BLE data transmitted in plaintext (within BLE range only)
- **No Validation**: Trusts all data from device

### Recommendations for Production

1. **Add BLE Pairing**: Implement passkey authentication
2. **Input Validation**: Validate all data from device before displaying
3. **Rate Limiting**: Limit write operations per minute
4. **Audit Logging**: Log configuration changes
5. **Secure Storage**: Don't store sensitive data in localStorage

**Note**: Current implementation prioritizes ease of use for personal/development use. Add security layers for public deployments.

## Development Tips

### Debugging Web Bluetooth

1. **Chrome DevTools**:
   - Console: See BLE read/write logs
   - Network: Check Kartverket API calls
   - Application → Storage: View localStorage

2. **Chrome Internals**:
   - `chrome://bluetooth-internals` - View BLE adapters and devices
   - `chrome://inspect/#devices` - Remote debugging for Android

3. **Console Logging**:
   All BLE operations log to console with prefixes:
   ```
   [BLEManager] Connected to device: Tide Light
   [BLEManager] Read Location: 59.908559, 10.73451
   [Validator] Location valid: Oslo, Norway
   ```

### Adding New BLE Characteristics

1. **Add UUID to `constants.js`**:
   ```javascript
   export const CHAR_UUIDS = {
     // ... existing
     NEW_PARAM: "12345678-1234-5678-1234-56789abcdefA"
   };
   ```

2. **Add read/write methods to `ble-manager.js`**:
   ```javascript
   async readNewParam() {
     const dataView = await this._readCharacteristic(CHAR_UUIDS.NEW_PARAM);
     return dataView.getUint8(0);
   }
   
   async writeNewParam(value) {
     const buffer = new Uint8Array([value]);
     await this._writeCharacteristic(CHAR_UUIDS.NEW_PARAM, buffer);
   }
   ```

3. **Add UI elements to `index.html`**:
   ```html
   <label for="new-param">New Parameter:</label>
   <input type="number" id="new-param" min="0" max="255">
   ```

4. **Wire up in `main.js`**:
   ```javascript
   // In loadConfiguration()
   const newParam = await this.bleManager.readNewParam();
   document.getElementById('new-param').value = newParam;
   
   // In applyChanges()
   const newParam = parseInt(document.getElementById('new-param').value);
   await this.bleManager.writeNewParam(newParam);
   ```

### Testing Checklist

- [ ] Load on desktop (Chrome/Edge)
- [ ] Load on mobile (Chrome/Edge Android)
- [ ] Connect to real device
- [ ] Read configuration successfully
- [ ] Map loads and allows selection
- [ ] Location validation works
- [ ] Write configuration successfully
- [ ] Status updates appear
- [ ] Disconnect works cleanly
- [ ] Error messages are user-friendly
- [ ] Responsive on phone/tablet/desktop

## Resources

- [Web Bluetooth API](https://webbluetoothcg.github.io/web-bluetooth/) - Official specification
- [Leaflet Documentation](https://leafletjs.com/reference.html) - Map library docs
- [Vite Guide](https://vitejs.dev/guide/) - Build tool documentation
- [Kartverket API](https://www.kartverket.no/en/at-sea/se-havniva) - Tide data source
- [BLE GATT Specification](https://www.bluetooth.com/specifications/gatt/) - BLE protocol
- [OpenStreetMap](https://www.openstreetmap.org/) - Map tiles

## Next Steps

- Test on real device: Deploy and connect
- Add PWA manifest for "install to home screen"
- Implement error recovery (auto-reconnect)
- Add configuration presets (save/load profiles)
- Create animated tutorial for first-time users

---

**Need help?** Check the [main documentation](../README.md) or [Python app docs](../app/README.md).
