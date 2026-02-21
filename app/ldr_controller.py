"""Light Dependent Resistor controller for automatic brightness adjustment.

Uses RC timing circuit method (same as Tide Light v2) with RPi.GPIO.
"""

import threading
import time
import logging
from typing import Optional, Callable

# Import GPIO library
try:
    from RPi import GPIO
    LDR_AVAILABLE = True
except ImportError:
    LDR_AVAILABLE = False
    logging.warning("[LDR] RPi.GPIO not available - LDR disabled")

class LdrController:
    """
    Monitors ambient light via LDR using RC timing and adjusts LED brightness automatically.
    
    Features:
    - RC timing circuit (no ADC needed)
    - Double-sampling to prevent flickering
    - Configurable brightness range (5-255)
    - Thread-safe operation
    - Enable/disable via config
    - Restores configured brightness when disabled
    """
    
    def __init__(self, config: dict, on_brightness_change: Callable[[int], None]):
        """
        Args:
            config: Configuration dict with ldr settings and led_strip.brightness
            on_brightness_change: Callback to update LED brightness
        """
        self._enabled = config.get("ldr", {}).get("enabled", False)
        self._pin = config.get("ldr", {}).get("pin", 11)
        self._configured_brightness = config.get("led_strip", {}).get("brightness", 128)
        self._min_brightness = 5
        self._max_brightness = 255
        self._on_brightness_change = on_brightness_change
        
        # RC timing parameters (calibrated for typical LDR)
        self._min_ldr_count = 1
        self._max_ldr_count = 250000
        
        # Timing parameters
        self._poll_interval = 0.5  # Time between readings (seconds)
        self._debounce_delay = 1.0  # Delay before confirming change (seconds)
        
        # Threading
        self._thread = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        
        # State
        self._current_brightness = self._configured_brightness
        self._gpio_initialized = False
        
    def start(self):
        """Start LDR monitoring thread."""
        if not self._enabled:
            logging.info("[LDR] LDR disabled - not starting thread")
            return
        
        if not LDR_AVAILABLE:
            logging.warning("[LDR] RPi.GPIO not available - cannot start")
            return
        
        if self._thread and self._thread.is_alive():
            logging.warning("[LDR] Thread already running")
            return
        
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logging.info(f"[LDR] Monitoring thread started (pin {self._pin})")
    
    def stop(self):
        """Stop LDR monitoring thread and cleanup GPIO."""
        if self._thread and self._thread.is_alive():
            logging.info("[LDR] Stopping monitoring thread...")
            self._stop_event.set()
            self._thread.join(timeout=5)
            
            if self._thread.is_alive():
                logging.warning("[LDR] Thread did not stop gracefully within timeout")
            else:
                logging.info("[LDR] Thread stopped")
        
        # Cleanup GPIO
        self._cleanup_gpio()
    
    def _run(self):
        """Main monitoring loop (runs in separate thread)."""
        logging.info("[LDR] Entering monitoring loop")
        
        if not LDR_AVAILABLE:
            logging.error("[LDR] GPIO library not available")
            return
        
        try:
            # GPIO setup - check if already initialized
            if not self._gpio_initialized:
                try:
                    GPIO.setmode(GPIO.BCM)
                    self._gpio_initialized = True
                except ValueError as e:
                    # GPIO mode already set - this is OK
                    logging.debug(f"[LDR] GPIO mode already set: {e}")
                    self._gpio_initialized = True
            
            while not self._stop_event.is_set():
                try:
                    # Read LDR count using RC timing
                    ldr_count = self._rc_time(self._pin)
                    new_brightness = self._scale_and_invert(ldr_count)
                    
                    # If brightness changed significantly, debounce and double-check
                    if abs(new_brightness - self._current_brightness) > 0:
                        time.sleep(self._debounce_delay)
                        if self._stop_event.is_set():
                            break
                        
                        # Second reading for confirmation
                        ldr_count_2 = self._rc_time(self._pin)
                        new_brightness_2 = self._scale_and_invert(ldr_count_2)
                        
                        # If both readings agree exactly, update immediately
                        if new_brightness == new_brightness_2:
                            logging.info(f"[LDR] Light change detected - Count: {ldr_count} → Brightness: {self._current_brightness} → {new_brightness}")
                            with self._lock:
                                self._current_brightness = new_brightness
                            self._on_brightness_change(new_brightness)
                        
                        # If both are dimmer than current, use averaged transition
                        elif new_brightness < self._current_brightness and new_brightness_2 < self._current_brightness:
                            avg_brightness = self._current_brightness - int((self._current_brightness - new_brightness) / 2)
                            logging.info(f"[LDR] Gradual dimming: {self._current_brightness} → {avg_brightness} (target: {new_brightness})")
                            with self._lock:
                                self._current_brightness = avg_brightness
                            self._on_brightness_change(avg_brightness)
                        
                        # If both are brighter than current, use averaged transition
                        elif new_brightness > self._current_brightness and new_brightness_2 > self._current_brightness:
                            avg_brightness = self._current_brightness + int((new_brightness - self._current_brightness) / 2)
                            logging.info(f"[LDR] Gradual brightening: {self._current_brightness} → {avg_brightness} (target: {new_brightness})")
                            with self._lock:
                                self._current_brightness = avg_brightness
                            self._on_brightness_change(avg_brightness)
                        else:
                            # Readings disagree - skip this cycle
                            logging.debug(f"[LDR] Inconsistent readings ({new_brightness} vs {new_brightness_2}), skipping")
                    
                    # Sleep before next cycle
                    time.sleep(self._poll_interval)
                    
                except Exception as e:
                    logging.error(f"[LDR] Error in monitoring loop: {e}", exc_info=True)
                    time.sleep(5.0)  # Back off on errors
        
        except Exception as e:
            logging.error(f"[LDR] Fatal error in monitoring thread: {e}", exc_info=True)
        
        finally:
            # Cleanup GPIO on exit
            self._cleanup_gpio()
    
    def _rc_time(self, pin: int) -> int:
        """
        Measure RC time by charging capacitor and counting time to discharge.
        
        Returns:
            Count value (higher = darker, lower = brighter)
        """
        if not LDR_AVAILABLE:
            return 0
        
        count = 0
        
        try:
            # Output on the pin to discharge capacitor
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)
            time.sleep(0.1)
            
            # Change pin to input
            GPIO.setup(pin, GPIO.IN)
            
            # Count until pin goes high (capacitor charged)
            while GPIO.input(pin) == GPIO.LOW and count < self._max_ldr_count:
                count += 1
        
        except Exception as e:
            logging.error(f"[LDR] Error in RC timing: {e}")
            return self._min_ldr_count  # Return minimum on error
        
        return count
    
    def _cleanup_gpio(self):
        """Cleanup GPIO pins safely."""
        if LDR_AVAILABLE and self._gpio_initialized:
            try:
                GPIO.cleanup(self._pin)
                logging.debug("[LDR] GPIO cleanup completed")
            except Exception as e:
                logging.warning(f"[LDR] Error during GPIO cleanup: {e}")
            finally:
                self._gpio_initialized = False
    
    def _scale_and_invert(self, ldr_count: int) -> int:
        """
        Map LDR count to brightness with inverted scaling.
        
        Higher count (dark) → Higher brightness (bright LEDs)
        Lower count (bright) → Lower brightness (dim LEDs)
        
        Args:
            ldr_count: RC time count from LDR
            
        Returns:
            Brightness value (5-255)
        """
        # Clamp to valid range
        if ldr_count > self._max_ldr_count:
            ldr_count = self._max_ldr_count
        
        # Linear scaling
        scaled = int(((ldr_count - self._min_ldr_count) * (self._max_brightness - self._min_brightness) /
                     (self._max_ldr_count - self._min_ldr_count)) + self._min_brightness)
        
        # Clamp to brightness range
        if scaled < self._min_brightness:
            scaled = self._min_brightness
        if scaled > self._max_brightness:
            scaled = self._max_brightness
        
        # Invert: dark room = bright LEDs, bright room = dim LEDs
        inverted = self._max_brightness + self._min_brightness - scaled
        
        return inverted
    
    def on_config_updated(self, config: dict):
        """Handle config changes (enable/disable)."""
        new_enabled = config.get("ldr", {}).get("enabled", False)
        new_configured_brightness = config.get("led_strip", {}).get("brightness", 128)
        
        # Update configured brightness
        with self._lock:
            self._configured_brightness = new_configured_brightness
        
        # Check if LDR was enabled/disabled
        if new_enabled != self._enabled:
            logging.info(f"[LDR] Enabled changed: {self._enabled} → {new_enabled}")
            self._enabled = new_enabled
            
            if self._enabled:
                # Start LDR control
                self.start()
            else:
                # Stop LDR and restore configured brightness
                self.stop()
                logging.info(f"[LDR] Restoring configured brightness: {self._configured_brightness}")
                self._on_brightness_change(self._configured_brightness)
    
    def get_status(self) -> dict:
        """Get current LDR status for diagnostics."""
        with self._lock:
            return {
                "enabled": self._enabled,
                "available": LDR_AVAILABLE,
                "current_brightness": self._current_brightness,
                "configured_brightness": self._configured_brightness,
                "thread_alive": self._thread.is_alive() if self._thread else False
            }
