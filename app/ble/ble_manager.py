"""
BLE Manager for Tide Light.

Factory/dispatcher that creates either a real BLE server or mock server
based on configuration. Uses lazy imports to avoid loading BLE libraries
when in mock mode.

This is the main entry point for the BLE subsystem.
"""

from typing import Optional

from config_manager import ConfigManager
from tide_calculator import TideCalculator
from tide_cache_manager import TideCacheManager
from rtc_manager import RTCManager


class BLEManager:
    """
    Manages BLE server lifecycle.
    Creates real or mock server based on configuration.
    Provides unified interface for main.py.
    """
    
    def __init__(
        self,
        config_manager: ConfigManager,
        tide_calculator: TideCalculator,
        tide_cache: TideCacheManager,
        config_path: str = "config.json",
        rtc_manager: Optional[RTCManager] = None
    ):
        """
        Initialize BLE manager.
        
        Args:
            config_manager: ConfigManager instance
            tide_calculator: TideCalculator for status
            tide_cache: TideCacheManager for status
            config_path: Path to config.json (for mock watcher)
            rtc_manager: Optional RTCManager for time sync
        """
        self._config_manager = config_manager
        self._tide_calculator = tide_calculator
        self._tide_cache = tide_cache
        self._config_path = config_path
        self._rtc_manager = rtc_manager
        
        # Determine if we should use mock or real
        config = config_manager.get_config()
        self._use_mock = config.get("bluetooth", {}).get("use_fake_library", False)
        
        # Server instance (created in start())
        self._server: Optional[any] = None
        
        print(f"[BLE Manager] Initialized (mock={self._use_mock})")
    
    def start(self) -> None:
        """Start BLE server (real or mock based on config)."""
        if self._server is not None:
            print("[BLE Manager] Already started")
            return
        
        print(f"[BLE Manager] Starting BLE server (mock={self._use_mock})...")
        
        # Create appropriate server with lazy imports
        self._server = self._create_server()
        
        # Start server
        self._server.start()
        
        print("[BLE Manager] BLE server started successfully")
    
    def stop(self) -> None:
        """Stop BLE server and cleanup."""
        if self._server is None:
            print("[BLE Manager] Not started, nothing to stop")
            return
        
        print("[BLE Manager] Stopping BLE server...")
        
        try:
            self._server.stop()
        except Exception as e:
            print(f"[BLE Manager] Error stopping server: {e}")
        finally:
            self._server = None
        
        print("[BLE Manager] BLE server stopped")
    
    def is_running(self) -> bool:
        """Check if BLE server is running."""
        if self._server is None:
            return False
        
        # Check if server has is_running method
        if hasattr(self._server, 'is_running'):
            return self._server.is_running()
        
        # Otherwise assume running if server exists
        return True
    
    def _create_server(self):
        """
        Create server instance with lazy imports.
        
        Returns:
            BLEServer or BLEMockServer instance
        """
        if self._use_mock:
            # Lazy import mock server (no BLE libraries)
            from ble.ble_mock_server import BLEMockServer
            
            print("[BLE Manager] Creating MOCK server with file watcher")
            return BLEMockServer(
                config_manager=self._config_manager,
                config_path=self._config_path
            )
        else:
            # Lazy import real server (requires pybleno)
            try:
                from ble.ble_server_pybleno import BLEServerPybleno
                from ble.ble_config_handler import BLEConfigHandler
                from ble.ble_status_provider import BLEStatusProvider
                from network.wifi_manager import WiFiManager
                from ble.wifi_handler import WiFiHandler
            except ImportError as e:
                print(f"[BLE Manager] ERROR: Failed to import BLE libraries: {e}")
                print("[BLE Manager] Make sure 'pybleno' is installed: pip install pybleno")
                print("[BLE Manager] Or set 'bluetooth.use_fake_library' to true in config.json")
                raise
            
            print("[BLE Manager] Creating REAL BLE server with pybleno")
            
            # Create dependencies
            config_handler = BLEConfigHandler(self._config_manager)
            status_provider = BLEStatusProvider(
                self._tide_calculator,
                self._tide_cache
            )
            
            # Initialize WiFi if available
            wifi_handler = None
            try:
                wifi_manager = WiFiManager()
                if wifi_manager.is_wifi_available():
                    wifi_handler = WiFiHandler(wifi_manager)
                    print("[BLE Manager] WiFi support enabled")
                else:
                    print("[BLE Manager] WiFi hardware not available, WiFi characteristics disabled")
            except Exception as e:
                print(f"[BLE Manager] WARNING: Failed to initialize WiFi: {e}")
                print("[BLE Manager] WiFi characteristics will be disabled")
            
            # Create and return real server
            return BLEServerPybleno(
                config_manager=self._config_manager,
                config_handler=config_handler,
                status_provider=status_provider,
                wifi_handler=wifi_handler,
                rtc_manager=self._rtc_manager
            )
