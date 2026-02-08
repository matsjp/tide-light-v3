/**
 * Mock BLE Manager - Simulates Tide Light BLE without hardware
 * For testing and demonstration purposes
 */

import { ERROR_CODES, ERROR_MESSAGES } from './constants.js';

const STORAGE_KEYS = {
  DEMO_MODE: 'tide-light-demo-mode',
  DEMO_CONFIG: 'tide-light-demo-config',
  DEMO_STATUS: 'tide-light-demo-status-state'
};

const DEFAULT_CONFIG = {
  location: { lat: 59.908559, lon: 10.73451 }, // Oslo
  brightness: 128,
  pattern: 'wave',
  waveSpeed: 0.5,
  ledCount: 60,
  ledInvert: false,
  errorCode: 0
};

const DEFAULT_STATUS_STATE = {
  tideDirection: 'rising',
  tideProgress: 0.35,
  startTime: Date.now()
};

export class BLEManagerMock {
  constructor() {
    this.device = null;
    this.server = null;
    this.service = null;
    this.characteristics = {};
    this.isConnected = false;
    
    // Event callbacks (same as real BLE Manager)
    this.onConnectionChange = null;
    this.onStatusUpdate = null;
    this.onError = null;
    
    // Mock state
    this.config = this._loadConfig();
    this.statusState = this._loadStatusState();
    this.notificationInterval = null;
    
    console.log('[BLE Mock] Initialized with config:', this.config);
  }

  /**
   * Check if Web Bluetooth is supported (always true for mock)
   */
  static isSupported() {
    return true;
  }

  /**
   * Simulate connection to device
   */
  async connect() {
    console.log('[BLE Mock] Connecting...');
    
    // Simulate connection delay
    await this._delay(1500);
    
    // Simulate device
    this.device = {
      id: 'mock-tide-light-device',
      name: 'Tide Light (Demo)',
      gatt: {
        connected: true,
        connect: () => Promise.resolve(this.server),
        disconnect: () => this._handleDisconnection()
      }
    };
    
    this.server = { connected: true };
    this.service = { uuid: '12345678-1234-5678-1234-56789abcdef0' };
    this.isConnected = true;
    
    this._notifyConnectionChange(true);
    console.log('[BLE Mock] Connected successfully');
    
    return true;
  }

  /**
   * Disconnect from device
   */
  async disconnect() {
    console.log('[BLE Mock] Disconnecting...');
    this._handleDisconnection();
  }

  /**
   * Read location (latitude, longitude)
   */
  async readLocation() {
    await this._delay(150);
    console.log('[BLE Mock] Read location:', this.config.location);
    return { ...this.config.location };
  }

  /**
   * Write location
   */
  async writeLocation(lat, lon) {
    await this._delay(200);
    this.config.location = { lat, lon };
    this._saveConfig();
    console.log('[BLE Mock] Write location:', lat, lon);
  }

  /**
   * Read brightness (0-255)
   */
  async readBrightness() {
    await this._delay(100);
    console.log('[BLE Mock] Read brightness:', this.config.brightness);
    return this.config.brightness;
  }

  /**
   * Write brightness (0-255)
   */
  async writeBrightness(value) {
    await this._delay(150);
    this.config.brightness = Math.max(0, Math.min(255, value));
    this._saveConfig();
    console.log('[BLE Mock] Write brightness:', this.config.brightness);
  }

  /**
   * Read pattern ("none" or "wave")
   */
  async readPattern() {
    await this._delay(100);
    console.log('[BLE Mock] Read pattern:', this.config.pattern);
    return this.config.pattern;
  }

  /**
   * Write pattern
   */
  async writePattern(value) {
    await this._delay(150);
    this.config.pattern = value;
    this._saveConfig();
    console.log('[BLE Mock] Write pattern:', value);
  }

  /**
   * Read wave speed (float)
   */
  async readWaveSpeed() {
    await this._delay(100);
    console.log('[BLE Mock] Read wave speed:', this.config.waveSpeed);
    return this.config.waveSpeed;
  }

