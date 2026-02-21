# Tide Light v2 to v3 - Missing Features Implementation Plan

**Created**: 2026-02-08  
**Status**: Planning Phase  
**Estimated Total Effort**: 8-11 hours

---

## 📊 Executive Summary

After comprehensive analysis of v2 and v3, the following features from v2 are missing in v3:

### ✅ **To Implement** (User Priority)
1. **LDR Auto-brightness** - Automatic dimming based on ambient light (Priority: HIGH)
2. **Hardware Clock Sync** - RTC support for offline operation (Priority: HIGH)
3. **Reset Functionality** - Factory reset via BLE (Priority: MODERATE)
4. **Data Pruning** - Automatic cache cleanup (Priority: LOW)

### ❌ **Intentionally Excluded** (User Decision)
- **Color Customization** - Keeping v3's hardcoded colors (simpler UX)
- **Multiple Animation Patterns** - Wave-only is sufficient

### ✅ **Already Better in V3**
- WiFi Management (NetworkManager vs WPA Supplicant)
- Architecture (Simpler, more maintainable)
- Data Storage (SQLite vs XML)
- Documentation (Much more comprehensive)
- Web Interface (Integrated, not separate repo)

---

## 🎯 Phase 1: LDR Auto-Brightness Support
**Priority**: 🔴 HIGH  
**Estimated Effort**: 3-4 hours  
**Dependencies**: None

### Overview
Port v2's Light Dependent Resistor (LDR) feature to enable automatic brightness adjustment based on ambient light. This significantly improves user experience by preventing overly bright LEDs at night and ensuring visibility in daylight.

### Technical Design

#### 1.1 Hardware Requirements
- **ADC Module**: MCP3008 (SPI) or ADS1015 (I2C) for analog reading
- **LDR Sensor**: Standard photoresistor (5-10kΩ @ 10 lux)
- **Resistor**: 10kΩ fixed resistor for voltage divider
- **GPIO Pin**: Configurable (default: GPIO 11)

**Circuit Diagram:**
```
3.3V ----[ LDR ]----+----[ 10kΩ ]---- GND
                     |
                     +---- ADC Channel 0
```

#### 1.2 Backend Implementation

