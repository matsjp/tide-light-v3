# AGENTS.md

This file contains guidelines for agentic coding agents working in this repository.

## Project Overview

This is a Python tide light application that fetches tide data from the Kartverket API and manages it with a SQLite cache. The system uses a scheduler to periodically update tide data and supports configuration changes at runtime.

**IMPORTANT**: The application is designed to run on a Raspberry Pi. All code must be optimized for this resource-constrained environment:
- Minimize memory usage
- Avoid CPU-intensive operations where possible
- Consider power consumption
- Use efficient database queries
- Keep dependencies lightweight

## Project Structure

The repository is organized into separate app and web directories:

```
tide-light-v3/
├── app/                    # Python application (run on Raspberry Pi)
├── web/                    # Web configuration interface  
└── docs/                   # Shared documentation
```

**IMPORTANT**: All Python commands must be run from the `app/` directory:

```bash
cd app
python main.py
```

## Platform Considerations

### Windows Development

When developing on Windows, be aware of the following:

- **DO NOT use `/dev/null`** for output redirection in bash commands
  - Windows does not have `/dev/null`
  - Using `> /dev/null` or `2> nul` may create a literal file named `nul` in the project directory
  - Instead, handle output in Python using `subprocess.DEVNULL` or capture output programmatically
  
- **Line Endings**: Git will convert LF to CRLF on Windows. This is normal and handled by Git's `core.autocrlf` setting.

- **Path Separators**: Use `os.path.join()` or `pathlib.Path` for cross-platform path handling instead of hardcoding `/` or `\`.

### Raspberry Pi Production

The production environment is Linux-based (Raspberry Pi OS). Ensure all features work on both platforms during development.

## Build/Test Commands

### Running Tests
```bash
# IMPORTANT: Run from app/ directory
cd app

# Run all tests
python -m unittest tests.tide_calculator_test tests.tide_scheduler_test

# Run a specific test file
python -m unittest tests.tide_scheduler_test
python -m unittest tests.tide_calculator_test

# Run a specific test method
python -m unittest tests.tide_scheduler_test.TestTideUpdateScheduler.test_run_once_fetches_when_cache_missing
```

### Running the Application
```bash
# IMPORTANT: Run from app/ directory
cd app
python main.py
```

### Web Development
```bash
# Run from web/ directory
cd web
npm install           # First time only
npm run dev          # Start dev server
npm run build        # Production build
```

### Dependencies
```bash
# Install core dependencies
pip install kartverket_tide_api

# Install LED library (choose ONE based on your environment):

# For development/testing (Windows, macOS, or Linux without hardware):
pip install rpi-ws281x-mock

