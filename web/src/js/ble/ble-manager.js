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
      
      // Request device - use acceptAllDevices with optionalServices
      // This matches the working v2 project pattern
      this.device = await navigator.bluetooth.requestDevice({
        acceptAllDevices: true,
        optionalServices: [SERVICE_UUID]  // 0xec00 in numeric hex format
      });

      console.log(`[BLE] Selected device: ${this.device.name}`);

      // Listen for disconnection
      this.device.addEventListener('gattserverdisconnected', () => {
        this._handleDisconnection();
      });

      // Connect to GATT server
      console.log('[BLE] Connecting to GATT server...');
      this.server = await this.device.gatt.connect();

      // Get service - use numeric hex UUID
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
    // Format as ISO 8601 in LOCAL time (not UTC)
    // Example: "2026-05-15T16:34:51" for local time
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const seconds = String(now.getSeconds()).padStart(2, '0');
    const isoString = `${year}-${month}-${day}T${hours}:${minutes}:${seconds}`;
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
   * Read status JSON
   */
  async readStatus() {
    const json = await this._readString(CHAR_UUIDS.STATUS);
    return JSON.parse(json);
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

      // Read all characteristics SEQUENTIALLY (BLE doesn't support parallel reads)
      // Using Promise.all() causes "NotSupportedError" on some characteristics
      const location = await safeRead(() => this.readLocation(), { lat: 0, lon: 0 });
      const brightness = await safeRead(() => this.readBrightness(), 128);
      const pattern = await safeRead(() => this.readPattern(), 'none');
      const waveSpeed = await safeRead(() => this.readWaveSpeed(), 1.0);
      const ledCount = await safeRead(() => this.readLedCount(), 60);
      const ledInvert = await safeRead(() => this.readLedInvert(), false);
      const ldrActive = await safeRead(() => this.readLdrActive(), false);

      return {
        location,
        brightness,
        pattern,
        waveSpeed,
        ledCount,
        ledInvert,
        ldrActive
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
        // Store with string key to ensure consistent lookup
        const key = String(uuid);
        this.characteristics[key] = char;
        
        console.log(`[BLE] ✓ Loaded: ${charName} (${uuid})`);
        console.log(`[BLE]   Stored with key: ${key} (type: ${typeof key})`);
        console.log(`[BLE]   UUID: ${char.uuid}`);
        console.log(`[BLE]   Properties - read: ${char.properties.read}, write: ${char.properties.write}, notify: ${char.properties.notify}`);
      } catch (error) {
        console.warn(`[BLE] ✗ Failed: ${charName} (${uuid}) - ${error.message}`);
      }
    }

    console.log(`[BLE] Successfully loaded ${Object.keys(this.characteristics).length}/${uuids.length} characteristics`);
    
    // Log which characteristics are missing
    const missing = uuids.filter(uuid => !this.characteristics[String(uuid)]);
    if (missing.length > 0) {
      console.warn(`[BLE] Missing ${missing.length} characteristics:`, missing.map(uuid => getCharName(uuid)));
    }
    
    // Debug: Log all loaded characteristic UUIDs
    console.log(`[BLE] Loaded characteristic UUIDs:`, Object.keys(this.characteristics));
  }

  async _readString(uuid) {
    // Convert UUID to string for consistent lookup
    const key = String(uuid);
    const char = this.characteristics[key];
    const charName = getCharName(uuid);
    
    if (!char) {
      const error = `Characteristic ${charName} not found`;
      console.error(`[BLE] ${error}`);
      throw new Error(error);
    }

    try {
      const value = await char.readValue();
      const decoded = new TextDecoder().decode(value);
      return decoded;
    } catch (error) {
      console.error(`[BLE] Error reading ${charName}:`, error);
      throw error;
    }
  }

  async _writeString(uuid, value) {
    // Convert UUID to string for consistent lookup
    const key = String(uuid);
    const char = this.characteristics[key];
    if (!char) throw new Error(`Characteristic ${uuid} not found`);

    const encoder = new TextEncoder();
    await char.writeValue(encoder.encode(value));
  }

  async _writeUint8(uuid, value) {
    // Convert UUID to string for consistent lookup
    const key = String(uuid);
    const char = this.characteristics[key];
    if (!char) throw new Error(`Characteristic ${uuid} not found`);

    const buffer = new Uint8Array([value]);
    await char.writeValue(buffer);
  }

  async _readUint8(uuid) {
    // Convert UUID to string for consistent lookup
    const key = String(uuid);
    const char = this.characteristics[key];
    const charName = getCharName(uuid);
    
    if (!char) throw new Error(`Characteristic ${charName} not found`);

    try {
      const value = await char.readValue();
      return value.getUint8(0);
    } catch (error) {
      console.error(`[BLE] Error reading ${charName}:`, error);
      throw error;
    }
  }

  async _writeUint8(uuid, value) {
    // Convert UUID to string for consistent lookup
    const key = String(uuid);
    const char = this.characteristics[key];
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
  /**
   * Read WiFi networks using notification-based protocol.
   * Subscribes to notifications, receives network batches, waits for completion signal.
   * @returns {Promise<Array>} Array of network objects
   */
  async readWifiNetworks() {
    if (!this.isConnected) {
      throw new Error('Device not connected');
    }

    const key = String(CHAR_UUIDS.WIFI_NETWORKS);
    const characteristic = this.characteristics[key];
    
    if (!characteristic) {
      throw new Error('WiFi Networks characteristic not available');
    }

    return new Promise((resolve, reject) => {
      const networks = [];
      let timeoutId = null;
      
      // Cleanup function
      const cleanup = () => {
        if (timeoutId) {
          clearTimeout(timeoutId);
        }
        characteristic.removeEventListener('characteristicvaluechanged', handleNotification);
        characteristic.stopNotifications().catch((error) => {
          console.warn('[BLE] Error stopping notifications:', error);
        });
      };
      
      // Set 60-second timeout
      timeoutId = setTimeout(() => {
        console.log(`[BLE] WiFi scan timeout after 60 seconds - returning ${networks.length} collected networks`);
        cleanup();
        resolve(networks);
      }, 60000);
      
      // Handle incoming notifications
      const handleNotification = (event) => {
        try {
          const value = event.target.value;
          const jsonString = new TextDecoder().decode(value);
          console.log(`[BLE] Received notification: "${jsonString.substring(0, 100)}${jsonString.length > 100 ? '...' : ''}"`);
          
          const batch = JSON.parse(jsonString);
          
          if (batch.length === 0) {
            // Empty array signals scan completion
            console.log(`[BLE] WiFi scan complete - received ${networks.length} total networks`);
            cleanup();
            resolve(networks);
          } else {
            // Add networks from this batch
            networks.push(...batch);
            console.log(`[BLE] Received batch of ${batch.length} networks (total: ${networks.length})`);
          }
        } catch (error) {
          console.error('[BLE] Error parsing notification:', error);
          // Don't reject - continue waiting for more notifications
          // The timeout will handle if this was fatal
        }
      };
      
      // Subscribe to notifications and start scan
      console.log('[BLE] Subscribing to WiFi scan notifications...');
      characteristic.addEventListener('characteristicvaluechanged', handleNotification);
      characteristic.startNotifications()
        .then(() => {
          console.log('[BLE] ✓ Subscribed - WiFi scan started on device');
        })
        .catch((error) => {
          console.error('[BLE] Failed to start notifications:', error);
          cleanup();
          reject(error);
        });
    });
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

    const key = String(CHAR_UUIDS.WIFI_SSID);
    const characteristic = this.characteristics[key];
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

    const key = String(CHAR_UUIDS.WIFI_PASSWORD);
    const characteristic = this.characteristics[key];
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

    const key = String(CHAR_UUIDS.WIFI_STATUS);
    const characteristic = this.characteristics[key];
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

    const key = String(CHAR_UUIDS.WIFI_STATUS);
    const characteristic = this.characteristics[key];
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
    const key = String(CHAR_UUIDS.WIFI_NETWORKS);
    const available = !!this.characteristics[key];
    console.log('[BLE] isWifiAvailable() - key:', key, 'available:', available);
    console.log('[BLE] Available keys:', Object.keys(this.characteristics));
    return available;
  }
}
