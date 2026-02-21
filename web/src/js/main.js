/**
 * Main Application - Tide Light Web Configuration
 */

import { BLEManager } from './ble/ble-manager.js';
import { BLEManagerMock } from './ble/ble-manager-mock.js';
import { MapManager } from './map/map-manager.js';
import { WiFiManager } from './wifi/wifi-manager.js';
import { validateLocation, debounce } from './map/validator.js';
import { validatePiTideData } from './tide/tide-validator.js';
import { showNotification, showError, showSuccess } from './utils/notifications.js';

class TideLightApp {
  constructor() {
    // Check if demo mode is enabled
    this.demoMode = localStorage.getItem('tide-light-demo-mode') === 'true';
    
    // Initialize appropriate BLE manager
    this.ble = this.demoMode ? new BLEManagerMock() : new BLEManager();
    
    this.map = null;
    this.wifi = null;
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

    // Initialize WiFi manager
    this.wifi = new WiFiManager(this.ble);

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

    // LDR toggle
    document.getElementById('ldr-toggle-input').addEventListener('change', async (e) => {
      await this.handleLdrToggle(e.target.checked);
    });

    // RTC sync button
    document.getElementById('sync-time-btn').addEventListener('click', async () => {
      await this.handleSyncTime();
    });

    // Factory reset button
    document.getElementById('factory-reset-btn').addEventListener('click', async () => {
      await this.handleFactoryReset();
    });

    // Apply button
    document.getElementById('apply-btn').addEventListener('click', () => this.applyChanges());

    // Debug panel controls
    this.setupDebugPanel();
  }

  setupDebugPanel() {
    const debugHeader = document.getElementById('debug-header');
    const debugToggle = document.getElementById('debug-toggle');
    const debugContent = document.getElementById('debug-content');
    const debugClear = document.getElementById('debug-clear');

    // Toggle debug panel expand/collapse
    debugHeader.addEventListener('click', () => {
      const isCollapsed = debugContent.classList.toggle('collapsed');
      debugToggle.classList.toggle('collapsed', isCollapsed);
      debugToggle.textContent = isCollapsed ? '◀' : '▼';
    });

    // Clear debug messages
    debugClear.addEventListener('click', () => {
      this.hideDebugPanel();
    });
  }

  showDebugError(error) {
    const debugPanel = document.getElementById('debug-panel');
    const debugMessage = document.getElementById('debug-message');
    const debugContent = document.getElementById('debug-content');
    const debugToggle = document.getElementById('debug-toggle');

    // Format error message
    let errorText = '';
    if (typeof error === 'string') {
      errorText = error;
    } else if (error instanceof Error) {
      errorText = `${error.name}: ${error.message}`;
      if (error.stack) {
        errorText += `\n\nStack:\n${error.stack}`;
      }
    } else {
      errorText = JSON.stringify(error, null, 2);
    }

    debugMessage.textContent = errorText;
    
    // Show panel and expand it
    debugPanel.style.display = 'block';
    debugContent.classList.remove('collapsed');
    debugToggle.classList.remove('collapsed');
    debugToggle.textContent = '▼';
  }