# For production on Raspberry Pi with actual LED strip:
pip install rpi_ws281x
```

**Important**: The mock and real libraries both provide the `rpi_ws281x` module and cannot be installed simultaneously. The mock library is a drop-in replacement for development and testing. Use `config.json` to set `"use_mock": true` for development or `"use_mock": false` for production.

## Code Style Guidelines

### Import Organization
- Standard library imports first (e.g., `import threading`, `from datetime import datetime`)
- Third-party imports second (e.g., `from kartverket_tide_api import TideApi`)
- Local imports third (e.g., `from tide_models import WaterLevel`)
- Each import group separated by a blank line
- Use `from module import specific` for specific imports
- Use `import module` for entire module usage

### Type Hints
- All function parameters and return values should have type hints
- Use `from typing import List, Optional, Dict, Any, Callable` as needed
- Use dataclasses for immutable data structures with `@dataclass(frozen=True)`
- Use Enums for fixed string values

### Naming Conventions
- **Classes**: PascalCase (e.g., `TideCacheManager`, `ConfigManager`)
- **Functions/Methods**: snake_case (e.g., `fetch_waterlevels`, `has_data_for_range`)
- **Variables**: snake_case (e.g., `current_lat`, `waterlevels`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `CONFIG_PATH`, `DB_PATH`)
- **Private members**: prefix with underscore (e.g., `_config`, `_lock`)

### Class Structure
- Use section comments with dashes to organize methods:
  ```python
  # -----------------------------
  # Public API
  # -----------------------------
  
  # -----------------------------
  # Internal methods
  # -----------------------------
  ```

### Error Handling
- Use specific exception types (`FileNotFoundError`, `ValueError`)
- Handle API errors gracefully (e.g., unknown enum values)
- Use try/except blocks for parsing and external API calls
- Log meaningful error messages with context

### Threading and Concurrency
- Use `threading.Lock()` for thread safety
- Always acquire locks when modifying shared state
- Use `with self.lock:` context manager for lock acquisition
- SQLite connections should use `check_same_thread=False` for cross-thread usage
- Use `threading.Event()` for stop signals in background threads

### Database Patterns
- Use SQLite with `sqlite3.Row` factory for dictionary-like access
- Always use parameterized queries to prevent SQL injection
- Use `with self.conn:` context manager for transactions
- Create indexes on frequently queried columns
- Store metadata in separate table for configuration tracking

### Configuration Management
- Use JSON configuration files with clear structure
- Support runtime configuration updates with listener pattern
- Use deep copies when passing configuration to prevent mutation
- Validate configuration on load

### Testing Patterns
- Design the code to be easily testable
- Use `unittest.TestCase` for all test classes
- Use `unittest.mock.MagicMock` for external dependencies
- Set up test data in `setUp()` method
- Use descriptive test method names that explain the scenario
- Test both success and failure cases
- Mock external API calls and database operations

### File Organization
- Keep related functionality in separate modules
- Use clear, descriptive module names (e.g., `tide_fetcher.py`, `config_manager.py`)
- Place all Python code in `app/` directory
- Place all tests in `app/tests/` directory
- Place all web code in `web/src/` directory
- Place shared documentation in `docs/` directory
- Use `if __name__ == "__main__":` guard for main execution

### Documentation
- Use docstrings for public methods explaining purpose and parameters
- Keep comments concise and focused on why, not what
- Use section comments to organize complex classes
- Document configuration structure in JSON files

### Constants and Magic Numbers
- Define constants at module level for repeated values
- Avoid magic numbers in code (e.g., `interval_days * 24 * 60 * 60`)
- Use descriptive names for configuration keys

### Data Structures
- Use dataclasses for immutable data with `@dataclass(frozen=True)`
- Use Enums for fixed string values
- Prefer lists over other collections when order matters
- Use dictionaries for configuration and metadata storage

## Architecture Patterns

### Dependency Injection
- Pass dependencies through constructor parameters
- Avoid importing modules directly in classes when possible
- Use interfaces/abstract base classes for testability

### Observer Pattern
- Use listener callbacks for configuration changes
- Register listeners with `register_listener()` methods
- Notify listeners after state changes are complete

### Caching Strategy
- Cache external API responses in SQLite
- Implement cache invalidation on configuration changes
- Check cache before making external API calls
- Store metadata to track cache state

## Common Pitfalls to Avoid

- Don't use global variables for configuration
- Always lock before modifying shared state
- Don't ignore thread safety in database operations
- Handle all API errors gracefully
- Don't hardcode file paths - use constants
- Always validate external data before using it

## WS281x LED Strip Behavior

The application controls a WS281x LED strip to visualize tide state in real-time.

### LED Physical Layout

The LED strip has a dynamic layout based on configuration:
- **Top LED**: Direction indicator for rising tide
- **Middle LEDs**: Tide level indicators (count - 2 LEDs)
  - **Always-Blue LED**: Last middle LED (serves as reference point)
  - **Dynamic LEDs**: Remaining middle LEDs (count - 3) show tide progression
- **Bottom LED**: Direction indicator for falling tide

### Invert Flag

The `invert` flag in `led_strip` configuration determines LED orientation:
- **`invert: false`** (standard orientation):
  - LED 0 = Top
  - LED (count-1) = Bottom
  - Middle LEDs fill from bottom up
- **`invert: true`** (reversed strip):
  - LED 0 = Bottom
  - LED (count-1) = Top  
  - Middle LEDs fill from top down

This accommodates LED strips installed in different orientations.

### Tide Direction Indicators

- **Tide Rising**: Top LED = GREEN `(0, 255, 0)`, Bottom LED = OFF `(0, 0, 0)`
- **Tide Falling**: Top LED = OFF `(0, 0, 0)`, Bottom LED = RED `(255, 0, 0)`

### Tide Level Visualization

Middle LEDs display tide progression between low and high tide:

**Progress Calculation:**
```
progress = (current_time - last_tide_event_time) / (next_tide_event_time - last_tide_event_time)
```
Progress ranges from 0.0 (low tide) to 1.0 (high tide).

**Color Mapping:**
- **At Low Tide** (progress = 0.0):
  - Dynamic middle LEDs: PURPLE `(128, 0, 128)`
  - Always-blue LED: BLUE `(0, 0, 255)` (always)

- **At High Tide** (progress = 1.0):
  - All middle LEDs: BLUE `(0, 0, 255)`

- **Transition** (0.0 < progress < 1.0):
  - LEDs fill with BLUE from bottom upward (or top downward if inverted)
  - Remaining LEDs stay PURPLE
  - Always-blue LED always remains BLUE

**Always-Blue LED Rule**: The last middle LED (closest to bottom indicator) always remains BLUE regardless of tide state, serving as a visual reference point.

### Animation Patterns

Controlled by `config.color.pattern`:

**Pattern: "none"** (Solid colors)
- Display tide state colors directly
- Update when tide state changes
- No moving effects

**Pattern: "wave"** (Animated wave effect)
- Base colors same as solid mode
- 3-LED wave travels through dynamic middle section (excludes always-blue LED)
- **Wave Direction**: 
  - UP (toward top) when tide rising
  - DOWN (toward bottom) when tide falling
- **Wave Appearance**: Shifts color (hue/saturation), not brightness
  - Blue → Cyan (adds green component)
  - Purple → Magenta (enhances blue component)
  - Leading LED: strongest color shift
  - Middle LED: medium color shift
  - Trailing LED: subtle color shift
- **Wave Speed**: Controlled by `config.color.wave_speed` (seconds per step)
  - `0.5` = move 1 position every 0.5 seconds
- **Wave Cycling**: Wraps around the dynamic middle LED range continuously

### Error State (No Tide Data Available)

When `TideCalculator` cannot determine current tide state:
- All LEDs blink RED `(255, 0, 0)`
- Blink rate: 1 Hz (0.5s on, 0.5s off)
- Triggered when:
  - No cached tide data for current location
  - Unable to find previous or next tide event
  - Database query fails

### Direction Changes

Direction changes occur at tide event times:
- **At high tide**: Direction changes from RISING → FALLING
- **At low tide**: Direction changes from FALLING → RISING

**Transition Characteristics:**
- Direction indicators flip instantly
- Progress resets from ~100% to ~0% (or vice versa)
- Middle LED colors transition naturally with progress
- Wave animation reverses direction
- Visual change feels natural as progress gradually approaches 100%

### Runtime Updates

The light system responds immediately to configuration changes:
- **Location Change**: TideUpdateScheduler fetches new data, notifies visualizer, LEDs update within 1 second
- **Brightness Change**: Applied immediately via `set_brightness()`
- **Pattern Change**: Switches between "none" and "wave" modes on next loop iteration
- **Invert Change**: Recalculates LED positions, applies immediately
- **LED Count Change**: Recalculates middle LED count and positions

No restart required for any configuration change.

### Hardware Configuration (Hardcoded Constants)

The following values are hardcoded in `LightController`:
- **GPIO Pin**: 18 (PWM-capable pin on Raspberry Pi)
- **LED Frequency**: 800000 Hz (800 kHz, standard for WS281x)
- **DMA Channel**: 10 (avoids conflicts with audio)
- **Strip Type**: `WS2811_STRIP_GRB` (compatible with most WS281x variants)

### Cache and Location Management

**Single Location Database Model:**

The cache database stores tide data for exactly one location at a time. Location coordinates are stored in metadata, not in waterlevel rows.

**Database Schema:**
```sql
-- Waterlevels table (no lat/lon columns)
CREATE TABLE waterlevels (
    id INTEGER PRIMARY KEY,
    time TEXT NOT NULL UNIQUE,  -- UNIQUE constraint prevents duplicates
    flag TEXT NOT NULL
);

