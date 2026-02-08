/**
 * Main Application - Tide Light Web Configuration
 */

import { BLEManager } from './ble/ble-manager.js';
import { BLEManagerMock } from './ble/ble-manager-mock.js';
import { MapManager } from './map/map-manager.js';
import { validateLocation, debounce } from './map/validator.js';
import { showNotification, showError, showSuccess } from './utils/notifications.js';

class TideLightApp {
  constructor() {
    // Check if demo mode is enabled
    this.demoMode = localStorage.getItem('tide-light-demo-mode') === 'true';
    
    // Initialize appropriate BLE manager
    this.ble = this.demoMode ? new BLEManagerMock() : new BLEManager();
    
    this.map = null;
    this.currentConfig = null;
    this.validationState = { valid: false, validating: false };

    // Update UI to show demo mode state
    this.updateDemoModeUI();

    // Check browser support (only if not in demo mode)
    if (!this.demoMode && !BLEManager.isSupported()) {
      this.showBrowserWarning();
      document.getElementById('connect-btn').disabled = true;
      return;
    }

    this.init();
  }

  init() {
    // Setup BLE callbacks
    this.ble.onConnectionChange = (connected) => this.handleConnectionChange(connected);
    this.ble.onStatusUpdate = (status) => this.updateStatus(status);
    this.ble.onError = (error) => showError(error);

    // Setup UI event listeners
    this.setupEventListeners();

    console.log('[App] Initialized');
  }

  setupEventListeners() {
    // Demo mode toggle
    document.getElementById('demo-mode-checkbox').addEventListener('change', (e) => {
      this.handleDemoModeToggle(e.target.checked);
    });

    // Connection
    document.getElementById('connect-btn').addEventListener('click', () => this.handleConnect());

    // Location inputs (with debounced validation)
    const validateDebounced = debounce(() => this.validateCurrentLocation(), 500);
    document.getElementById('lat-input').addEventListener('input', validateDebounced);
    document.getElementById('lon-input').addEventListener('input', validateDebounced);

    // Current location button
    document.getElementById('current-location-btn').addEventListener('click', () => this.useCurrentLocation());

    // Configuration inputs
    document.getElementById('brightness-input').addEventListener('input', (e) => {
      document.getElementById('brightness-value').textContent = e.target.value;
    });

    document.getElementById('pattern-select').addEventListener('change', (e) => {
      this.toggleWaveSpeedVisibility(e.target.value === 'wave');
    });

    // Apply button
    document.getElementById('apply-btn').addEventListener('click', () => this.applyChanges());
  }

  async handleConnect() {
    try {
      this.showLoading('Connecting to device...');
      await this.ble.connect();
      // Connection success handled by callback
    } catch (error) {
      console.error('[App] Connection error:', error);
      showError(`Failed to connect: ${error.message}`);
    } finally {
      this.hideLoading();
    }
  }

  async handleConnectionChange(connected) {
    const statusDot = document.getElementById('status-dot');
    const statusText = document.getElementById('status-text');

    if (connected) {
      statusDot.className = 'status-dot connected';
      statusText.textContent = 'Connected';
      showSuccess('Connected to Tide Light');

      // Load current configuration
      await this.loadConfiguration();

      // Show all sections
      this.showSection('map-section');
      this.showSection('config-section');
      this.showSection('status-section');

      // Initialize map
      if (!this.map) {
        this.initializeMap();
      }

      // Subscribe to status updates
      await this.ble.subscribeToStatus((status) => this.updateStatus(status));

      // Load initial status
      const status = await this.ble.readStatus();
      this.updateStatus(status);

    } else {
      statusDot.className = 'status-dot';
      statusText.textContent = 'Not Connected';
      
      // Hide sections
      this.hideSection('map-section');
      this.hideSection('config-section');
      this.hideSection('status-section');
    }
  }

