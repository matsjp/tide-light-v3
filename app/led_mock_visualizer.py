"""
LED Mock Visualizer - Wrapper for rpi_ws281x mock that prints LED state to console.

This module wraps the mock PixelStrip and prints a visual representation of the LED
strip state every time it changes. Useful for debugging and development without hardware.

Character Mapping:
  * = Off (0,0,0)
  G = Green (0,255,0) - Rising tide indicator
  R = Red (255,0,0) - Falling tide indicator
  B = Blue (0,0,255) - High tide (no wave)
  c = Subtle cyan - Wave level 0
  C = Medium cyan - Wave level 1
  Y = Strong cyan - Wave level 2
  P = Purple (128,0,128) - Low tide (no wave)
  m = Subtle magenta - Wave level 0
  M = Medium magenta - Wave level 1
  K = Strong magenta - Wave level 2
  ? = Unknown color
  
Wave Animation: The 3-LED cascading wave shows as "cCY" (on blue) or "mMK" (on purple),
with colors rotating through positions as the wave moves.
"""

from typing import Optional
from rpi_ws281x import PixelStrip


class PixelStripVisualizer:
    """
    Wrapper around rpi_ws281x mock PixelStrip that visualizes LED state in console.
    Implements the same interface as PixelStrip for drop-in compatibility.
    """
    
    def __init__(
        self,
        num,
        pin,
        freq_hz=800000,
        dma=10,
        invert=False,
        brightness=255,
        channel=0,
        strip_type=None,
        gamma=None,
    ):
        """
        Initialize visualizer with a wrapped mock PixelStrip.
        
        Args:
            Same as rpi_ws281x.PixelStrip
        """
        # Create the underlying mock strip
        self._strip = PixelStrip(
            num=num,
            pin=pin,
            freq_hz=freq_hz,
            dma=dma,
            invert=invert,
            brightness=brightness,
            channel=channel,
            strip_type=strip_type,
            gamma=gamma
        )
        
        # Track previous state for change detection
        self._previous_state: Optional[str] = None
        self._show_count = 0
    
    # -----------------------------
    # PixelStrip Interface (delegate to mock)
    # -----------------------------
    
    def begin(self):
        """Initialize library, must be called once before other functions."""
        self._strip.begin()
        print("[LED MOCK] Visualizer initialized")
    
    def show(self):
        """Update the display and print visualization if state changed."""
        self._strip.show()
        self._show_count += 1
        
        # Get current LED state
        current_state = self._get_led_visualization()
        
        # Only print if state changed
        if current_state != self._previous_state:
            print(f"[LED] {current_state}")
            self._previous_state = current_state
    
    def setPixelColor(self, n, color):
        """Set LED at position n to the provided 24-bit color value."""
        self._strip.setPixelColor(n, color)
    
    def setPixelColorRGB(self, n, red, green, blue, white=0):
        """Set LED at position n to the provided red, green, and blue color."""
        self._strip.setPixelColorRGB(n, red, green, blue, white)
    
    def getBrightness(self):
        """Get the current brightness level."""
        return self._strip.getBrightness()
    
    def setBrightness(self, brightness):
        """Set the brightness level."""
        self._strip.setBrightness(brightness)
    
    def getPixels(self):
        """Return an object which allows access to the LED display data."""
        return self._strip.getPixels()
    
    def numPixels(self):
        """Return the number of pixels in the display."""
        return self._strip.numPixels()
    
    def getPixelColor(self, n):
        """Get the 24-bit RGB color value for the LED at position n."""
        return self._strip.getPixelColor(n)
    
    def getPixelColorRGB(self, n):
        """Get the RGB color for the LED at position n."""
        return self._strip.getPixelColorRGB(n)
    
    # -----------------------------
    # Visualization
    # -----------------------------
    
    def _get_led_visualization(self) -> str:
        """
        Generate a string visualization of current LED state.
        
        Returns:
            String representation of LED strip (e.g., "G**PPPPBBBBBBB*")
        """
        chars = []
        
        for i in range(self._strip.numPixels()):
            color = self._strip.getPixelColor(i)
            char = self._color_to_char(color)
            chars.append(char)
        
        return ''.join(chars)
    
    def _color_to_char(self, color: int) -> str:
        """
        Convert a 24-bit color value to a single character representation.
        
        Args:
            color: 24-bit RGB color value (format: 0xRRGGBB)
            
        Returns:
            Single character representing the color:
            - '*' = Off (black)
            - 'G' = Green (rising tide indicator)
            - 'R' = Red (falling tide indicator)
            - 'B' = Blue (high tide / reference LED)
            - 'C' = Cyan (wave effect on blue, strong)
            - 'c' = Cyan (wave effect on blue, subtle)
            - 'P' = Purple (low tide)
            - 'M' = Magenta (wave effect on purple, strong)
            - 'm' = Magenta (wave effect on purple, subtle)
            - '?' = Unknown/other color
        """
        # Extract RGB components
        r = (color >> 16) & 0xFF
        g = (color >> 8) & 0xFF
        b = color & 0xFF
        
        # Off (all components low)
        if r < 30 and g < 30 and b < 30:
            return '*'
        
        # Green (rising tide indicator)
        # Looking for (0, 255, 0) or close to it
        if g > 200 and r < 100 and b < 100:
            return 'G'
        
        # Red (falling tide indicator)
        # Looking for (255, 0, 0) or close to it
        if r > 200 and g < 100 and b < 100:
            return 'R'
        
        # --- Cyan wave levels (blue + green) ---
        # Strong cyan: green ~200
        # Looking for (0, 200, 255)
        if b > 200 and g >= 180 and r < 50:
            return 'Y'  # Level 2 (strongest cyan)
        
        # Medium cyan: green ~150
        # Looking for (0, 150, 255)
        if b > 200 and 130 <= g < 180 and r < 50:
            return 'C'  # Level 1 (medium cyan)
        
        # Subtle cyan: green ~100
        # Looking for (0, 100, 255)
        if b > 200 and 80 <= g < 130 and r < 50:
            return 'c'  # Level 0 (subtle cyan)
        
        # Blue (high tide / no wave)
        # Looking for (0, 0, 255) or close to it
        if b > 200 and g < 80 and r < 50:
            return 'B'
        
        # --- Magenta/Pink wave levels (purple + saturation boost) ---
        # Using saturation boosts [1.2, 1.4, 1.6] on (128, 0, 128)
        # Strong magenta: int(128*1.6) = 204
        if r >= 190 and b >= 190 and g < 50:
            return 'K'  # Level 2 (strongest magenta/pink)
        
        # Medium magenta: int(128*1.4) = 179
        if r >= 165 and r < 190 and b >= 165 and b < 190 and g < 50:
            return 'M'  # Level 1 (medium magenta)
        
        # Subtle magenta: int(128*1.2) = 153
        if r >= 140 and r < 165 and b >= 140 and b < 165 and g < 50:
            return 'm'  # Level 0 (subtle magenta)
        
        # Purple (low tide / no wave)
        # Looking for (128, 0, 128) or close to it
        if r >= 100 and r < 130 and b >= 100 and b < 130 and g < 50:
            return 'P'
        
        # Unknown color
        return '?'


# Export the visualizer as PixelStrip for drop-in compatibility
__all__ = ['PixelStripVisualizer']