-- Metadata table stores current location
CREATE TABLE metadata (
    key TEXT PRIMARY KEY,  -- 'current_latitude', 'current_longitude'
    value TEXT
);
```

**Location Handling:**

1. **On Data Insert:** Location is stored in metadata (not in rows)
   - `insert_waterlevels(waterlevels, lat, lon)` stores lat/lon in metadata only
   - Uses `INSERT OR IGNORE` to handle duplicate times (weekly updates)

2. **On Location Change (Runtime):** All data and metadata cleared
   - Detected in `TideUpdateScheduler.on_config_updated()`
   - Calls `cache.invalidate_all()` which clears both waterlevels and location metadata
   - New data fetched and new location stored in metadata

3. **On Location Change (Offline):** Detected at startup
   - `main.py` compares config location to `cache.get_cached_location()`
   - If different or metadata missing → `cache.invalidate_all()` clears old data
   - Scheduler then fetches data for new location

4. **Cache Retrieval:** No location parameters needed
   - `get_waterlevels_in_range(start, end)` queries without lat/lon
   - `has_data_for_range(start, end)` checks without lat/lon
   - `is_empty()` returns True if no data OR no location metadata exists
   - Assumes all data in cache is for the current location

**Four Cases for Data Updates:**

1. **Startup with empty cache:** `is_empty()` returns True → fetch data
2. **Weekly scheduled update:** Missing future data → fetch and insert (duplicates ignored)
3. **Runtime location change:** Config change detected → invalidate all → fetch new
4. **Offline location change:** Startup detects mismatch → invalidate all → fetch new

**Data Flow:**
1. User changes location in config
2. TideUpdateScheduler detects change, calls `invalidate_all()` (clears data and metadata)
3. Scheduler fetches new location data, calls `insert_waterlevels()` (stores data and location metadata)
4. Scheduler notifies TideVisualizer via `on_tide_data_updated()`
5. Visualizer queries TideCalculator on next loop iteration
6. Calculator queries cache without location parameters (assumes current location)
7. LEDs update to show new location's tide state
