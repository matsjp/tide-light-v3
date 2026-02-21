/**
 * WiFi Manager - Handles WiFi configuration UI
 */

import { ERROR_CODES, ERROR_MESSAGES } from '../ble/constants.js';

export class WiFiManager {
  constructor(bleManager) {
    this._bleManager = bleManager;
    this._selectedSsid = null;
    this._isScanning = false;

    // DOM elements
    this._wifiStatusDisplay = null;
    
    // Views
    this._scanView = null;
    this._networksView = null;
    this._passwordView = null;
    this._connectionStatusView = null;

    // Buttons
    this._scanBtn = null;
    this._rescanBtn = null;
    this._connectBtn = null;
    this._cancelBtn = null;
    this._doneBtn = null;

    // Inputs
    this._networksList = null;
    this._selectedSsidDisplay = null;
    this._passwordInput = null;
    this._showPasswordCheckbox = null;
    this._statusMessage = null;

    this._initElements();
    this._attachListeners();
  }

  _initElements() {
    // Status display
    this._wifiStatusDisplay = document.getElementById('wifi-status-display');

    // Views
    this._scanView = document.getElementById('wifi-scan-view');
    this._networksView = document.getElementById('wifi-networks-view');
    this._passwordView = document.getElementById('wifi-password-view');
    this._connectionStatusView = document.getElementById('wifi-connection-status');

    // Buttons
    this._scanBtn = document.getElementById('wifi-scan-btn');
    this._rescanBtn = document.getElementById('wifi-rescan-btn');
    this._connectBtn = document.getElementById('wifi-connect-btn');
    this._cancelBtn = document.getElementById('wifi-cancel-btn');
    this._doneBtn = document.getElementById('wifi-done-btn');

    // Inputs
    this._networksList = document.getElementById('wifi-networks-list');
    this._selectedSsidDisplay = document.getElementById('wifi-selected-ssid');
    this._passwordInput = document.getElementById('wifi-password-input');
    this._showPasswordCheckbox = document.getElementById('wifi-show-password');
    this._statusMessage = document.getElementById('wifi-status-message');
  }

  _attachListeners() {
    // WiFi buttons
    this._scanBtn?.addEventListener('click', () => this._scanNetworks());
    this._rescanBtn?.addEventListener('click', () => this._scanNetworks());
    this._connectBtn?.addEventListener('click', () => this._connectToNetwork());
    this._cancelBtn?.addEventListener('click', () => this._showScanView());
    this._doneBtn?.addEventListener('click', () => this._showScanView());

    // Password visibility toggle
    this._showPasswordCheckbox?.addEventListener('change', (e) => {
      this._passwordInput.type = e.target.checked ? 'text' : 'password';
    });
  }

  /**
   * Initialize WiFi section when connected
   */
  async init() {
    if (this._bleManager.isConnected && this._bleManager.isWifiAvailable()) {
      await this._updateWifiStatus();
    }
  }

  /**
   * Update WiFi status indicator
   */
  async _updateWifiStatus() {
    if (!this._bleManager.isWifiAvailable()) return;

    try {
      const status = await this._bleManager.readWifiStatus();
      this._displayWifiStatus(status);
    } catch (error) {
      console.error('[WiFi] Error reading status:', error);
    }
  }

  _displayWifiStatus(status) {
    if (!this._wifiStatusDisplay) return;

    if (status.connected) {
      this._wifiStatusDisplay.textContent = `Connected to ${status.ssid}`;
      this._wifiStatusDisplay.style.color = 'var(--success-color)';
    } else {
      this._wifiStatusDisplay.textContent = 'Not connected';
      this._wifiStatusDisplay.style.color = 'var(--text-secondary)';
    }
  }

  // ===== View Management =====

  _showScanView() {
    this._scanView.style.display = 'block';
    this._networksView.style.display = 'none';
    this._passwordView.style.display = 'none';
    this._connectionStatusView.style.display = 'none';
    this._selectedSsid = null;
    this._passwordInput.value = '';
  }

  _showNetworksView() {
    this._scanView.style.display = 'none';
    this._networksView.style.display = 'block';
    this._passwordView.style.display = 'none';
    this._connectionStatusView.style.display = 'none';
  }

  _showPasswordView(ssid) {
    this._selectedSsid = ssid;
    this._selectedSsidDisplay.textContent = ssid;
    this._passwordInput.value = '';
    this._showPasswordCheckbox.checked = false;
    this._passwordInput.type = 'password';

    this._scanView.style.display = 'none';
    this._networksView.style.display = 'none';
    this._passwordView.style.display = 'block';
    this._connectionStatusView.style.display = 'none';

    // Focus password input
    setTimeout(() => this._passwordInput.focus(), 100);
  }

  _showConnectionStatusView(message, isSuccess) {
    this._statusMessage.textContent = message;
    this._statusMessage.className = 'status-message ' + (isSuccess ? 'success' : 'error');

    this._scanView.style.display = 'none';
    this._networksView.style.display = 'none';
    this._passwordView.style.display = 'none';
    this._connectionStatusView.style.display = 'block';
  }

  // ===== Network Scanning =====