##### File: `app/ldr_controller.py` (NEW)
```python
"""Light Dependent Resistor controller for automatic brightness adjustment."""

import threading
import time
import logging
from typing import Optional, Callable

# Import ADC library (choose based on hardware)
try:
    import board
    import busio
    import adafruit_mcp3008.mcp3008 as MCP
    from adafruit_mcp3008.analog_in import AnalogIn
    LDR_AVAILABLE = True
except ImportError:
    LDR_AVAILABLE = False
    logging.warning("[LDR] ADC library not available - LDR disabled")

class LdrController:
    """
    Monitors ambient light via LDR and adjusts LED brightness automatically.
    
    Features:
    - Continuous monitoring (1 Hz sample rate)
    - Smart averaging (2 samples) to prevent flickering
    - Configurable brightness range (5-255)
    - Thread-safe operation
    - Enable/disable via config
    """
    
    def __init__(self, config: dict, on_brightness_change: Callable[[int], None]):
        """
        Args:
            config: Configuration dict with ldr settings
            on_brightness_change: Callback to update LED brightness
        """
        self._enabled = config.get("ldr", {}).get("enabled", False)
        self._pin = config.get("ldr", {}).get("pin", 11)
        self._min_brightness = 5
        self._max_brightness = 255
        self._on_brightness_change = on_brightness_change
        
        # ADC setup
        self._adc = None
        self._ldr_channel = None
        if LDR_AVAILABLE and self._enabled:
            self._setup_adc()
        
        # Threading
        self._thread = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        
        # State
        self._last_brightness = None
        self._last_light_level = None
        
    def _setup_adc(self):
        """Initialize SPI and ADC (MCP3008)."""
        try:
            spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
            cs = board.D5  # Chip select pin
            mcp = MCP.MCP3008(spi, cs)
            self._ldr_channel = AnalogIn(mcp, MCP.P0)  # Channel 0
            logging.info(f"[LDR] ADC initialized on channel 0")
        except Exception as e:
            logging.error(f"[LDR] Failed to initialize ADC: {e}")
            self._enabled = False
    
    def start(self):
        """Start LDR monitoring thread."""
        if not self._enabled:
            logging.info("[LDR] LDR disabled - not starting thread")
            return
        
        if not LDR_AVAILABLE:
            logging.warning("[LDR] ADC library not available - cannot start")
            return
        
        if self._thread and self._thread.is_alive():
            logging.warning("[LDR] Thread already running")
            return
        
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logging.info("[LDR] Monitoring thread started")
    
    def stop(self):
        """Stop LDR monitoring thread."""
        if self._thread and self._thread.is_alive():
            logging.info("[LDR] Stopping monitoring thread...")
            self._stop_event.set()
            self._thread.join(timeout=5)
            logging.info("[LDR] Thread stopped")
    
    def _run(self):
        """Main monitoring loop (runs in separate thread)."""
        logging.info("[LDR] Entering monitoring loop")
        
        while not self._stop_event.is_set():
            try:
                # Read light level (0-65535 from 16-bit ADC)
                light_level = self._ldr_channel.value
                
                # Wait 1 second and read again (debouncing)
                time.sleep(1.0)
                if self._stop_event.is_set():
                    break
                
                light_level_2 = self._ldr_channel.value
                
                # Average the two readings
                avg_light = (light_level + light_level_2) // 2
                
                # Check if significantly different from last reading
                if self._last_light_level is None or \
                   abs(avg_light - self._last_light_level) > 2000:  # ~3% threshold
                    
                    # Map light level to brightness (inverted: bright room = dim LEDs)
                    brightness = self._map_light_to_brightness(avg_light)
                    
                    # Update if changed
                    if brightness != self._last_brightness:
                        logging.info(f"[LDR] Light: {avg_light} → Brightness: {brightness}")
                        with self._lock:
                            self._last_brightness = brightness
                            self._last_light_level = avg_light
                        
                        # Callback to update LEDs
                        self._on_brightness_change(brightness)
                
                # Sleep until next check
                time.sleep(1.0)
                
            except Exception as e:
                logging.error(f"[LDR] Error in monitoring loop: {e}")
                time.sleep(5.0)  # Back off on errors
    
    def _map_light_to_brightness(self, light_level: int) -> int:
        """
        Map light level (0-65535) to brightness (5-255).
        
        Inverted mapping: More light = Dimmer LEDs
        
        Args:
            light_level: ADC reading (0 = dark, 65535 = bright)
            
        Returns:
            Brightness value (5-255)
        """
        # Inverted linear mapping
        # Dark room (0) → Max brightness (255)
        # Bright room (65535) → Min brightness (5)
        brightness = int(self._max_brightness - 
                        (light_level / 65535.0) * 
                        (self._max_brightness - self._min_brightness))
        
        # Clamp to valid range
        return max(self._min_brightness, min(self._max_brightness, brightness))
    
    def on_config_updated(self, config: dict):
        """Handle config changes (enable/disable, pin change)."""
        new_enabled = config.get("ldr", {}).get("enabled", False)
        new_pin = config.get("ldr", {}).get("pin", 11)
        
        # Check if LDR was enabled/disabled
        if new_enabled != self._enabled:
            logging.info(f"[LDR] Enabled changed: {self._enabled} → {new_enabled}")
            self._enabled = new_enabled
            
            if self._enabled:
                self.start()
            else:
                self.stop()
        
        # Check if pin changed (requires restart)
        if new_pin != self._pin and self._enabled:
            logging.info(f"[LDR] Pin changed: {self._pin} → {new_pin}")
            self.stop()
            self._pin = new_pin
            self._setup_adc()
            self.start()
    
    def get_status(self) -> dict:
        """Get current LDR status for diagnostics."""
        with self._lock:
            return {
                "enabled": self._enabled,
                "available": LDR_AVAILABLE,
                "light_level": self._last_light_level,
                "brightness": self._last_brightness,
                "thread_alive": self._thread.is_alive() if self._thread else False
            }
```

##### File: `app/main.py` (MODIFY)
```python
# Add LDR import
from ldr_controller import LdrController

# In main() function, after TideVisualizer initialization:
def main():
    # ... existing code ...
    
    # Initialize visualizer
    visualizer = TideVisualizer(config=config, ...)
    
    # Initialize LDR controller (NEW)
    def on_ldr_brightness_change(brightness: int):
        """Callback when LDR wants to change brightness."""
        logging.info(f"[LDR] Auto-adjusting brightness to {brightness}")
        # Update visualizer brightness
        visualizer.set_brightness(brightness)
    
    ldr = LdrController(config=config, on_brightness_change=on_ldr_brightness_change)
    
    # Register LDR as config listener
    def on_config_changed(new_config):
        scheduler.on_config_updated(new_config)
        visualizer.on_config_updated(new_config)
        ldr.on_config_updated(new_config)  # NEW
    
    config_manager.add_listener(on_config_changed)
    
    # Start LDR monitoring
    ldr.start()
    
    # ... rest of main() ...
    
    # In shutdown:
    ldr.stop()
```

