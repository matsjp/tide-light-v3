/**
 * Location Validator - Check if tide data is available via Kartverket API
 */

const API_URL = 'https://vannstand.kartverket.no/tideapi.php';

/**
 * Format date for Kartverket API
 */
function formatTime(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  return `${year}-${month}-${day}T${hours}:${minutes}`;
}

/**
 * Validate location by checking if tide data is available
 * @param {number} lat - Latitude
 * @param {number} lon - Longitude
 * @returns {Promise<{valid: boolean, error: string|null, stationName: string|null}>}
 */
export async function validateLocation(lat, lon) {
  try {
    // Request just 1 day to minimize data transfer
    const now = new Date();
    const tomorrow = new Date(now.getTime() + 24 * 60 * 60 * 1000);

    const params = new URLSearchParams({
      tide_request: 'locationdata',
      lat: lat.toString(),
      lon: lon.toString(),
      fromtime: formatTime(now),
      totime: formatTime(tomorrow),
      datatype: 'TAB',
      dst: '1',
      refcode: 'CD',
      lang: 'en'
    });

    const response = await fetch(`${API_URL}?${params}`, {
      method: 'GET',
      headers: {
        'Accept': 'text/xml'
      }
    });

    if (!response.ok) {
      return {
        valid: false,
        error: `API error: ${response.status} ${response.statusText}`,
        stationName: null
      };
    }

    const xml = await response.text();

    // Check if XML contains tide data
    // Kartverket returns XML with <waterlevel> elements if data exists
    const hasTideData = xml.includes('<waterlevel') || 
                        xml.includes('type="high"') || 
                        xml.includes('type="low"');

    if (!hasTideData) {
      return {
        valid: false,
        error: 'No tide data available at this location',
        stationName: null
      };
    }

    // Try to extract station/location name
    const stationName = extractStationName(xml);

    return {
      valid: true,
      error: null,
      stationName
    };

  } catch (error) {
    console.error('[Validator] Error validating location:', error);
    return {
      valid: false,
      error: `Validation failed: ${error.message}`,
      stationName: null
    };
  }
}

/**
 * Extract station name from XML response
 */
function extractStationName(xml) {
  try {
    // Parse XML to get location name
    const parser = new DOMParser();
    const xmlDoc = parser.parseFromString(xml, 'text/xml');
    
    // Try to get location name from various possible elements
    const locationElement = xmlDoc.querySelector('location[name]');
    if (locationElement) {
      return locationElement.getAttribute('name');
    }

    const stationElement = xmlDoc.querySelector('locationdata[name]');
    if (stationElement) {
      return stationElement.getAttribute('name');
    }

    return null;
  } catch (error) {
    console.warn('[Validator] Could not extract station name:', error);
    return null;
  }
}

/**
 * Debounce function for validation requests
 */
export function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}
