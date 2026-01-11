/**
 * BLE Manager - Web Bluetooth API wrapper for Tide Light
 * Handles device connection, characteristic reads/writes, and notifications
 */

import { SERVICE_UUID, CHAR_UUIDS, ERROR_CODES, ERROR_MESSAGES } from './constants.js';

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

    // Start notifications
    await char.startNotifications();

    // Listen for changes
    char.addEventListener('characteristicvaluechanged', (event) => {
      const value = event.target.value;
      const json = new TextDecoder().decode(value);
      const status = JSON.parse(json);
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
      const [location, brightness, pattern, waveSpeed, ledCount, ledInvert, errorCode] = await Promise.all([
        this.readLocation(),
        this.readBrightness(),
        this.readPattern(),
        this.readWaveSpeed(),
        this.readLedCount(),
        this.readLedInvert(),
        this.readErrorCode()
      ]);

      return {
        location,
        brightness,
        pattern,
        waveSpeed,
        ledCount,
        ledInvert,
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
    
    for (const uuid of uuids) {
      try {
        const char = await this.service.getCharacteristic(uuid);
        this.characteristics[uuid] = char;
      } catch (error) {
        console.warn(`[BLE] Could not get characteristic ${uuid}:`, error);
      }
    }

    console.log(`[BLE] Loaded ${Object.keys(this.characteristics).length} characteristics`);
  }

  async _readString(uuid) {
    const char = this.characteristics[uuid];
    if (!char) throw new Error(`Characteristic ${uuid} not found`);

    const value = await char.readValue();
    return new TextDecoder().decode(value);
  }

  async _writeString(uuid, value) {
    const char = this.characteristics[uuid];
    if (!char) throw new Error(`Characteristic ${uuid} not found`);

    const encoder = new TextEncoder();
    await char.writeValue(encoder.encode(value));
  }

  async _readUint8(uuid) {
    const char = this.characteristics[uuid];
    if (!char) throw new Error(`Characteristic ${uuid} not found`);

    const value = await char.readValue();
    return value.getUint8(0);
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
}