##### File: `app/light_controller.py` (MODIFY)
```python
# Add method to LightController class:
def set_brightness_override(self, brightness: int):
    """
    Set brightness override (called by LDR).
    
    Args:
        brightness: Brightness value (0-255)
    """
    with self._lock:
        self._strip.brightness = brightness / 255.0
        self._strip.show()
```

##### File: `app/tide_visualizer.py` (MODIFY)
```python
# Add method to TideVisualizer class:
def set_brightness(self, brightness: int):
    """
    Set brightness (called by LDR or BLE).
    
    Args:
        brightness: Brightness value (0-255)
    """
    self._light.set_brightness_override(brightness)
```

#### 1.3 BLE Characteristic

##### File: `app/ble/characteristics/ldr_active_characteristic.py` (NEW)
```python
"""BLE characteristic for LDR enable/disable."""

from ble_data_utils import encode_bool, decode_bool

class LdrActiveCharacteristic:
    """
    LDR Active Characteristic (UUID: ...defe)
    
    Read: Get current LDR state (0x00 = disabled, 0x01 = enabled)
    Write: Enable/disable LDR (0x00 = disable, 0x01 = enable)
    """
    
    UUID = "12345678-1234-5678-1234-56789abcdefe"
    
    def __init__(self, config_handler, status_provider):
        self._config_handler = config_handler
        self._status_provider = status_provider
    
    def on_read_request(self, offset):
        """Handle read request."""
        config = self._status_provider.get_config()
        enabled = config.get("ldr", {}).get("enabled", False)
        return encode_bool(enabled)
    
    def on_write_request(self, data, offset, without_response):
        """Handle write request."""
        try:
            enabled = decode_bool(data)
            error_code = self._config_handler.update_ldr_active(enabled)
            return {"error": error_code}
        except Exception as e:
            logging.error(f"[LDR Characteristic] Write failed: {e}")
            return {"error": 4}  # INTERNAL_ERROR
```

##### File: `app/ble/ble_config_handler.py` (MODIFY)
```python
# Add method to BLEConfigHandler class:
def update_ldr_active(self, enabled: bool) -> int:
    """
    Update LDR active state.
    
    Args:
        enabled: True to enable, False to disable
        
    Returns:
        Error code (0 = success)
    """
    logging.info(f"[BLE Config] LDR active: {enabled}")
    
    try:
        config = self._config_manager.get_config()
        if "ldr" not in config:
            config["ldr"] = {"enabled": False, "pin": 11}
        
        config["ldr"]["enabled"] = enabled
        self._config_manager.update_config(config)
        return 0  # SUCCESS
    except Exception as e:
        logging.error(f"[BLE Config] Failed to update LDR: {e}")
        return 4  # INTERNAL_ERROR
```

##### File: `app/ble/services/tide_light_service.py` (MODIFY)
```python
# Add LDR characteristic to service:
from characteristics.ldr_active_characteristic import LdrActiveCharacteristic

# In __init__:
self.ldr_active = LdrActiveCharacteristic(config_handler, status_provider)

# Add to characteristics list
```

##### File: `app/ble/ble_characteristics.py` (MODIFY)
```python
# Add LDR UUID constant:
LDR_ACTIVE_CHAR_UUID = "12345678-1234-5678-1234-56789abcdefe"
```

#### 1.4 Web Interface

##### File: `web/src/js/ble/constants.js` (MODIFY)
```javascript
// Add LDR UUID
export const LDR_ACTIVE_UUID = '12345678-1234-5678-1234-56789abcdefe';
```

##### File: `web/src/js/ble/ble-manager.js` (MODIFY)
```javascript
// Add LDR methods:
async readLdrActive() {
    if (!this.isConnected) throw new Error('Not connected');
    const char = this.characteristics[LDR_ACTIVE_UUID];
    if (!char) throw new Error('LDR not available');
    
    const value = await char.readValue();
    return value.getUint8(0) === 1;
}

async writeLdrActive(enabled) {
    if (!this.isConnected) throw new Error('Not connected');
    const char = this.characteristics[LDR_ACTIVE_UUID];
    if (!char) throw new Error('LDR not available');
    
    const data = new Uint8Array([enabled ? 1 : 0]);
    await char.writeValue(data);
}

isLdrAvailable() {
    return LDR_ACTIVE_UUID in this.characteristics;
}
```

