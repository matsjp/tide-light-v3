/**
 * Map Manager - Leaflet wrapper for location selection
 */

import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

export class MapManager {
  constructor(containerId, options = {}) {
    const defaultOptions = {
      center: [59.9, 10.7], // Norway coast
      zoom: 6,
      minZoom: 4,
      maxZoom: 15
    };

    const opts = { ...defaultOptions, ...options };

    // Initialize map
    this.map = L.map(containerId, {
      center: opts.center,
      zoom: opts.zoom,
      minZoom: opts.minZoom,
      maxZoom: opts.maxZoom,
      zoomControl: true
    });

    // Add OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 19
    }).addTo(this.map);

    // Marker for selected location
    this.marker = null;

    // Callbacks
    this.onLocationSelect = null;

    // Restore last map position
    this._restoreMapPosition();

    console.log('[Map] Initialized');
  }

  /**
   * Enable click-to-place marker
   */
  enableLocationSelection() {
    this.map.on('click', (e) => {
      this.setMarker(e.latlng.lat, e.latlng.lng);
      if (this.onLocationSelect) {
        this.onLocationSelect(e.latlng.lat, e.latlng.lng);
      }
    });
  }

  /**
   * Set marker at coordinates
   */
  setMarker(lat, lon) {
    // Remove existing marker
    if (this.marker) {
      this.map.removeLayer(this.marker);
    }

    // Add new marker
    this.marker = L.marker([lat, lon], {
      draggable: false
    }).addTo(this.map);

    // Center map on marker
    this.map.setView([lat, lon], Math.max(this.map.getZoom(), 8));

    // Save position
    this._saveMapPosition();
  }

  /**
   * Get current marker position
   */
  getMarkerPosition() {
    if (!this.marker) return null;
    const latlng = this.marker.getLatLng();
    return { lat: latlng.lat, lon: latlng.lng };
  }

  /**
   * Clear marker
   */
  clearMarker() {
    if (this.marker) {
      this.map.removeLayer(this.marker);
      this.marker = null;
    }
  }

  /**
   * Pan to location
   */
  panTo(lat, lon, zoom = null) {
    const currentZoom = zoom || this.map.getZoom();
    this.map.setView([lat, lon], currentZoom);
    this._saveMapPosition();
  }

  /**
   * Get user's current location via geolocation
   */
  async getUserLocation() {
    return new Promise((resolve, reject) => {
      if (!navigator.geolocation) {
        reject(new Error('Geolocation not supported'));
        return;
      }

      navigator.geolocation.getCurrentPosition(
        (position) => {
          const lat = position.coords.latitude;
          const lon = position.coords.longitude;
          resolve({ lat, lon });
        },
        (error) => {
          reject(error);
        },
        {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 0
        }
      );
    });
  }

  /**
   * Use current location
   */
  async useCurrentLocation() {
    try {
      const { lat, lon } = await this.getUserLocation();
      this.setMarker(lat, lon);
      if (this.onLocationSelect) {
        this.onLocationSelect(lat, lon);
      }
      return { lat, lon };
    } catch (error) {
      console.error('[Map] Error getting current location:', error);
      throw error;
    }
  }

  /**
   * Resize map (call after container size change)
   */
  invalidateSize() {
    this.map.invalidateSize();
  }

  /**
   * Destroy map instance
   */
  destroy() {
    if (this.map) {
      this.map.remove();
      this.map = null;
    }
  }

  // Private methods

  _saveMapPosition() {
    try {
      const center = this.map.getCenter();
      const zoom = this.map.getZoom();
      const position = {
        lat: center.lat,
        lon: center.lng,
        zoom: zoom
      };
      localStorage.setItem('tide-light-map-position', JSON.stringify(position));
    } catch (error) {
      console.warn('[Map] Could not save position:', error);
    }
  }

  _restoreMapPosition() {
    try {
      const saved = localStorage.getItem('tide-light-map-position');
      if (saved) {
        const position = JSON.parse(saved);
        this.map.setView([position.lat, position.lon], position.zoom);
      }
    } catch (error) {
      console.warn('[Map] Could not restore position:', error);
    }
  }
}