  /**
   * Write wave speed
   */
  async writeWaveSpeed(value) {
    await this._delay(150);
    this.config.waveSpeed = Math.max(0.1, Math.min(5.0, value));
    this._saveConfig();
    console.log('[BLE Mock] Write wave speed:', this.config.waveSpeed);
  }

  /**
   * Read LED count (3-255)
   */
  async readLedCount() {
    await this._delay(100);
    console.log('[BLE Mock] Read LED count:', this.config.ledCount);
    return this.config.ledCount;
  }

  /**
   * Write LED count
   */
  async writeLedCount(value) {
    await this._delay(150);
    this.config.ledCount = Math.max(3, Math.min(255, value));
    this._saveConfig();
    console.log('[BLE Mock] Write LED count:', this.config.ledCount);
  }

  /**
   * Read LED invert (boolean)
   */
  async readLedInvert() {
    await this._delay(100);
    console.log('[BLE Mock] Read LED invert:', this.config.ledInvert);
    return this.config.ledInvert;
  }

  /**
   * Write LED invert
   */
  async writeLedInvert(value) {
    await this._delay(150);
    this.config.ledInvert = Boolean(value);
    this._saveConfig();
    console.log('[BLE Mock] Write LED invert:', this.config.ledInvert);
  }

  /**
   * Read full config JSON
   */
  async readFullConfig() {
    await this._delay(200);
    const config = {
      location: this.config.location,
      led_strip: {
        count: this.config.ledCount,
        brightness: this.config.brightness,
        invert: this.config.ledInvert
      },
      color: {
        pattern: this.config.pattern,
        wave_speed: this.config.waveSpeed
      }
    };
    console.log('[BLE Mock] Read full config:', config);
    return config;
  }

  /**
   * Write full config JSON
   */
  async writeFullConfig(config) {
    await this._delay(250);
    if (config.location) {
      this.config.location = config.location;
    }
    if (config.led_strip) {
      this.config.brightness = config.led_strip.brightness;
      this.config.ledCount = config.led_strip.count;
      this.config.ledInvert = config.led_strip.invert;
    }
    if (config.color) {
      this.config.pattern = config.color.pattern;
      this.config.waveSpeed = config.color.wave_speed;
    }
    this._saveConfig();
    console.log('[BLE Mock] Write full config');
  }

  /**
   * Read status JSON
   */
  async readStatus() {
    await this._delay(150);
    const status = this._generateStatus();
    console.log('[BLE Mock] Read status');
    return status;
  }

  /**
   * Subscribe to status notifications
   */
  async subscribeToStatus(callback) {
    console.log('[BLE Mock] Subscribed to status notifications');
    
    // Clear any existing interval
    if (this.notificationInterval) {
      clearInterval(this.notificationInterval);
    }
    
    // Send notifications every 10 seconds
    this.notificationInterval = setInterval(() => {
      if (this.isConnected) {
        this._updateStatusSimulation();
        const status = this._generateStatus();
        callback(status);
        if (this.onStatusUpdate) {
          this.onStatusUpdate(status);
        }
      }
    }, 10000);
    
    // Send initial notification
    const status = this._generateStatus();
    callback(status);
  }

  /**
   * Read error code
   */
  async readErrorCode() {
    await this._delay(100);
    console.log('[BLE Mock] Read error code:', this.config.errorCode);
    return this.config.errorCode;
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
    console.log('[BLE Mock] Reading all values...');
    await this._delay(500);
    
    return {
      location: { ...this.config.location },
      brightness: this.config.brightness,
      pattern: this.config.pattern,
      waveSpeed: this.config.waveSpeed,
      ledCount: this.config.ledCount,
      ledInvert: this.config.ledInvert,
      errorCode: this.config.errorCode,
      errorMessage: this.getErrorMessage(this.config.errorCode)
    };
  }

  // Private helper methods

