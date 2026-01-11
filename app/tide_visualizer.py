import threading
import time
from typing import Dict, Any, List, Tuple

from light_controller import LightController
from tide_calculator import TideCalculator


# -----------------------------
# Constants
# -----------------------------

# Color definitions (RGB tuples)
COLOR_GREEN = (0, 255, 0)      # Rising direction
COLOR_RED = (255, 0, 0)        # Falling direction
COLOR_BLUE = (0, 0, 255)       # High tide / Always-blue LED
COLOR_PURPLE = (128, 0, 128)   # Low tide
COLOR_OFF = (0, 0, 0)          # Off state


class TideVisualizer:
    """
    Manages LED visualization of tide state with animation support.
    Runs in background thread with 10 Hz update rate.
    Responds to runtime configuration changes.
    Location-agnostic - works with whatever data is in cache.
    """
    
    def __init__(
        self,
        light_controller: LightController,
        tide_calculator: TideCalculator,
        config: Dict[str, Any]
    ):
        """
        Initialize tide visualizer.
        
        Args:
            light_controller: Controller for LED strip
            tide_calculator: Calculator for tide state
            config: Full configuration dictionary
        """
        self._light = light_controller
        self._calculator = tide_calculator
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        
        # Extract LED configuration
        self._led_count = config["led_strip"]["count"]
        self._invert = config["led_strip"]["invert"]
        
        # Calculate dynamic LED positions
        self._update_led_positions()
        
        # Extract visualization configuration
        self._pattern = config["color"]["pattern"]
        self._wave_speed = config["color"]["wave_speed"]
        
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        
        print(f"[TideVisualizer] Initialized with {self._led_count} LEDs")
        print(f"[TideVisualizer] Pattern: {self._pattern}, Speed: {self._wave_speed}s")
    
    # -----------------------------
    # Public API
    # -----------------------------
    
    def start(self) -> None:
        """Start visualization thread."""
        self._thread.start()
        print("[TideVisualizer] Started")
    
    def stop(self) -> None:
        """Stop visualization thread and wait for cleanup."""
        print("[TideVisualizer] Stopping...")
        self._stop_event.set()
        self._thread.join()
        print("[TideVisualizer] Stopped")
    
    def on_config_updated(self, new_config: Dict[str, Any]) -> None:
        """
        Handle runtime configuration changes.
        Updates LED count, invert, brightness, and pattern without restart.
        
        Args:
            new_config: New configuration dictionary
        """
        with self._lock:
            # Update LED configuration
            self._led_count = new_config["led_strip"]["count"]
            self._invert = new_config["led_strip"]["invert"]
            self._update_led_positions()
            
            # Update brightness
            new_brightness = new_config["led_strip"]["brightness"]
            self._light.set_brightness(new_brightness)
            
            # Update pattern settings
            self._pattern = new_config["color"]["pattern"]
            self._wave_speed = new_config["color"]["wave_speed"]
        
        print(f"[TideVisualizer] Config updated: pattern={self._pattern}, brightness={new_brightness}")
    
    def on_tide_data_updated(self) -> None:
        """
        Called by TideUpdateScheduler when new tide data is fetched.
        Visualizer can reset animation or preload state.
        """
        print("[TideVisualizer] Tide data updated, refreshing visualization")
        # Main loop will automatically pick up new data on next iteration
    
    # -----------------------------
    # Internal methods
    # -----------------------------
    
    def _update_led_positions(self) -> None:
        """Calculate LED positions based on count and invert flag."""
        if self._invert:
            """TODO: investigate this a bit closer. Strip may have built in invert"""
            # LED 0 is bottom, LED (count-1) is top
            self._top_led = self._led_count - 1
            self._bottom_led = 0
            self._middle_start = 1
            self._middle_end = self._led_count - 2
        else:
            # LED 0 is top, LED (count-1) is bottom
            self._top_led = 0
            self._bottom_led = self._led_count - 1
            self._middle_start = 1
            self._middle_end = self._led_count - 2
        
        self._num_middle_leds = self._middle_end - self._middle_start + 1
        self._always_blue_led_index = self._num_middle_leds - 1  # Last middle LED in array
    
    def _run_loop(self) -> None:
        """
        Main visualization loop.
        Updates at 10 Hz for smooth animation.
        """
        wave_position = 0
        last_wave_update = time.time()
        error_blink_state = False
        last_error_blink = time.time()
        last_direction = None  # Track direction changes
        
        while not self._stop_event.is_set():
            # Get current config values (thread-safe)
            with self._lock:
                pattern = self._pattern
                wave_speed = self._wave_speed
                num_middle = self._num_middle_leds
            
            # Get current tide state (no parameters - uses cache)
            tide_state = self._calculator.get_current_state()
            
            if tide_state is None:
                # ERROR STATE: No tide data available
                now = time.time()
                if now - last_error_blink >= 0.5:
                    error_blink_state = not error_blink_state
                    last_error_blink = now
                self._show_error_state(error_blink_state)
                time.sleep(0.1)
                continue
            
            # Detect direction change
            if last_direction is not None and last_direction != tide_state.direction:
                print(f"[TideVisualizer] Tide direction changed: {last_direction} → {tide_state.direction}")
            last_direction = tide_state.direction
            
            # Set direction indicators
            self._set_direction_indicators(tide_state.direction)
            
            # Calculate base middle colors
            middle_colors = self._calculate_middle_colors(tide_state.progress, num_middle)
            
            # Apply wave animation if enabled
            if pattern == "wave":
                now = time.time()
                if now - last_wave_update >= wave_speed:
                    wave_position = (wave_position + 1) % (num_middle - 1)  # Exclude always-blue LED
                    last_wave_update = now
                
                middle_colors = self._apply_wave_effect(
                    middle_colors,
                    wave_position,
                    tide_state.direction,
                    num_middle
                )
            
            # Set all middle LEDs
            self._set_middle_leds(middle_colors)
            
            # Update strip
            self._light.show()
            
            # Sleep for 10 Hz update rate
            time.sleep(0.1)
    
    def _set_direction_indicators(self, direction: str) -> None:
        """Set top and bottom direction LEDs based on tide direction."""
        if direction == "rising":
            self._light.set_pixel(self._top_led, *COLOR_GREEN)
            self._light.set_pixel(self._bottom_led, *COLOR_OFF)
        else:  # falling
            self._light.set_pixel(self._top_led, *COLOR_OFF)
            self._light.set_pixel(self._bottom_led, *COLOR_RED)
    
    def _calculate_middle_colors(
        self, 
        progress: float, 
        num_middle: int
    ) -> List[Tuple[int, int, int]]:
        """
        Calculate colors for middle LEDs based on tide progress.
        
        Args:
            progress: 0.0 (low) to 1.0 (high)
            num_middle: Number of middle LEDs
            
        Returns:
            List of RGB tuples for middle LEDs
        """
        colors = [COLOR_OFF] * num_middle
        
        # Last middle LED (index num_middle-1) always BLUE
        colors[self._always_blue_led_index] = COLOR_BLUE
        
        # Calculate how many LEDs should be BLUE (excluding always-blue LED)
        num_blue = int(progress * (num_middle - 1))
        
        # Fill from bottom up (last middle LED is reference point)
        # Array index 0 is closest to top, index (num_middle-1) is closest to bottom
        for i in range(num_blue):
            colors[num_middle - 2 - i] = COLOR_BLUE
        
        # Rest are PURPLE
        for i in range(num_blue, num_middle - 1):
            colors[num_middle - 2 - i] = COLOR_PURPLE
        
        return colors
    
    def _set_middle_leds(self, colors: List[Tuple[int, int, int]]) -> None:
        """Set middle LED colors, respecting invert flag."""
        for i, (r, g, b) in enumerate(colors):
            physical_index = self._middle_start + i
            self._light.set_pixel(physical_index, r, g, b)
    
    def _apply_wave_effect(
        self, 
        base_colors: List[Tuple[int, int, int]],
        wave_position: int,
        direction: str,
        num_middle: int
    ) -> List[Tuple[int, int, int]]:
        """
        Apply 3-LED cascading wave effect with color rotation.
        
        The wave consists of 3 LEDs that move together, but the colors
        rotate through the LEDs creating a "climbing" effect:
        Frame 1: 123 → Frame 2: 231 → Frame 3: 312 → Frame 4: 123
        
        Args:
            base_colors: Base colors for middle LEDs
            wave_position: Current wave position (also determines phase)
            direction: "rising" or "falling"
            num_middle: Number of middle LEDs
            
        Returns:
            Colors with wave effect applied
        """
        result = list(base_colors)  # Copy to avoid mutation
        
        # Calculate wave phase for color rotation (0, 1, 2)
        wave_phase = wave_position % 3
        
        # Wave consists of 3 LEDs with rotating color shifts
        # offset 0 = leading edge, offsets 1,2 = trailing
        wave_offsets = [0, 1, 2]
        
        for offset in wave_offsets:
            if direction == "rising":
                # Wave moves UP (toward top, LOWER indices)
                # Start from bottom (high indices) and move toward top (low indices)
                pos = (num_middle - 2 - wave_position) - offset
            else:  # falling
                # Wave moves DOWN (toward bottom, HIGHER indices)
                # Start from top (low indices) and move toward bottom (high indices)
                pos = wave_position + offset
            
            # Include all middle LEDs (including always-blue LED)
            if 0 <= pos < num_middle:
                # Calculate shift level with rotation
                # Each position cycles through levels 0→1→2 as wave passes
                shift_level = (wave_phase + offset) % 3
                result[pos] = self._shift_color(result[pos], shift_level)
        
        return result
    
    def _shift_color(
        self, 
        color: Tuple[int, int, int], 
        shift_level: int
    ) -> Tuple[int, int, int]:
        """
        Shift color for cascading wave effect.
        
        Creates 3 distinct color levels for the wave animation:
        - Blue (0, 0, 255) → 3 levels of cyan
        - Purple (128, 0, 128) → 3 levels of pink/magenta
        
        Args:
            color: Base RGB color
            shift_level: Shift intensity level (0=subtle, 1=medium, 2=strong)
            
        Returns:
            Shifted RGB color
        """
        r, g, b = color
        
        # Shift toward cyan/magenta depending on base color
        if b > r and b > g:  # Blue-ish → Cyan
            # 3 distinct levels of cyan (add green component)
            # Level 0: slight (30% green), Level 1: medium (50%), Level 2: strong (70%)
            green_shifts = [100, 150, 200]
            g = min(255, green_shifts[shift_level])
            
        elif r > b and g < r:  # Red-ish or Purple-ish → Pink/Magenta
            # 3 distinct levels of pink/magenta (boost red and blue)
            # Level 0: +20, Level 1: +40, Level 2: +60
            brightness_boosts = [20, 40, 60]
            boost = brightness_boosts[shift_level]
            r = min(255, r + boost)
            b = min(255, b + boost)
            
        else:
            # For other colors, add some saturation
            # (This shouldn't normally be reached in tide visualization)
            saturation_boosts = [1.2, 1.4, 1.6]
            boost = saturation_boosts[shift_level]
            r = min(255, int(r * boost))
            g = min(255, int(g * boost))
            b = min(255, int(b * boost))
        
        return (r, g, b)
    
    def _show_error_state(self, blink_on: bool) -> None:
        """
        Display error pattern (all red blinking).
        
        Args:
            blink_on: True to show red, False to show off
        """
        if blink_on:
            for i in range(self._led_count):
                self._light.set_pixel(i, *COLOR_RED)
        else:
            self._light.clear()
        
        self._light.show()