  hideDebugPanel() {
    const debugPanel = document.getElementById('debug-panel');
    debugPanel.style.display = 'none';
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

      // FIRST: Update UI immediately (hide connect button, show config sections)
      this.hideSection('connection-section');
      this.showSection('map-section');
      this.showSection('config-section');
      this.showSection('status-section');

      // Initialize map
      if (!this.map) {
        this.initializeMap();
      }

      // THEN: Try to load data with error handling
      try {
        // Load current configuration
        await this.loadConfiguration();

        // Show WiFi section if available
        if (this.ble.isWifiAvailable && this.ble.isWifiAvailable()) {
          this.showSection('wifi-section');
          try {
            await this.wifi?.init();
          } catch (wifiError) {
            console.warn('[App] WiFi init failed:', wifiError);
            this.showDebugError(`WiFi initialization failed: ${wifiError.message}`);
          }
        }

        // Show System section if RTC available
        if (this.ble.isRtcAvailable && this.ble.isRtcAvailable()) {
          this.showSection('system-section');
          try {
            await this.initializeRtcUI();
          } catch (rtcError) {
            console.warn('[App] RTC init failed:', rtcError);
            this.showDebugError(`RTC initialization failed: ${rtcError.message}`);
          }
        }

        // Try to subscribe to status updates (optional - don't fail if unavailable)
        try {
          await this.ble.subscribeToStatus((status) => this.updateStatus(status));
          const status = await this.ble.readStatus();
          this.updateStatus(status);
        } catch (statusError) {
          console.warn('[App] Status updates not available:', statusError);
          // Don't show error for missing status - it's optional
        }

      } catch (error) {
        console.error('[App] Error during connection setup:', error);
        this.showDebugError(error);
        showError(`Connection setup error: ${error.message}`);
      }

    } else {
      statusDot.className = 'status-dot';
      statusText.textContent = 'Not Connected';
      
      // Show connection section
      this.showSection('connection-section');
      
      // Clear time update interval
      if (this.timeUpdateInterval) {
        clearInterval(this.timeUpdateInterval);
        this.timeUpdateInterval = null;
      }
      
      // Hide sections
      this.hideSection('map-section');
      this.hideSection('config-section');
      this.hideSection('status-section');
      this.hideSection('wifi-section');
      this.hideSection('system-section');
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

      // Show/hide LDR toggle based on availability
      if (this.ble.isLdrAvailable && this.ble.isLdrAvailable()) {
        document.getElementById('ldr-group').style.display = 'block';
        document.getElementById('ldr-toggle-input').checked = config.ldrActive;
        this.updateBrightnessSliderState(config.ldrActive);
      } else {
        document.getElementById('ldr-group').style.display = 'none';
      }

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

  async handleLdrToggle(enabled) {
    if (!this.ble.isConnected) {
      showError('Not connected to device');
      document.getElementById('ldr-toggle-input').checked = !enabled; // Revert
      return;
    }

    try {
      await this.ble.writeLdrActive(enabled);
      showSuccess(enabled ? 'LDR enabled' : 'LDR disabled');
      this.updateBrightnessSliderState(enabled);
      console.log('[App] LDR toggled:', enabled);
    } catch (error) {
      console.error('[App] Error toggling LDR:', error);
      showError(`Failed to update LDR: ${error.message}`);
      document.getElementById('ldr-toggle-input').checked = !enabled; // Revert
    }
  }

  updateBrightnessSliderState(ldrEnabled) {
    const slider = document.getElementById('brightness-input');
    const valueDisplay = document.getElementById('brightness-value');
    const label = slider.previousElementSibling;

    if (ldrEnabled) {
      slider.disabled = true;
      slider.style.opacity = '0.5';
      valueDisplay.style.opacity = '0.5';
      if (label) label.style.opacity = '0.5';
      if (label) label.title = 'Manual control disabled while LDR is active';
    } else {
      slider.disabled = false;
      slider.style.opacity = '1';
      valueDisplay.style.opacity = '1';
      if (label) label.style.opacity = '1';
      if (label) label.title = '';
    }
  }

  async initializeRtcUI() {
    // Start updating time displays every second
    this.updateTimeDisplays();
    this.timeUpdateInterval = setInterval(() => {
      this.updateTimeDisplays();
    }, 1000);
  }

  async updateTimeDisplays() {
    // Update browser time
    const now = new Date();
    const browserTimeStr = now.toLocaleTimeString('en-US', { hour12: false });
    document.getElementById('browser-time-display').textContent = browserTimeStr;

    // Update device time
    try {
      if (this.ble.isConnected && this.ble.isRtcAvailable && this.ble.isRtcAvailable()) {
        const deviceTime = await this.ble.readSystemTime();
        if (deviceTime) {
          const deviceDate = new Date(deviceTime);
          const deviceTimeStr = deviceDate.toLocaleTimeString('en-US', { hour12: false });
          document.getElementById('device-time-display').textContent = deviceTimeStr;
        }
      }
    } catch (error) {
      console.error('[App] Error reading device time:', error);
    }
  }

  async handleSyncTime() {
    if (!this.ble.isConnected) {
      showError('Not connected to device');
      return;
    }

    try {
      this.showLoading('Syncing device time...');
      await this.ble.syncTimeNow();
      showSuccess('Device time synced successfully');
      await this.updateTimeDisplays(); // Update immediately
      console.log('[App] Time synced');
    } catch (error) {
      console.error('[App] Error syncing time:', error);
      showError(`Failed to sync time: ${error.message}`);
    } finally {
      this.hideLoading();
    }
  }

  async handleFactoryReset() {
    if (!this.ble.isConnected) {
      showError('Not connected to device');
      return;
    }

    // Show confirmation dialog
    const confirmed = confirm(
      '⚠️ WARNING: Factory Reset\n\n' +
      'This will restore ALL settings to factory defaults:\n' +
      '• Location will be reset\n' +
      '• LED settings will be reset\n' +
      '• All custom configurations will be lost\n\n' +
      'This action CANNOT be undone!\n\n' +
      'Are you absolutely sure you want to continue?'
    );

    if (!confirmed) {
      return;
    }

    // Double confirmation for safety
    const doubleConfirmed = confirm(
      'Final Confirmation\n\n' +
      'Click OK to proceed with factory reset, or Cancel to abort.'
    );

    if (!doubleConfirmed) {
      return;
    }

    try {
      this.showLoading('Resetting to factory defaults...');
      await this.ble.factoryReset();
      showSuccess('Factory reset completed. Reloading configuration...');
      
      // Wait a moment for the reset to complete
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Reload configuration from device
      await this.loadConfiguration();
      console.log('[App] Factory reset completed');
    } catch (error) {
      console.error('[App] Error during factory reset:', error);
      showError(`Factory reset failed: ${error.message}`);
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

    // Trigger automatic tide data validation
    this.handleTideValidation(status);
  }

  async handleTideValidation(status) {
    const validationEl = document.getElementById('tide-validation');
    
    // Show validating state
    validationEl.innerHTML = `
      <div class="validation-validating">
        <span class="validation-spinner"></span>
        Validating tide data against Kartverket API...
      </div>
    `;

    try {
      const result = await validatePiTideData(status);
      
      console.log('[App] Validation result:', result);

      // Display validation result based on status
      if (result.status === 'valid') {
        validationEl.innerHTML = `
          <div class="validation-success">
            <strong>✓ Validated</strong>
            <p>${result.message}</p>
            ${result.details ? `
              <div class="validation-details">
                <div class="validation-detail-row">
                  <span>Next event:</span>
                  <span>${result.details.nextEvent.diffMinutes} min difference</span>
                </div>
              </div>
            ` : ''}
          </div>
        `;
      } else if (result.status === 'mismatch') {
        validationEl.innerHTML = `
          <div class="validation-warning">
            <strong>⚠️ Data Mismatch Detected</strong>
            <p>${result.message}</p>
            ${result.details && result.details.mismatches ? `
              <ul class="validation-mismatches">
                ${result.details.mismatches.map(m => `<li>${m}</li>`).join('')}
              </ul>
            ` : ''}
            ${result.details ? `
              <div class="validation-details">
                <div class="validation-event-group">
                  <strong>Next Event:</strong>
                  <div class="validation-detail-row">
                    <span>Pi:</span>
                    <span>${this.formatTime(result.details.nextEvent.piTime)} (${result.details.nextEvent.piType})</span>
                  </div>
                  <div class="validation-detail-row">
                    <span>API:</span>
                    <span>${this.formatTime(result.details.nextEvent.apiTime)} (${result.details.nextEvent.apiType})</span>
                  </div>
                  <div class="validation-detail-row">
                    <span>Difference:</span>
                    <span>${result.details.nextEvent.diffMinutes} minutes</span>
                  </div>
                </div>
              </div>
            ` : ''}
          </div>
        `;
      } else if (result.status === 'unavailable') {
        validationEl.innerHTML = `
          <div class="validation-unavailable">
            <strong>ℹ️ Validation Unavailable</strong>
            <p>${result.message}</p>
          </div>
        `;
      } else if (result.status === 'error') {
        validationEl.innerHTML = `
          <div class="validation-error">
            <strong>✗ Validation Error</strong>
            <p>${result.message}</p>
          </div>
        `;
      }

    } catch (error) {
      console.error('[App] Validation failed:', error);
      validationEl.innerHTML = `
        <div class="validation-error">
          <strong>✗ Validation Failed</strong>
          <p>Could not validate tide data: ${error.message}</p>
        </div>
      `;
    }
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