  async loadConfiguration() {
    try {
      this.showLoading('Loading configuration...');

      const config = await this.ble.readAll();
      this.currentConfig = config;

      // Update UI with current values
      document.getElementById('lat-input').value = config.location.lat.toFixed(6);
      document.getElementById('lon-input').value = config.location.lon.toFixed(6);
      document.getElementById('brightness-input').value = config.brightness;
      document.getElementById('brightness-value').textContent = config.brightness;
      document.getElementById('pattern-select').value = config.pattern;
      document.getElementById('wave-speed-input').value = config.waveSpeed;
      document.getElementById('led-count-input').value = config.ledCount;
      document.getElementById('led-invert-input').checked = config.ledInvert;

      // Update map marker
      if (this.map) {
        this.map.setMarker(config.location.lat, config.location.lon);
      }

      // Validate location
      await this.validateCurrentLocation();

      // Toggle wave speed visibility
      this.toggleWaveSpeedVisibility(config.pattern === 'wave');

      console.log('[App] Configuration loaded:', config);

    } catch (error) {
      console.error('[App] Error loading configuration:', error);
      showError('Failed to load configuration');
    } finally {
      this.hideLoading();
    }
  }

  initializeMap() {
    this.map = new MapManager('map');
    
    // Enable click to select location
    this.map.enableLocationSelection();
    
    // Handle location selection
    this.map.onLocationSelect = (lat, lon) => {
      document.getElementById('lat-input').value = lat.toFixed(6);
      document.getElementById('lon-input').value = lon.toFixed(6);
      this.validateCurrentLocation();
    };
  }

  async validateCurrentLocation() {
    const lat = parseFloat(document.getElementById('lat-input').value);
    const lon = parseFloat(document.getElementById('lon-input').value);

    if (isNaN(lat) || isNaN(lon)) {
      this.showValidationStatus('error', 'Invalid coordinates');
      return;
    }

    this.showValidationStatus('validating', 'Checking tide data availability...');
    this.validationState.validating = true;

    try {
      const result = await validateLocation(lat, lon);
      
      if (result.valid) {
        const message = result.stationName 
          ? `✓ Tide data available (${result.stationName})`
          : '✓ Tide data available';
        this.showValidationStatus('success', message);
        this.validationState.valid = true;
      } else {
        this.showValidationStatus('error', `✗ ${result.error}`);
        this.validationState.valid = false;
      }
    } catch (error) {
      this.showValidationStatus('error', `✗ Validation failed: ${error.message}`);
      this.validationState.valid = false;
    } finally {
      this.validationState.validating = false;
    }
  }

  async useCurrentLocation() {
    try {
      this.showLoading('Getting your location...');
      const { lat, lon } = await this.map.useCurrentLocation();
      
      document.getElementById('lat-input').value = lat.toFixed(6);
      document.getElementById('lon-input').value = lon.toFixed(6);
      
      await this.validateCurrentLocation();
      showSuccess('Location updated');
    } catch (error) {
      showError(`Could not get location: ${error.message}`);
    } finally {
      this.hideLoading();
    }
  }

  async applyChanges() {
    if (!this.ble.isConnected) {
      showError('Not connected to device');
      return;
    }

    // Validate location first
    if (!this.validationState.valid) {
      showError('Please select a valid location with tide data');
      return;
    }

    try {
      this.showLoading('Applying changes...');

      const lat = parseFloat(document.getElementById('lat-input').value);
      const lon = parseFloat(document.getElementById('lon-input').value);
      const brightness = parseInt(document.getElementById('brightness-input').value);
      const pattern = document.getElementById('pattern-select').value;
      const waveSpeed = parseFloat(document.getElementById('wave-speed-input').value);
      const ledCount = parseInt(document.getElementById('led-count-input').value);
      const ledInvert = document.getElementById('led-invert-input').checked;

      // Write all values
      await Promise.all([
        this.ble.writeLocation(lat, lon),
        this.ble.writeBrightness(brightness),
        this.ble.writePattern(pattern),
        this.ble.writeWaveSpeed(waveSpeed),
        this.ble.writeLedCount(ledCount),
        this.ble.writeLedInvert(ledInvert)
      ]);

      // Check for errors
      const errorCode = await this.ble.readErrorCode();
      if (errorCode !== 0) {
        const errorMsg = this.ble.getErrorMessage(errorCode);
        throw new Error(errorMsg);
      }

      showSuccess('Configuration updated successfully');
      console.log('[App] Configuration applied');

    } catch (error) {
      console.error('[App] Error applying changes:', error);
      showError(`Failed to apply changes: ${error.message}`);
    } finally {
      this.hideLoading();
    }
  }

