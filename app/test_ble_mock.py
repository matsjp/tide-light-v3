"""
Simple test script to verify BLE mock functionality.
Tests that file watcher detects config changes and triggers updates.
"""

import json
import time
from pathlib import Path

from config_manager import ConfigManager
from ble import BLEManager
from tide_calculator import TideCalculator
from tide_cache_manager import TideCacheManager

CONFIG_PATH = "config.json"
DB_PATH = "tide_cache.sqlite"


def test_ble_mock():
    """Test BLE mock server with file watcher."""
    print("=" * 60)
    print("BLE Mock Test")
    print("=" * 60)
    
    # Initialize components
    print("\n1. Initializing components...")
    config_manager = ConfigManager(CONFIG_PATH)
    cache = TideCacheManager(DB_PATH)
    calculator = TideCalculator(cache)
    
    config = config_manager.get_config()
    print(f"   Initial brightness: {config['led_strip']['brightness']}")
    print(f"   BLE mock enabled: {config['bluetooth']['use_fake_library']}")
    
    # Track config changes
    config_updated = []
    
    def on_config_update(cfg):
        config_updated.append(cfg)
        print(f"\n   [OK] Config listener triggered!")
        print(f"   New brightness: {cfg['led_strip']['brightness']}")
    
    config_manager.register_listener(on_config_update)
    
    # Create and start BLE manager
    print("\n2. Starting BLE manager...")
    ble_manager = BLEManager(
        config_manager=config_manager,
        tide_calculator=calculator,
        tide_cache=cache,
        config_path=CONFIG_PATH
    )
    ble_manager.start()
    print("   BLE manager started")
    
    # Wait a bit for file watcher to initialize
    time.sleep(1)
    
    # Test 1: Modify brightness
    print("\n3. Test 1: Modifying brightness via file edit...")
    print("   Reading config file...")
    with open(CONFIG_PATH, 'r') as f:
        config_data = json.load(f)
    
    old_brightness = config_data['led_strip']['brightness']
    new_brightness = 100 if old_brightness != 100 else 150
    
    print(f"   Changing brightness: {old_brightness} -> {new_brightness}")
    config_data['led_strip']['brightness'] = new_brightness
    
    print("   Writing modified config...")
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config_data, f, indent=2)
    
    print("   Waiting for file watcher to detect change...")
    time.sleep(2)
    
    # Check if update was triggered
    if len(config_updated) > 0:
        print("   [OK] SUCCESS: Config update detected!")
        print(f"   Brightness updated to: {config_updated[-1]['led_strip']['brightness']}")
    else:
        print("   [X] FAILED: No config update detected")
    
    # Test 2: Modify pattern
    print("\n4. Test 2: Modifying pattern via file edit...")
    config_updated.clear()
    
    with open(CONFIG_PATH, 'r') as f:
        config_data = json.load(f)
    
    old_pattern = config_data['color']['pattern']
    new_pattern = "none" if old_pattern == "wave" else "wave"
    
    print(f"   Changing pattern: {old_pattern} -> {new_pattern}")
    config_data['color']['pattern'] = new_pattern
    
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config_data, f, indent=2)
    
    print("   Waiting for file watcher to detect change...")
    time.sleep(2)
    
    if len(config_updated) > 0:
        print("   [OK] SUCCESS: Config update detected!")
        print(f"   Pattern updated to: {config_updated[-1]['color']['pattern']}")
    else:
        print("   [X] FAILED: No config update detected")
    
    # Restore original config
    print("\n5. Restoring original brightness...")
    with open(CONFIG_PATH, 'r') as f:
        config_data = json.load(f)
    
    config_data['led_strip']['brightness'] = old_brightness
    config_data['color']['pattern'] = old_pattern
    
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config_data, f, indent=2)
    
    time.sleep(1)
    
    # Stop BLE manager
    print("\n6. Stopping BLE manager...")
    ble_manager.stop()
    print("   BLE manager stopped")
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)


if __name__ == "__main__":
    test_ble_mock()
