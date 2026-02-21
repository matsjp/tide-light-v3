/**
 * BLE Manager - Web Bluetooth API wrapper for Tide Light
 * Handles device connection, characteristic reads/writes, and notifications
 */

import { SERVICE_UUID, CHAR_UUIDS, ERROR_CODES, ERROR_MESSAGES, getCharName } from './constants.js';

export class BLEManager {
  constructor() {
    this.device = null;
    this.server = null;
    this.service = null;
    this.characteristics = {};
    this.isConnected = false;
    
    // Event callbacks
    this.onConnectionChange = null;
    this.onStatusUpdate = null;
    this.onError = null;
  }

  /**
   * Check if Web Bluetooth is supported
   */
  static isSupported() {
    return 'bluetooth' in navigator;
  }

  /**
   * Connect to Tide Light device
   */
  async connect() {
    try {
      console.log('[BLE] Requesting device...');
      
      // Request device with service filter
      this.device = await navigator.bluetooth.requestDevice({
        filters: [{ services: [SERVICE_UUID] }],
        optionalServices: [SERVICE_UUID]
      });

      console.log(`[BLE] Selected device: ${this.device.name}`);

      // Listen for disconnection
      this.device.addEventListener('gattserverdisconnected', () => {
        this._handleDisconnection();
      });

      // Connect to GATT server
      console.log('[BLE] Connecting to GATT server...');
      this.server = await this.device.gatt.connect();

      // Get service
      console.log('[BLE] Getting service...');
      this.service = await this.server.getPrimaryService(SERVICE_UUID);

      // Get all characteristics
      await this._loadCharacteristics();

      this.isConnected = true;
      this._notifyConnectionChange(true);

      // Save device ID for reconnection
      this._saveDeviceId(this.device.id);

      console.log('[BLE] Connected successfully');
      return true;

    } catch (error) {
      console.error('[BLE] Connection error:', error);
      this._notifyError(`Connection failed: ${error.message}`);
      throw error;
    }
  }

  /**
   * Disconnect from device
   */
  async disconnect() {
    if (this.device && this.device.gatt.connected) {
      this.device.gatt.disconnect();
    }
    this._handleDisconnection();
  }

  /**
   * Read location (latitude, longitude)
   * @returns {Promise<{lat: number, lon: number}>}
   */
  async readLocation() {
    const value = await this._readString(CHAR_UUIDS.LOCATION);
    const [lat, lon] = value.split(',').map(v => parseFloat(v.trim()));
    return { lat, lon };
  }

  /**
   * Write location
   */
  async writeLocation(lat, lon) {
    const value = `${lat},${lon}`;
    await this._writeString(CHAR_UUIDS.LOCATION, value);
  }

  /**
   * Read brightness (0-255)
   */
  async readBrightness() {
    return await this._readUint8(CHAR_UUIDS.BRIGHTNESS);
  }

  /**
   * Write brightness (0-255)
   */
  async writeBrightness(value) {
    await this._writeUint8(CHAR_UUIDS.BRIGHTNESS, value);
  }

  /**
   * Read pattern ("none" or "wave")
   */
  async readPattern() {
    return await this._readString(CHAR_UUIDS.PATTERN);
  }

  /**
   * Write pattern
   */
  async writePattern(value) {
    await this._writeString(CHAR_UUIDS.PATTERN, value);
  }

  /**
   * Read wave speed (float as string)
   */
  async readWaveSpeed() {
    const value = await this._readString(CHAR_UUIDS.WAVE_SPEED);
    return parseFloat(value);
  }

  /**
   * Write wave speed
   */
  async writeWaveSpeed(value) {
    await this._writeString(CHAR_UUIDS.WAVE_SPEED, value.toString());
  }

  /**
   * Read LED count (3-255)
   */
  async readLedCount() {
    return await this._readUint8(CHAR_UUIDS.LED_COUNT);
  }

  /**
   * Write LED count
   */
  async writeLedCount(value) {
    await this._writeUint8(CHAR_UUIDS.LED_COUNT, value);
  }

  /**
   * Read LED invert (boolean)
   */
  async readLedInvert() {
    const value = await this._readUint8(CHAR_UUIDS.LED_INVERT);
    return value === 1;
  }

  /**
   * Write LED invert
   */
  async writeLedInvert(value) {
    await this._writeUint8(CHAR_UUIDS.LED_INVERT, value ? 1 : 0);
  }

  /**
   * Read LDR active (boolean)
   */
  async readLdrActive() {
    if (!this.characteristics[CHAR_UUIDS.LDR_ACTIVE]) {
      return false; // LDR not available on this device
    }
    const value = await this._readUint8(CHAR_UUIDS.LDR_ACTIVE);
    return value === 1;
  }