  async _scanNetworks() {
    if (this._isScanning) return;
    
    if (!this._bleManager.isWifiAvailable()) {
      this._showError('WiFi not available on this device');
      return;
    }

    this._isScanning = true;
    this._networksList.innerHTML = '<div class="loading">Scanning for networks...</div>';
    this._showNetworksView();

    try {
      const networks = await this._bleManager.readWifiNetworks();
      this._displayNetworks(networks);
    } catch (error) {
      console.error('[WiFi] Scan error:', error);
      this._networksList.innerHTML = '<div class="error">Failed to scan networks. Please try again.</div>';
    } finally {
      this._isScanning = false;
    }
  }

  _displayNetworks(networks) {
    if (!networks || networks.length === 0) {
      this._networksList.innerHTML = '<div class="hint">No networks found. Try rescanning.</div>';
      return;
    }

    // Sort by signal strength
    networks.sort((a, b) => b.signal - a.signal);

    this._networksList.innerHTML = '';
    
    networks.forEach(network => {
      const item = this._createNetworkItem(network);
      this._networksList.appendChild(item);
    });
  }

  _createNetworkItem(network) {
    const item = document.createElement('div');
    item.className = 'wifi-network-item';
    item.onclick = () => this._showPasswordView(network.ssid);

    const info = document.createElement('div');
    info.className = 'wifi-network-info';

    const signalIcon = document.createElement('span');
    signalIcon.className = 'wifi-signal-icon';
    signalIcon.textContent = this._getSignalIcon(network.signal);

    const details = document.createElement('div');
    details.className = 'wifi-network-details';

    const ssid = document.createElement('div');
    ssid.className = 'wifi-ssid';
    ssid.textContent = network.ssid;

    const signalText = document.createElement('div');
    signalText.className = 'wifi-signal-text';
    signalText.textContent = `Signal: ${this._getSignalStrength(network.signal)}`;

    details.appendChild(ssid);
    details.appendChild(signalText);

    info.appendChild(signalIcon);
    info.appendChild(details);

    item.appendChild(info);

    if (network.security) {
      const securityIcon = document.createElement('span');
      securityIcon.className = 'wifi-security-icon';
      securityIcon.textContent = '🔒';
      securityIcon.title = 'Secured';
      item.appendChild(securityIcon);
    }

    return item;
  }

  _getSignalIcon(signal) {
    if (signal >= 75) return '📶';
    if (signal >= 50) return '📶';
    if (signal >= 25) return '📶';
    return '📶';
  }

  _getSignalStrength(signal) {
    if (signal >= 75) return 'Excellent';
    if (signal >= 50) return 'Good';
    if (signal >= 25) return 'Fair';
    return 'Weak';
  }

  // ===== Connection =====

  async _connectToNetwork() {
    if (!this._selectedSsid) return;

    const password = this._passwordInput.value;

    // Disable button during connection
    this._connectBtn.disabled = true;
    this._connectBtn.textContent = 'Connecting...';

    try {
      // Write SSID
      await this._bleManager.writeWifiSsid(this._selectedSsid);
      
      // Write password (triggers connection)
      await this._bleManager.writeWifiPassword(password);

      // Subscribe to status updates
      await this._bleManager.subscribeWifiStatus((status) => {
        this._handleWifiStatusUpdate(status);
      });

      // Poll for status
      this._pollConnectionStatus();

    } catch (error) {
      console.error('[WiFi] Connection error:', error);
      this._showConnectionStatusView(
        'Failed to initiate connection: ' + error.message,
        false
      );
      this._connectBtn.disabled = false;
      this._connectBtn.textContent = 'Connect';
    }
  }

  async _pollConnectionStatus() {
    let attempts = 0;
    const maxAttempts = 20; // 20 seconds

    const poll = async () => {
      if (attempts >= maxAttempts) {
        this._showConnectionStatusView('Connection timeout', false);
        this._connectBtn.disabled = false;
        this._connectBtn.textContent = 'Connect';
        return;
      }

      try {
        const status = await this._bleManager.readWifiStatus();
        
        if (status.connected) {
          this._showConnectionStatusView(
            `Successfully connected to ${status.ssid}!`,
            true
          );
          this._updateWifiStatus();
          this._connectBtn.disabled = false;
          this._connectBtn.textContent = 'Connect';
          return;
        }

        if (status.error_code && status.error_code !== ERROR_CODES.NONE) {
          const errorMsg = ERROR_MESSAGES[status.error_code] || 'Connection failed';
          this._showConnectionStatusView(errorMsg, false);
          this._connectBtn.disabled = false;
          this._connectBtn.textContent = 'Connect';
          return;
        }

        // Continue polling
        attempts++;
        setTimeout(poll, 1000);

      } catch (error) {
        console.error('[WiFi] Status poll error:', error);
        attempts++;
        setTimeout(poll, 1000);
      }
    };

    poll();
  }

  _handleWifiStatusUpdate(status) {
    console.log('[WiFi] Status update:', status);
    this._displayWifiStatus(status);
  }

  _showError(message) {
    this._networksList.innerHTML = `<div class="error">${message}</div>`;
  }
}