##### File: `web/src/js/ble/ble-manager-mock.js` (MODIFY)
```javascript
// Add LDR mock:
async readLdrActive() {
    await this._delay(100);
    return localStorage.getItem('tide-light-ldr-enabled') === 'true';
}

async writeLdrActive(enabled) {
    await this._delay(100);
    localStorage.setItem('tide-light-ldr-enabled', enabled.toString());
}

isLdrAvailable() {
    return true;  // Always available in demo mode
}
```

##### File: `web/index.html` (MODIFY)
```html
<!-- Add LDR toggle in LED Settings section -->
<section class="card" id="led-settings">
    <h2>LED Settings</h2>
    
    <!-- Existing brightness slider -->
    
    <!-- NEW: LDR toggle -->
    <div class="setting-row">
        <label for="ldr-toggle">
            Auto-brightness (LDR)
            <span class="info-icon" title="Automatically adjust brightness based on ambient light">ℹ️</span>
        </label>
        <input type="checkbox" id="ldr-toggle">
    </div>
    
    <!-- Rest of LED settings -->
</section>
```

##### File: `web/src/js/main.js` (MODIFY)
```javascript
// Add LDR initialization:
async init() {
    // ... existing code ...
    
    // Load LDR state if available
    if (this.ble.isLdrAvailable()) {
        const enabled = await this.ble.readLdrActive();
        document.getElementById('ldr-toggle').checked = enabled;
        
        // Update brightness slider state (disabled when LDR active)
        this._updateBrightnessSliderState(enabled);
    } else {
        // Hide LDR toggle if not available
        document.querySelector('#ldr-toggle').parentElement.style.display = 'none';
    }
    
    // Add LDR event listener
    document.getElementById('ldr-toggle').addEventListener('change', async (e) => {
        try {
            await this.ble.writeLdrActive(e.target.checked);
            showNotification('LDR ' + (e.target.checked ? 'enabled' : 'disabled'), 'success');
            this._updateBrightnessSliderState(e.target.checked);
        } catch (err) {
            showNotification('Failed to update LDR: ' + err.message, 'error');
            e.target.checked = !e.target.checked;  // Revert
        }
    });
}

_updateBrightnessSliderState(ldrEnabled) {
    const slider = document.getElementById('brightness-slider');
    const label = document.querySelector('label[for="brightness-slider"]');
    
    if (ldrEnabled) {
        slider.disabled = true;
        slider.style.opacity = '0.5';
        label.style.opacity = '0.5';
        label.title = 'Manual control disabled while LDR is active';
    } else {
        slider.disabled = false;
        slider.style.opacity = '1';
        label.style.opacity = '1';
        label.title = '';
    }
}
```

##### File: `web/src/css/main.css` (MODIFY)
```css
/* Add LDR toggle styles */
.setting-row input[type="checkbox"] {
    width: 44px;
    height: 24px;
    cursor: pointer;
}

.info-icon {
    display: inline-block;
    margin-left: 5px;
    cursor: help;
    font-size: 14px;
    color: #888;
}
```

#### 1.5 Documentation

##### File: `docs/BLE_API.md` (MODIFY)
Add LDR characteristic documentation.

##### File: `app/README.md` (MODIFY)
Add LDR hardware setup section.

#### 1.6 Testing

##### Unit Tests: `app/tests/ldr_controller_test.py` (NEW)
Test light level mapping and config updates.

##### Integration Test Plan:
1. Hardware test with real LDR
2. BLE enable/disable via web
3. Config persistence
4. Thread safety

---

## 🕐 Phase 2: Hardware Clock Sync (RTC Support)
**Priority**: 🔴 HIGH  
**Estimated Effort**: 2-3 hours  
**Dependencies**: None

### Overview
Add support for Real-Time Clock (RTC) modules to enable true offline operation without internet. Critical for installations on boats, remote cabins, or anywhere without reliable NTP access.

### Technical Design

#### 2.1 Hardware Requirements
- **RTC Module**: DS3231 or DS1307 (I2C interface)
- **Battery**: CR2032 coin cell (backup power)
- **GPIO Pins**: I2C (GPIO 2/3 - SDA/SCL)

