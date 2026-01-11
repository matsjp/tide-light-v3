"""
BLE Mock Server for Tide Light - File Watcher Implementation.

Watches config.json for manual changes and applies them via ConfigManager.
Only active when bluetooth.use_fake_library = true.
Avoids infinite loops by detecting self-generated updates.

NO BLE libraries imported in this module.
"""

import json
import time
import threading
from pathlib import Path
from typing import Optional

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent

from config_manager import ConfigManager


class ConfigFileHandler(FileSystemEventHandler):
    """
    Handler for config.json file modification events.
    Debounces rapid changes and avoids infinite loops.
    """
    
    def __init__(self, config_path: Path, config_manager: ConfigManager):
        """
        Initialize file handler.
        
        Args:
            config_path: Path to config.json
            config_manager: ConfigManager instance
        """
        super().__init__()
        self._config_path = config_path
        self._config_manager = config_manager
        self._last_modified_time = 0.0
        self._debounce_seconds = 0.5
        self._updating = False  # Flag to prevent loops
        self._lock = threading.Lock()
    
    def on_modified(self, event):
        """
        Handle file modification event.
        
        Args:
            event: FileModifiedEvent from watchdog
        """
        # Only handle file modifications (not directory)
        if not isinstance(event, FileModifiedEvent):
            return
        
        # Check if it's our config file
        if Path(event.src_path).resolve() != self._config_path.resolve():
            return
        
        # Debounce: ignore if modified too recently
        current_time = time.time()
        with self._lock:
            if current_time - self._last_modified_time < self._debounce_seconds:
                return
            
            # Check if we're currently updating (avoid loop)
            if self._updating:
                return
            
            self._last_modified_time = current_time
        
        # Wait a bit more to ensure file write is complete
        time.sleep(0.1)
        
        # Read and apply new config
        self._apply_config_update()
    
    def _apply_config_update(self):
        """Read config file and apply update via ConfigManager."""
        try:
            print("[BLE Mock] Config file changed, reading...")
            
            # Read new config from file
            with open(self._config_path, 'r', encoding='utf-8') as f:
                new_config = json.load(f)
            
            # Get current config from manager
            current_config = self._config_manager.get_config()
            
            # Check if config actually changed (avoid triggering on our own writes)
            if new_config == current_config:
                print("[BLE Mock] Config unchanged, ignoring")
                return
            
            # Set updating flag to prevent loop
            with self._lock:
                self._updating = True
            
            try:
                # Apply update via ConfigManager
                # This will trigger listeners and persist to disk
                print("[BLE Mock] Applying config update from file watcher")
                self._config_manager.update_config(new_config)
                print("[BLE Mock] Config update applied successfully")
            finally:
                # Clear updating flag after a delay
                # This allows ConfigManager's disk write to complete
                time.sleep(0.2)
                with self._lock:
                    self._updating = False
                    # Update last modified time to ignore our own write
                    self._last_modified_time = time.time()
        
        except json.JSONDecodeError as e:
            print(f"[BLE Mock] Error parsing config.json: {e}")
        except Exception as e:
            print(f"[BLE Mock] Error applying config update: {e}")
            with self._lock:
                self._updating = False


class BLEMockServer:
    """
    Mock BLE server using file watcher.
    Watches config.json and applies changes when detected.
    
    This allows testing BLE functionality locally by manually editing config.json.
    """
    
    def __init__(self, config_manager: ConfigManager, config_path: str = "config.json"):
        """
        Initialize mock BLE server.
        
        Args:
            config_manager: ConfigManager instance
            config_path: Path to config.json file
        """
        self._config_manager = config_manager
        self._config_path = Path(config_path).resolve()
        self._observer: Optional[Observer] = None
        self._handler: Optional[ConfigFileHandler] = None
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        print(f"[BLE Mock] Initialized with config path: {self._config_path}")
    
    def start(self):
        """Start file watcher in background thread."""
        if self._observer is not None:
            print("[BLE Mock] Already started")
            return
        
        print("[BLE Mock] Starting file watcher...")
        
        # Create handler
        self._handler = ConfigFileHandler(self._config_path, self._config_manager)
        
        # Create observer
        self._observer = Observer()
        self._observer.schedule(
            self._handler,
            str(self._config_path.parent),
            recursive=False
        )
        
        # Start observer
        self._observer.start()
        
        print(f"[BLE Mock] Watching {self._config_path} for changes")
        print("[BLE Mock] Edit config.json manually to trigger config updates")
    
    def stop(self):
        """Stop file watcher and cleanup."""
        if self._observer is None:
            return
        
        print("[BLE Mock] Stopping file watcher...")
        
        self._observer.stop()
        self._observer.join(timeout=2.0)
        self._observer = None
        self._handler = None
        
        print("[BLE Mock] File watcher stopped")
    
    def is_running(self) -> bool:
        """Check if file watcher is running."""
        return self._observer is not None and self._observer.is_alive()