  updateStatus(status) {
    console.log('[App] Status update:', status);

    // Update tide status
    const tideStatusEl = document.getElementById('tide-status');
    if (status.tide.available) {
      const direction = status.tide.direction === 'rising' ? '↗️ Rising' : '↘️ Falling';
      const progress = (status.tide.progress * 100).toFixed(1);
      
      tideStatusEl.innerHTML = `
        <div class="status-row">
          <span class="label">Direction:</span>
          <span class="value">${direction}</span>
        </div>
        <div class="status-row">
          <span class="label">Progress:</span>
          <span class="value">
            <div class="progress-bar">
              <div class="progress-fill" style="width: ${progress}%"></div>
            </div>
            ${progress}%
          </span>
        </div>
        <div class="status-row">
          <span class="label">Next Event:</span>
          <span class="value">${status.tide.next_event.flag} at ${this.formatTime(status.tide.next_event.time)}</span>
        </div>
        <div class="status-row">
          <span class="label">Last Event:</span>
          <span class="value">${status.tide.last_event.flag} at ${this.formatTime(status.tide.last_event.time)}</span>
        </div>
      `;
    } else {
      tideStatusEl.innerHTML = `
        <div class="no-data">
          ${status.tide.reason || 'No tide data available'}
        </div>
      `;
    }

    // Update cache info
    const cacheInfoEl = document.getElementById('cache-info');
    cacheInfoEl.innerHTML = `
      <div class="info-row">
        <span class="label">Has Data:</span>
        <span class="value">${status.cache.has_data ? '✓ Yes' : '✗ No'}</span>
      </div>
      <div class="info-row">
        <span class="label">Location:</span>
        <span class="value">${status.cache.latitude || 'N/A'}, ${status.cache.longitude || 'N/A'}</span>
      </div>
    `;

    // Update system info
    const systemInfoEl = document.getElementById('system-info');
    const uptime = this.formatDuration(status.system.uptime_seconds);
    systemInfoEl.innerHTML = `
      <div class="info-row">
        <span class="label">Uptime:</span>
        <span class="value">${uptime}</span>
      </div>
      <div class="info-row">
        <span class="label">Last Update:</span>
        <span class="value">${this.formatTime(status.system.last_update)}</span>
      </div>
    `;
  }

  // Helper methods

  showBrowserWarning() {
    document.getElementById('browser-warning').style.display = 'block';
  }

  showSection(id) {
    document.getElementById(id).style.display = 'block';
  }

  hideSection(id) {
    document.getElementById(id).style.display = 'none';
  }

  showLoading(message = 'Loading...') {
    document.getElementById('loading-message').textContent = message;
    document.getElementById('loading-overlay').style.display = 'flex';
  }

  hideLoading() {
    document.getElementById('loading-overlay').style.display = 'none';
  }

  showValidationStatus(type, message) {
    const el = document.getElementById('validation-status');
    el.className = `validation-status validation-${type}`;
    el.textContent = message;
    el.style.display = 'block';
  }

  toggleWaveSpeedVisibility(visible) {
    const group = document.getElementById('wave-speed-group');
    group.style.display = visible ? 'block' : 'none';
  }

  formatTime(isoString) {
    const date = new Date(isoString);
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  }

  formatDuration(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  }

  updateDemoModeUI() {
    const checkbox = document.getElementById('demo-mode-checkbox');
    const banner = document.getElementById('demo-mode-banner');
    
    checkbox.checked = this.demoMode;
    
    if (this.demoMode) {
      banner.style.display = 'block';
    } else {
      banner.style.display = 'none';
    }
  }

  handleDemoModeToggle(enabled) {
    if (enabled) {
      localStorage.setItem('tide-light-demo-mode', 'true');
    } else {
      localStorage.setItem('tide-light-demo-mode', 'false');
    }
    
    // Reload page to apply changes
    window.location.reload();
  }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  new TideLightApp();
});
