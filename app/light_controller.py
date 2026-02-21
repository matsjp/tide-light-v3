import threading
import sys
from typing import Dict, Any


class LightController:
    """
    Thread-safe controller for WS281x LED strip.
    Abstracts real hardware vs mock implementation based on config.
    """
    
    # Hardcoded hardware constants
    GPIO_PIN = 18
    LED_FREQ_HZ = 800000
    DMA_CHANNEL = 10
    STRIP_TYPE_GRB = 0x00100800  # WS2811_STRIP_GRB
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize LED controller with configuration.
        
        Args:
            config: Full configuration dictionary
        """
        self._config = config
        self._lock = threading.Lock()
        
        led_config = config["led_strip"]
        use_mock = led_config.get("use_mock", False)
        
        # Dynamically import correct library based on config
        # The mock library is a drop-in replacement that installs as 'rpi_ws281x'
        # On Linux with real hardware, the real rpi_ws281x library should be installed
        # On other platforms or when testing, rpi-ws281x-mock should be installed
        if use_mock:
            print("[LightController] Using MOCK library with console visualization")
            try:
                from led_mock_visualizer import PixelStripVisualizer as PixelStrip
            except ImportError as e:
                raise ImportError(
                    "Mock visualizer not found. Ensure led_mock_visualizer.py exists."
                ) from e
        else:
            print("[LightController] Using REAL library for hardware")
            try:
                from rpi_ws281x import PixelStrip
            except ImportError as e:
                raise ImportError(
                    "Real WS281x library not found. Install with: pip install rpi_ws281x"
                ) from e
        
        # Initialize strip with hardcoded hardware parameters
        self._strip = PixelStrip(
            num=led_config["count"],
            pin=self.GPIO_PIN,
            freq_hz=self.LED_FREQ_HZ,
            dma=self.DMA_CHANNEL,
            invert=led_config["invert"],
            brightness=led_config["brightness"],
            strip_type=self.STRIP_TYPE_GRB
        )
    
    # -----------------------------
    # Public API
    # -----------------------------
    
    def begin(self) -> None:
        """Initialize hardware. Must be called before use."""
        with self._lock:
            self._strip.begin()
        print("[LightController] LED strip initialized")
    
    def show(self) -> None:
        """Update LED strip with current pixel colors."""
        with self._lock:
            self._strip.show()
    
    def set_pixel(self, index: int, r: int, g: int, b: int) -> None:
        """
        Set color of a single pixel.
        
        Args:
            index: LED index (0-count-1)
            r: Red value (0-255)
            g: Green value (0-255)
            b: Blue value (0-255)
        """
        with self._lock:
            # Convert RGB to library's color format
            color = (r << 16) | (g << 8) | b
            self._strip.setPixelColor(index, color)
    
    def set_brightness(self, brightness: int) -> None:
        """
        Set global brightness.
        
        Args:
            brightness: Brightness value (0-255)
        """
        with self._lock:
            self._strip.setBrightness(brightness)
    
    def set_brightness_override(self, brightness: int) -> None:
        """
        Set brightness override (called by LDR).
        Immediately updates the display.
        
        Args:
            brightness: Brightness value (0-255)
        """
        with self._lock:
            self._strip.setBrightness(brightness)
            self._strip.show()
    
    def clear(self) -> None:
        """Turn all LEDs off."""
        with self._lock:
            for i in range(self._strip.numPixels()):
                self._strip.setPixelColor(i, 0)
    
    def cleanup(self) -> None:
        """Clean up resources and turn off LEDs."""
        print("[LightController] Cleaning up LED strip")
        self.clear()
        self.show()