  /**
   * Write LDR active
   */
  async writeLdrActive(value) {
    if (!this.characteristics[CHAR_UUIDS.LDR_ACTIVE]) {
      throw new Error('LDR characteristic not available');
    }
    await this._writeUint8(CHAR_UUIDS.LDR_ACTIVE, value ? 1 : 0);
  }

  /**
   * Check if LDR is available
   */
  isLdrAvailable() {
    return !!this.characteristics[CHAR_UUIDS.LDR_ACTIVE];
  }

  /**
   * Read system time (ISO 8601 string)
   */
  async readSystemTime() {
    if (!this.characteristics[CHAR_UUIDS.SYSTEM_TIME]) {
      return null; // RTC not available on this device
    }
    return await this._readString(CHAR_UUIDS.SYSTEM_TIME);
  }

  /**
   * Write system time (ISO 8601 string)
   */
  async writeSystemTime(isoTimeString) {
    if (!this.characteristics[CHAR_UUIDS.SYSTEM_TIME]) {
      throw new Error('System time characteristic not available');
    }
    await this._writeString(CHAR_UUIDS.SYSTEM_TIME, isoTimeString);
  }

  /**
   * Check if RTC is available
   */
  isRtcAvailable() {
    return !!this.characteristics[CHAR_UUIDS.SYSTEM_TIME];
  }

  /**
   * Sync device time to browser's current time
   */
  async syncTimeNow() {
    const now = new Date();
    // Format as ISO 8601 without milliseconds or timezone (local time)
    const isoString = now.toISOString().split('.')[0];
    await this.writeSystemTime(isoString);
  }

  /**
   * Trigger factory reset (restore default configuration)
   * Writing 0x01 triggers the reset
   */
  async factoryReset() {
    if (!this.characteristics[CHAR_UUIDS.RESET]) {
      throw new Error('Reset characteristic not available');
    }
    await this._writeUint8(CHAR_UUIDS.RESET, 1);
  }

  /**
   * Read full config JSON
   */
  async readFullConfig() {
    const json = await this._readString(CHAR_UUIDS.FULL_CONFIG);
    return JSON.parse(json);
  }

  /**
   * Write full config JSON
   */
  async writeFullConfig(config) {
    const json = JSON.stringify(config);
    await this._writeString(CHAR_UUIDS.FULL_CONFIG, json);
  }

  /**
   * Read status JSON
   */
  async readStatus() {
    const json = await this._readString(CHAR_UUIDS.STATUS);
    console.log('[BLE] Raw status JSON:', json);
    const status = JSON.parse(json);
    console.log('[BLE] Parsed status:', status);
    return status;
  }

  /**
   * Subscribe to status notifications
   */
  async subscribeToStatus(callback) {
    const char = this.characteristics[CHAR_UUIDS.STATUS];
    if (!char) {
      throw new Error('Status characteristic not found');
    }

    console.log('[BLE] Status characteristic found:', char);
    console.log('[BLE] Status characteristic UUID:', char.uuid);
    console.log('[BLE] Status characteristic properties:', char.properties);
    
    // Check if notifications are supported
    if (!char.properties.notify) {
      throw new Error('Status characteristic does not support notifications');
    }

    console.log('[BLE] Starting notifications on Status characteristic...');
    try {
      // Start notifications
      await char.startNotifications();
      console.log('[BLE] ✓ Notifications started successfully');
    } catch (error) {
      console.error('[BLE] ✗ Failed to start notifications:', error.message, error);
      console.error('[BLE] Error name:', error.name);
      console.error('[BLE] Error code:', error.code);
      throw error;
    }

    // Listen for changes
    char.addEventListener('characteristicvaluechanged', (event) => {
      const value = event.target.value;
      const json = new TextDecoder().decode(value);
      console.log('[BLE] Status notification JSON:', json);
      const status = JSON.parse(json);
      console.log('[BLE] Parsed notification status:', status);
      callback(status);
      if (this.onStatusUpdate) {
        this.onStatusUpdate(status);
      }
    });

    console.log('[BLE] Subscribed to status notifications');
  }

  /**
   * Read error code
   */
  async readErrorCode() {
    return await this._readUint8(CHAR_UUIDS.ERROR);
  }

  /**
   * Get error message for error code
   */
  getErrorMessage(errorCode) {
    return ERROR_MESSAGES[errorCode] || `Unknown error (${errorCode})`;
  }

