/**
 * Tide Data Validator - Validates Pi's tide data against Kartverket API
 * 
 * Automatically compares Pi's current and next tide events with API data
 * when BLE connection is established. Displays warning if times differ by >5 minutes.
 */

const API_URL = 'https://vannstand.kartverket.no/tideapi.php';
const TOLERANCE_MINUTES = 5;

/**
 * Format date for Kartverket API (YYYY-MM-DDTHH:MM)
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
 * Fetch tide events from Kartverket API
 * @param {number} lat - Latitude
 * @param {number} lon - Longitude
 * @returns {Promise<Array<{time: Date, type: string}>>} Array of tide events
 */
async function fetchTideDataFromAPI(lat, lon) {
  try {
    // Request 48 hours of data to ensure we get current and next events
    const now = new Date();
    const future = new Date(now.getTime() + 48 * 60 * 60 * 1000);

    const params = new URLSearchParams({
      tide_request: 'locationdata',
      lat: lat.toString(),
      lon: lon.toString(),
      fromtime: formatTime(now),
      totime: formatTime(future),
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
      throw new Error(`API error: ${response.status} ${response.statusText}`);
    }

    const xml = await response.text();
    return parseTideEvents(xml);

  } catch (error) {
    console.error('[TideValidator] Error fetching tide data:', error);
    throw error;
  }
}

/**
 * Parse tide events from Kartverket XML response
 * @param {string} xml - XML response from API
 * @returns {Array<{time: Date, type: string}>} Array of tide events
 */
function parseTideEvents(xml) {
  try {
    const parser = new DOMParser();
    const xmlDoc = parser.parseFromString(xml, 'text/xml');
    
    // Kartverket API uses 'waterlevel' elements with 'flag' and 'time' attributes
    const waterLevelElements = xmlDoc.querySelectorAll('waterlevel');
    const events = [];

    waterLevelElements.forEach(element => {
      const flag = element.getAttribute('flag'); // 'high' or 'low'
      const timeStr = element.getAttribute('time');
      
      if ((flag === 'high' || flag === 'low') && timeStr) {
        // Parse ISO 8601 time string
        const time = new Date(timeStr);
        events.push({ time, type: flag });
      }
    });

    // Sort by time
    events.sort((a, b) => a.time - b.time);
    
    console.log('[TideValidator] Parsed tide events:', events.length);
    return events;

  } catch (error) {
    console.error('[TideValidator] Error parsing tide events:', error);
    throw error;
  }
}

/**
 * Find next tide event from API data relative to now
 * @param {Array<{time: Date, type: string}>} events - Sorted array of tide events
 * @returns {Object|null} Next future tide event
 */
function findNextEvent(events) {
  const now = new Date();

  for (let i = 0; i < events.length; i++) {
    if (events[i].time > now) {
      return events[i];
    }
  }

  return null;
}

/**
 * Compare two tide events with time tolerance
 * @param {Object} piEvent - Event from Pi (time: string ISO8601, flag: string)
 * @param {Object} apiEvent - Event from API (time: Date, type: string)
 * @param {number} toleranceMinutes - Allowed time difference in minutes
 * @returns {{matches: boolean, timeDiffMinutes: number}} Comparison result
 */
function compareTideEvents(piEvent, apiEvent, toleranceMinutes) {
  if (!piEvent || !apiEvent) {
    return { matches: false, timeDiffMinutes: null };
  }

  // Parse Pi event time (ISO 8601 string)
  const piTime = new Date(piEvent.time);
  const apiTime = apiEvent.time;

  // Calculate time difference in minutes
  const timeDiffMs = Math.abs(piTime - apiTime);
  const timeDiffMinutes = Math.round(timeDiffMs / (60 * 1000));

  // Check if types match (high/low)
  const typeMatches = piEvent.flag === apiEvent.type;

  // Time must be within tolerance AND types must match
  const matches = timeDiffMinutes <= toleranceMinutes && typeMatches;

  return { matches, timeDiffMinutes, typeMatches };
}

/**
 * Main validation function - compares Pi's tide data with Kartverket API
 * @param {Object} piStatus - Status object from BLE containing tide and cache data
 * @returns {Promise<Object>} Validation result with status and details
 */
export async function validatePiTideData(piStatus) {
  console.log('[TideValidator] Starting validation...');

  try {
    // Check if tide data is available
    if (!piStatus.tide || !piStatus.tide.available) {
      return {
        status: 'unavailable',
        message: 'No tide data available from Pi'
      };
    }

    // Check if cache has location
    if (!piStatus.cache || !piStatus.cache.has_data) {
      return {
        status: 'unavailable',
        message: 'No cached location data'
      };
    }

    const lat = piStatus.cache.latitude;
    const lon = piStatus.cache.longitude;

    if (!lat || !lon) {
      return {
        status: 'unavailable',
        message: 'Invalid location coordinates'
      };
    }

    // Fetch tide events from API
    const apiEvents = await fetchTideDataFromAPI(lat, lon);

    if (apiEvents.length === 0) {
      return {
        status: 'error',
        message: 'No tide events returned from API'
      };
    }

    // Find next event from API
    const apiNext = findNextEvent(apiEvents);

    // Check if we found the next event
    if (!apiNext) {
      return {
        status: 'error',
        message: 'No future tide events found in API data'
      };
    }

    // Compare next event only
    const nextComparison = compareTideEvents(
      piStatus.tide.next_event,
      apiNext,
      TOLERANCE_MINUTES
    );

    console.log('[TideValidator] Next event comparison:', nextComparison);

    // Determine overall validation status
    if (nextComparison.matches) {
      return {
        status: 'valid',
        message: 'Tide data matches API (within ±5 minutes)',
        details: {
          nextEvent: {
            piTime: piStatus.tide.next_event.time,
            apiTime: apiNext.time.toISOString(),
            diffMinutes: nextComparison.timeDiffMinutes
          }
        }
      };
    } else {
      // Build detailed mismatch message
      const mismatches = [];
      
      if (!nextComparison.typeMatches) {
        mismatches.push(`Next event type mismatch (Pi: ${piStatus.tide.next_event.flag}, API: ${apiNext.type})`);
      } else {
        mismatches.push(`Next event time differs by ${nextComparison.timeDiffMinutes} minutes`);
      }

      return {
        status: 'mismatch',
        message: 'Tide data differs from API',
        details: {
          mismatches,
          nextEvent: {
            piTime: piStatus.tide.next_event.time,
            piType: piStatus.tide.next_event.flag,
            apiTime: apiNext.time.toISOString(),
            apiType: apiNext.type,
            diffMinutes: nextComparison.timeDiffMinutes,
            typeMatches: nextComparison.typeMatches
          }
        }
      };
    }

  } catch (error) {
    console.error('[TideValidator] Validation error:', error);
    return {
      status: 'error',
      message: `Validation failed: ${error.message}`
    };
  }
}
