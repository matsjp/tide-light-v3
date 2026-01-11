"""
BLE configuration interface for Tide Light.

This module provides a BLE GATT server for runtime configuration with support
for both real hardware (Raspberry Pi with bluezero) and mock testing (file watcher).

Key Features:
- Conditional imports - no BLE libraries loaded when mocked
- File watcher for local testing (only active when use_fake_library=true)
- Thread-safe configuration updates
- Status reporting with tide state information

Usage:
    from ble import BLEManager
    
    ble_manager = BLEManager(config_manager, tide_calculator, tide_cache)
    ble_manager.start()
"""

from .ble_manager import BLEManager

__all__ = ['BLEManager']