  _handleDisconnection() {
    console.log('[BLE Mock] Disconnected');
    this.isConnected = false;
    this.device = null;
    this.server = null;
    this.service = null;
    this.characteristics = {};
    
    // Clear notification interval
    if (this.notificationInterval) {
      clearInterval(this.notificationInterval);
      this.notificationInterval = null;
    }
    
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

  _delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  _loadConfig() {
    try {
      const saved = localStorage.getItem(STORAGE_KEYS.DEMO_CONFIG);
      if (saved) {
        return JSON.parse(saved);
      }
    } catch (error) {
      console.warn('[BLE Mock] Could not load saved config:', error);
    }
    return { ...DEFAULT_CONFIG };
  }

  _saveConfig() {
    try {
      localStorage.setItem(STORAGE_KEYS.DEMO_CONFIG, JSON.stringify(this.config));
    } catch (error) {
      console.warn('[BLE Mock] Could not save config:', error);
    }
  }

  _loadStatusState() {
    try {
      const saved = localStorage.getItem(STORAGE_KEYS.DEMO_STATUS);
      if (saved) {
        return JSON.parse(saved);
      }
    } catch (error) {
      console.warn('[BLE Mock] Could not load status state:', error);
    }
    return { ...DEFAULT_STATUS_STATE };
  }

  _saveStatusState() {
    try {
      localStorage.setItem(STORAGE_KEYS.DEMO_STATUS, JSON.stringify(this.statusState));
    } catch (error) {
      console.warn('[BLE Mock] Could not save status state:', error);
    }
  }

  _updateStatusSimulation() {
    // Increment tide progress
    this.statusState.tideProgress += 0.02; // 2% per 10 seconds
    
    // Switch direction when reaching 100%
    if (this.statusState.tideProgress >= 1.0) {
      this.statusState.tideProgress = 0;
      this.statusState.tideDirection = 
        this.statusState.tideDirection === 'rising' ? 'falling' : 'rising';
    }
    
    this._saveStatusState();
  }

  _generateStatus() {
    const now = new Date();
    const uptimeSeconds = Math.floor((Date.now() - this.statusState.startTime) / 1000);
    
    // Calculate next and last events based on tide progress
    const direction = this.statusState.tideDirection;
    const progress = this.statusState.tideProgress;
    
    // Estimate time to next event (assuming 6 hours per tide cycle)
    const secondsPerCycle = 6 * 3600; // 6 hours
    const remainingProgress = 1.0 - progress;
    const secondsToNext = Math.floor(remainingProgress * secondsPerCycle);
    const secondsSinceLast = Math.floor(progress * secondsPerCycle);
    
    const nextEventTime = new Date(now.getTime() + secondsToNext * 1000);
    const lastEventTime = new Date(now.getTime() - secondsSinceLast * 1000);
    
    return {
      tide: {
        available: true,
        direction: direction,
        progress: progress,
        next_event: {
          time: nextEventTime.toISOString(),
          flag: direction === 'rising' ? 'high' : 'low'
        },
        last_event: {
          time: lastEventTime.toISOString(),
          flag: direction === 'rising' ? 'low' : 'high'
        }
      },
      cache: {
        has_data: true,
        latitude: this.config.location.lat,
        longitude: this.config.location.lon
      },
      system: {
        uptime_seconds: uptimeSeconds,
        last_update: now.toISOString()
      }
    };
  }

  /**
   * Reset mock to default values (utility method)
   */
  resetToDefaults() {
    console.log('[BLE Mock] Resetting to defaults');
    this.config = { ...DEFAULT_CONFIG };
    this.statusState = { ...DEFAULT_STATUS_STATE };
    this._saveConfig();
    this._saveStatusState();
  }

  /**
   * Check if demo mode is enabled
   */
  static isDemoModeEnabled() {
    try {
      return localStorage.getItem(STORAGE_KEYS.DEMO_MODE) === 'true';
    } catch (error) {
      return false;
    }
  }

  /**
   * Enable demo mode
   */
  static enableDemoMode() {
    try {
      localStorage.setItem(STORAGE_KEYS.DEMO_MODE, 'true');
      console.log('[BLE Mock] Demo mode enabled');
    } catch (error) {
      console.warn('[BLE Mock] Could not enable demo mode:', error);
    }
  }

  /**
   * Disable demo mode
   */
  static disableDemoMode() {
    try {
      localStorage.setItem(STORAGE_KEYS.DEMO_MODE, 'false');
      console.log('[BLE Mock] Demo mode disabled');
    } catch (error) {
      console.warn('[BLE Mock] Could not disable demo mode:', error);
    }
  }
}