  /**
   * Read all configuration values at once
   */
  async readAll() {
    try {
      // Helper to safely read a characteristic, returning null if unavailable
      const safeRead = async (readFn, defaultValue = null) => {
        try {
          return await readFn();
        } catch (error) {
          console.warn('[BLE] Could not read characteristic:', error.message);
          return defaultValue;
        }
      };

      // Read all characteristics, handling missing ones gracefully
      const [location, brightness, pattern, waveSpeed, ledCount, ledInvert, ldrActive, errorCode] = await Promise.all([
        safeRead(() => this.readLocation(), { lat: 0, lon: 0 }),
        safeRead(() => this.readBrightness(), 128),
        safeRead(() => this.readPattern(), 'none'),
        safeRead(() => this.readWaveSpeed(), 1.0),
        safeRead(() => this.readLedCount(), 60),
        safeRead(() => this.readLedInvert(), false),
        safeRead(() => this.readLdrActive(), false),
        safeRead(() => this.readErrorCode(), 0)
      ]);

      return {
        location,
        brightness,
        pattern,
        waveSpeed,
        ledCount,
        ledInvert,
        ldrActive,
        errorCode,
        errorMessage: this.getErrorMessage(errorCode)
      };
    } catch (error) {
      console.error('[BLE] Error reading all values:', error);
      throw error;
    }
  }

  // Private helper methods

  async _loadCharacteristics() {
    const uuids = Object.values(CHAR_UUIDS);
    
    console.log(`[BLE] Attempting to load ${uuids.length} characteristics`);
    
    for (const uuid of uuids) {
      const charName = getCharName(uuid);
      try {
        const char = await this.service.getCharacteristic(uuid);
        this.characteristics[uuid] = char;
        
        // Extra logging for Status characteristic
        if (uuid === CHAR_UUIDS.STATUS) {
          console.log(`[BLE] ✓ Loaded: ${charName} (${uuid})`);
          console.log(`[BLE]   Properties:`, char.properties);
          console.log(`[BLE]   Notify supported:`, char.properties.notify);
          console.log(`[BLE]   Read supported:`, char.properties.read);
        } else {
          console.log(`[BLE] ✓ Loaded: ${charName} (${uuid})`);
        }
      } catch (error) {
        console.warn(`[BLE] ✗ Failed: ${charName} (${uuid}) - ${error.message}`);
      }
    }

    console.log(`[BLE] Successfully loaded ${Object.keys(this.characteristics).length}/${uuids.length} characteristics`);
    
    // Log which characteristics are missing
    const missing = uuids.filter(uuid => !this.characteristics[uuid]);
    if (missing.length > 0) {
      console.warn(`[BLE] Missing ${missing.length} characteristics:`, missing.map(uuid => getCharName(uuid)));
    }
  }

  async _readString(uuid) {
    const char = this.characteristics[uuid];
    const charName = getCharName(uuid);
    if (!char) throw new Error(`Characteristic ${charName} not found`);

    console.log(`[BLE] Reading ${charName}...`);
    try {
      const value = await char.readValue();
      const decoded = new TextDecoder().decode(value);
      console.log(`[BLE] ✓ Read ${decoded.length} bytes from ${charName}`);
      return decoded;
    } catch (error) {
      console.error(`[BLE] ✗ Error reading ${charName}:`, error.message, error);
      throw error;
    }
  }

  async _writeString(uuid, value) {
    const char = this.characteristics[uuid];
    if (!char) throw new Error(`Characteristic ${uuid} not found`);

    const encoder = new TextEncoder();
    await char.writeValue(encoder.encode(value));
  }

  async _readUint8(uuid) {
    const char = this.characteristics[uuid];
    const charName = getCharName(uuid);
    if (!char) throw new Error(`Characteristic ${charName} not found`);

    console.log(`[BLE] Reading ${charName}...`);
    try {
      const value = await char.readValue();
      const uint8Value = value.getUint8(0);
      console.log(`[BLE] ✓ Read ${charName}: ${uint8Value}`);
      return uint8Value;
    } catch (error) {
      console.error(`[BLE] ✗ Error reading ${charName}:`, error.message, error);
      throw error;
    }
  }

  async _writeUint8(uuid, value) {
    const char = this.characteristics[uuid];
    if (!char) throw new Error(`Characteristic ${uuid} not found`);

    const buffer = new Uint8Array([value]);
    await char.writeValue(buffer);
  }

  _handleDisconnection() {
    console.log('[BLE] Disconnected');
    this.isConnected = false;
    this.device = null;
    this.server = null;
    this.service = null;
    this.characteristics = {};
    this._notifyConnectionChange(false);
  }

