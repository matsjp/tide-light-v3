"""
GPIO Manager - Handles GPIO initialization and mocking.

This module provides GPIO functionality for features like:
- LDR (Light Dependent Resistor) brightness sensing
- Future GPIO-based sensors or controls

Note: WS281x LED strips do NOT need this module - they handle
GPIO internally via PWM/DMA through the rpi_ws281x library.
"""

import sys
from typing import Optional


class GPIOManager:
    """
    Manages GPIO initialization with automatic mock/real detection.
    """
    
    def __init__(self, use_mock: bool = False):
        """
        Initialize GPIO manager.
        
        Args:
            use_mock: Force mock mode (for development on non-Pi platforms)
        """
        self.use_mock = use_mock or sys.platform != 'linux'
        self.gpio: Optional[any] = None
        self._initialized = False
        
    def initialize(self, mode: str = "BOARD") -> None:
        """
        Initialize GPIO with specified pin numbering mode.
        
        Args:
            mode: Pin numbering mode - "BOARD" (physical pins) or "BCM" (GPIO numbers)
        """
        if self._initialized:
            print("[GPIO] Already initialized")
            return
            
        if self.use_mock:
            print("[GPIO] Using MOCK GPIO for development")
            self.gpio = self._get_mock_gpio()
        else:
            print("[GPIO] Using REAL GPIO for Raspberry Pi")
            try:
                import RPi.GPIO as GPIO
                self.gpio = GPIO
            except ImportError:
                raise ImportError(
                    "RPi.GPIO not found. Install with: pip install RPi.GPIO"
                )
        
        # Set pin numbering mode
        if mode == "BOARD":
            self.gpio.setmode(self.gpio.BOARD)
        elif mode == "BCM":
            self.gpio.setmode(self.gpio.BCM)
        else:
            raise ValueError(f"Invalid GPIO mode: {mode}. Use 'BOARD' or 'BCM'")
        
        # Disable warnings about channels already in use
        self.gpio.setwarnings(False)
        
        self._initialized = True
        print(f"[GPIO] Initialized in {mode} mode")
    
    def cleanup(self) -> None:
        """Clean up GPIO resources."""
        if self._initialized and self.gpio:
            self.gpio.cleanup()
            self._initialized = False
            print("[GPIO] Cleaned up")
    
    def _get_mock_gpio(self):
        """Create a mock GPIO module for development."""
        
        class MockGPIO:
            """Mock implementation of RPi.GPIO for development."""
            
            # Pin numbering modes
            BOARD = 10
            BCM = 11
            
            # Pin modes
            IN = 1
            OUT = 0
            
            # Pull up/down resistors
            PUD_OFF = 20
            PUD_DOWN = 21
            PUD_UP = 22
            
            # Edge detection
            RISING = 31
            FALLING = 32
            BOTH = 33
            
            # PWM
            HIGH = 1
            LOW = 0
            
            @staticmethod
            def setmode(mode):
                """Set pin numbering mode."""
                pass
            
            @staticmethod
            def setwarnings(flag):
                """Enable/disable warnings."""
                pass
            
            @staticmethod
            def setup(channel, mode, pull_up_down=PUD_OFF, initial=LOW):
                """Setup a channel as input or output."""
                print(f"[MockGPIO] setup(channel={channel}, mode={mode})")
            
            @staticmethod
            def output(channel, state):
                """Set output channel state."""
                print(f"[MockGPIO] output(channel={channel}, state={state})")
            
            @staticmethod
            def input(channel):
                """Read input channel state."""
                print(f"[MockGPIO] input(channel={channel}) -> 0")
                return 0
            
            @staticmethod
            def cleanup(channel=None):
                """Clean up GPIO resources."""
                if channel:
                    print(f"[MockGPIO] cleanup(channel={channel})")
                else:
                    print("[MockGPIO] cleanup(all channels)")
            
            class PWM:
                """Mock PWM class."""
                
                def __init__(self, channel, frequency):
                    self.channel = channel
                    self.frequency = frequency
                    print(f"[MockGPIO] PWM created on channel {channel} at {frequency}Hz")
                
                def start(self, duty_cycle):
                    print(f"[MockGPIO] PWM.start(duty_cycle={duty_cycle})")
                
                def ChangeDutyCycle(self, duty_cycle):
                    print(f"[MockGPIO] PWM.ChangeDutyCycle({duty_cycle})")
                
                def ChangeFrequency(self, frequency):
                    print(f"[MockGPIO] PWM.ChangeFrequency({frequency})")
                
                def stop(self):
                    print("[MockGPIO] PWM.stop()")
        
        return MockGPIO


# Global GPIO manager instance
_gpio_manager: Optional[GPIOManager] = None


def get_gpio_manager(use_mock: bool = False) -> GPIOManager:
    """
    Get or create the global GPIO manager instance.
    
    Args:
        use_mock: Force mock mode (only used on first call)
    
    Returns:
        Global GPIOManager instance
    """
    global _gpio_manager
    if _gpio_manager is None:
        _gpio_manager = GPIOManager(use_mock=use_mock)
    return _gpio_manager


def initialize_gpio(mode: str = "BOARD", use_mock: bool = False) -> None:
    """
    Convenience function to initialize GPIO.
    
    Args:
        mode: Pin numbering mode - "BOARD" or "BCM"
        use_mock: Force mock mode for development
    """
    manager = get_gpio_manager(use_mock=use_mock)
    manager.initialize(mode=mode)
