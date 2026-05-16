import json
import logging
import threading
from copy import deepcopy
from pathlib import Path
from typing import Callable, Dict, Any, List


class ConfigManager:
    # Default configuration template (Production/Raspberry Pi settings)
    DEFAULT_CONFIG = {
        "config_version": 1,
        "bluetooth": {
            "use_fake_library": False,  # Real BLE on Raspberry Pi
            "device_name": "Tide Light"
        },
        "tide": {
            "location": {
                "latitude": 69.966,
                "longitude": 23.272
            }
        },
        "led_strip": {
            "count": 60,
            "brightness": 50,
            "invert": False,
            "use_mock": False  # Real LED strip on Raspberry Pi
        },
        "ldr": {
            "enabled": False,
            "pin": 11
        },
        "color": {
            "format": "rgb",
            "pattern": "wave",
            "wave_speed": 0.5
        }
    }

    def __init__(self, config_path: str):
        self._config_path = Path(config_path)
        self._lock = threading.Lock()
        self._config: Dict[str, Any] = {}
        self._listeners: List[Callable[[Dict[str, Any]], None]] = []

        self._load_from_disk()

    # ---------- Public API ----------

    def get_config(self) -> Dict[str, Any]:
        """Return a deep copy of the current in-memory config."""
        with self._lock:
            return deepcopy(self._config)

    def update_config(self, new_config: Dict[str, Any]) -> None:
        """
        Replace the current config with a new one.
        This is the entry point BLE or other interfaces should use.
        """
        with self._lock:
            self._config = deepcopy(new_config)
            self._persist_to_disk()

        self._notify_listeners()

    def register_listener(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Register a callback that will be called after config changes.
        The callback receives the full updated config.
        """
        self._listeners.append(callback)

    def reset_to_defaults(self) -> None:
        """
        Reset configuration to factory defaults.
        This triggers cache invalidation and notifies all listeners.
        """
        with self._lock:
            self._config = deepcopy(self.DEFAULT_CONFIG)
            self._persist_to_disk()

        self._notify_listeners()

    # ---------- Internal ----------

    def _load_from_disk(self) -> None:
        if not self._config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self._config_path}")

        logging.debug(f"[ConfigManager] Loading configuration from {self._config_path}")
        with self._config_path.open("r", encoding="utf-8") as f:
            self._config = json.load(f)
        logging.debug(f"[ConfigManager] Configuration loaded successfully")

    def _persist_to_disk(self) -> None:
        tmp_path = self._config_path.with_suffix(".tmp")

        logging.debug(f"[ConfigManager] Persisting configuration to {self._config_path}")
        with tmp_path.open("w", encoding="utf-8") as f:
            json.dump(self._config, f, indent=2)

        tmp_path.replace(self._config_path)
        logging.debug(f"[ConfigManager] Configuration persisted successfully")

    def _notify_listeners(self) -> None:
        config_snapshot = self.get_config()
        logging.debug(f"[ConfigManager] Notifying {len(self._listeners)} listener(s) of configuration change")
        for listener in self._listeners:
            listener(config_snapshot)