  _notifyConnectionChange(connected) {
    if (this.onConnectionChange) {
      this.onConnectionChange(connected);
    }
  }

  _notifyError(message) {
    if (this.onError) {
      this.onError(message);
    }
  }

  _saveDeviceId(deviceId) {
    try {
      localStorage.setItem('tide-light-device-id', deviceId);
    } catch (error) {
      console.warn('[BLE] Could not save device ID:', error);
    }
  }

  static getLastDeviceId() {
    try {
      return localStorage.getItem('tide-light-device-id');
    } catch (error) {
      return null;
    }
  }

  // ===== WiFi Methods =====

  /**
   * Read available WiFi networks.
   * This triggers a scan on the device.
   * @returns {Promise<Array>} Array of network objects: [{ssid, signal, security}, ...]
   */
  async readWifiNetworks() {
    if (!this.isConnected) {
      throw new Error('Device not connected');
    }

    const characteristic = this.characteristics[CHAR_UUIDS.WIFI_NETWORKS];
    if (!characteristic) {
      throw new Error('WiFi Networks characteristic not available');
    }

    try {
      const value = await characteristic.readValue();
      const jsonString = new TextDecoder().decode(value);
      return JSON.parse(jsonString);
    } catch (error) {
      console.error('[BLE] Error reading WiFi networks:', error);
      throw error;
    }
  }

  /**
   * Write WiFi SSID to connect to.
   * Must be called before writeWifiPassword.
   * @param {string} ssid - Network SSID
   */
  async writeWifiSsid(ssid) {
    if (!this.isConnected) {
      throw new Error('Device not connected');
    }

    const characteristic = this.characteristics[CHAR_UUIDS.WIFI_SSID];
    if (!characteristic) {
      throw new Error('WiFi SSID characteristic not available');
    }

    try {
      const encodedValue = new TextEncoder().encode(ssid);
      await characteristic.writeValue(encodedValue);
      console.log('[BLE] WiFi SSID written:', ssid);
    } catch (error) {
      console.error('[BLE] Error writing WiFi SSID:', error);
      throw error;
    }
  }

  /**
   * Write WiFi password and trigger connection attempt.
   * writeWifiSsid must be called first.
   * @param {string} password - Network password
   */
  async writeWifiPassword(password) {
    if (!this.isConnected) {
      throw new Error('Device not connected');
    }

    const characteristic = this.characteristics[CHAR_UUIDS.WIFI_PASSWORD];
    if (!characteristic) {
      throw new Error('WiFi Password characteristic not available');
    }

    try {
      const encodedValue = new TextEncoder().encode(password);
      await characteristic.writeValue(encodedValue);
      console.log('[BLE] WiFi password written, connection attempt started');
    } catch (error) {
      console.error('[BLE] Error writing WiFi password:', error);
      throw error;
    }
  }

  /**
   * Read WiFi connection status.
   * @returns {Promise<Object>} Status object: {connected, ssid, error_code}
   */
  async readWifiStatus() {
    if (!this.isConnected) {
      throw new Error('Device not connected');
    }

    const characteristic = this.characteristics[CHAR_UUIDS.WIFI_STATUS];
    if (!characteristic) {
      throw new Error('WiFi Status characteristic not available');
    }

    try {
      const value = await characteristic.readValue();
      const jsonString = new TextDecoder().decode(value);
      return JSON.parse(jsonString);
    } catch (error) {
      console.error('[BLE] Error reading WiFi status:', error);
      throw error;
    }
  }

  /**
   * Subscribe to WiFi status notifications.
   * @param {Function} callback - Called with status object: {connected, ssid, error_code}
   */
  async subscribeWifiStatus(callback) {
    if (!this.isConnected) {
      throw new Error('Device not connected');
    }

    const characteristic = this.characteristics[CHAR_UUIDS.WIFI_STATUS];
    if (!characteristic) {
      throw new Error('WiFi Status characteristic not available');
    }

    try {
      await characteristic.startNotifications();
      characteristic.addEventListener('characteristicvaluechanged', (event) => {
        const value = event.target.value;
        const jsonString = new TextDecoder().decode(value);
        const status = JSON.parse(jsonString);
        callback(status);
      });
      console.log('[BLE] Subscribed to WiFi status notifications');
    } catch (error) {
      console.error('[BLE] Error subscribing to WiFi status:', error);
      throw error;
    }
  }

  /**
   * Check if WiFi characteristics are available.
   * @returns {boolean} True if WiFi is supported
   */
  isWifiAvailable() {
    return !!this.characteristics[CHAR_UUIDS.WIFI_NETWORKS];
  }
}