#### 2.2 Backend Implementation

##### File: `app/rtc_manager.py` (NEW)
Manages hardware clock synchronization with methods for:
- Read system time
- Set system time from BLE
- Sync to/from hardware clock
- Detect RTC availability

##### File: `app/ble/characteristics/rtc_time_characteristic.py` (NEW)
BLE characteristic for reading/writing system time in ISO 8601 format.

#### 2.3 Boot Script

##### File: `app/scripts/rtc_sync_boot.sh` (NEW)
Script to sync system time from RTC on boot.

##### File: `app/scripts/install_rtc_boot.sh` (NEW)
Install systemd service for automatic RTC sync on boot.

#### 2.4 Web Interface

Add "System Settings" section with:
- Current time display
- "Sync Device Time" button
- Auto-sync to RTC on time change

#### 2.5 Documentation

##### File: `docs/RTC_SETUP.md` (NEW)
Complete guide for:
- Hardware wiring
- Raspberry Pi I2C configuration
- RTC kernel module setup
- Boot sync installation

---

## 🔄 Phase 3: Reset Functionality
**Priority**: 🟡 MODERATE  
**Estimated Effort**: 1-2 hours  
**Dependencies**: None

### Overview
Add BLE characteristic to trigger factory reset, restoring default configuration and clearing cache. Useful for remote troubleshooting and recovery.

### Technical Design

#### 3.1 Backend Implementation

##### File: `app/config_manager.py` (MODIFY)
Add `reset_to_defaults()` method to restore factory config.

##### File: `app/ble/characteristics/reset_characteristic.py` (NEW)
Write-only characteristic that triggers:
1. Cache invalidation
2. Config reset to defaults
3. Notify all listeners

#### 3.2 Web Interface

Add "Factory Reset" button in System Settings with:
- Confirmation dialog
- Warning about data loss
- Auto-reload config after reset

---

## 🧹 Phase 4: Data Pruning (Optional)
**Priority**: 🟢 LOW  
**Estimated Effort**: 1 hour  
**Dependencies**: None

### Overview
Add automatic cleanup of old tide data to prevent database bloat.

### Technical Design

##### File: `app/tide_cache_manager.py` (MODIFY)
Add `prune_old_data(days_to_keep=7)` method.

##### File: `app/tide_update_scheduler.py` (MODIFY)
Integrate daily pruning into scheduler loop.

---

## 📝 Summary

### Implementation Priority
1. ✅ **LDR Support** (3-4 hours) - High value, moderate effort
2. ✅ **Hardware Clock Sync** (2-3 hours) - Critical for offline
3. ✅ **Reset Functionality** (1-2 hours) - Useful for troubleshooting
4. ✅ **Data Pruning** (1 hour) - Low priority, easy add

### Total Estimated Effort
**8-11 hours** of development + testing

### Dependencies to Install
```bash
# LDR support
pip install adafruit-circuitpython-mcp3008

# RTC support (no new dependencies - uses subprocess)
```

### Hardware Shopping List (Optional)
- **LDR Kit**: MCP3008 ADC + Photoresistor + 10kΩ resistor (~$10)
- **RTC Kit**: DS3231 module + CR2032 battery (~$5)

### Breaking Changes
**None** - All new features are additive and optional.

### Backward Compatibility
✅ **100% compatible** with existing v3 installations  
✅ Config.json remains valid (new fields optional)  
✅ Existing BLE clients continue to work  
✅ Web interface gracefully hides unavailable features

---

## 🚀 Next Steps

### Before Implementation
- [ ] Review this plan
- [ ] Approve priority order
- [ ] Confirm hardware requirements
- [ ] Order RTC/LDR modules (if needed)

### During Implementation
- [ ] Implement Phase 1 (LDR)
- [ ] Test with real hardware
- [ ] Implement Phase 2 (RTC)
- [ ] Test offline operation
- [ ] Implement Phase 3 (Reset)
- [ ] Test factory reset flow
- [ ] Implement Phase 4 (Pruning) - Optional
- [ ] Update all documentation

### After Implementation
- [ ] Integration testing (all features together)
- [ ] Update README with new features
- [ ] Update BLE_API.md with new characteristics
- [ ] Create hardware setup guides
- [ ] Test on real Raspberry Pi deployment
- [ ] Update web interface deployment

---

**Plan Status**: ✅ Ready for Implementation  
**Last Updated**: 2026-02-08  
**Author**: OpenCode AI Assistant
