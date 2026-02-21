import time
import logging
from config_manager import ConfigManager
from tide_cache_manager import TideCacheManager
from tide_fetcher import TideFetcher
from tide_update_scheduler import TideUpdateScheduler
from light_controller import LightController
from tide_calculator import TideCalculator
from tide_visualizer import TideVisualizer
from ble import BLEManager
from ldr_controller import LdrController
from rtc_manager import RTCManager

CONFIG_PATH = "config.json"
DB_PATH = "tide_cache.sqlite"

def on_config_changed(config, scheduler, visualizer, ldr):
    lat = config["tide"]["location"]["latitude"]
    lon = config["tide"]["location"]["longitude"]
    brightness = config["led_strip"]["brightness"]
    invert = config["led_strip"]["invert"]
    pattern = config["color"]["pattern"]

    print("Configuration updated:")
    print(f"  Tide location: ({lat}, {lon})")
    print(f"  LED brightness: {brightness}")
    print(f"  LED invert: {invert}")
    print(f"  LED pattern: {pattern}")

    scheduler.on_config_updated(config)
    visualizer.on_config_updated(config)
    ldr.on_config_updated(config)

def main():
    # Configure logging
    # Option 1: Debug for BLE only, Info for everything else
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Enable DEBUG for BLE-related modules only
    logging.getLogger('ble').setLevel(logging.DEBUG)
    logging.getLogger('app.ble').setLevel(logging.DEBUG)
    
    # Option 2: To enable DEBUG for ALL modules, uncomment this line instead:
    logging.getLogger().setLevel(logging.DEBUG)
    
    print("Starting Tide Light...")

    config_manager = ConfigManager(CONFIG_PATH)
    config = config_manager.get_config()

    cache = TideCacheManager(DB_PATH)  # Thread-safe SQLite
    fetcher = TideFetcher()

    # Check if location changed while offline (Case 4)
    config_lat = config["tide"]["location"]["latitude"]
    config_lon = config["tide"]["location"]["longitude"]
    cached_location = cache.get_cached_location()
    
    if cached_location is not None:
        cached_lat, cached_lon = cached_location
        if cached_lat != config_lat or cached_lon != config_lon:
            print("[Startup] Location changed while offline:")
            print(f"  Cached location: ({cached_lat}, {cached_lon})")
            print(f"  Config location: ({config_lat}, {config_lon})")
            print("[Startup] Clearing old tide data...")
            cache.invalidate_all()
    else:
        print("[Startup] No cached location found (first run or cache cleared)")

    scheduler = TideUpdateScheduler(
        cache_manager=cache,
        tide_fetcher=fetcher,
        config=config,
        prefetch_days=7,
        interval_days=7
    )
    scheduler.start()

    # Initialize LED light system
    print("Initializing LED strip...")
    light = LightController(config)
    light.begin()
    
    print("Initializing tide calculator...")
    calculator = TideCalculator(cache)
    
    print("Starting tide visualizer...")
    visualizer = TideVisualizer(
        light_controller=light,
        tide_calculator=calculator,
        config=config
    )
    
    # Connect scheduler and visualizer
    scheduler.set_visualizer(visualizer)
    
    # Start visualizer
    visualizer.start()
    
    # Initialize LDR controller
    print("Initializing LDR controller...")
    def on_ldr_brightness_change(brightness: int):
        """Callback when LDR wants to change brightness."""
        print(f"[LDR] Auto-adjusting brightness to {brightness}")
        visualizer.set_brightness(brightness)
    
    ldr = LdrController(config=config, on_brightness_change=on_ldr_brightness_change)
    ldr.start()
    
    # Register config listener
    config_manager.register_listener(lambda cfg: on_config_changed(cfg, scheduler, visualizer, ldr))

    # Initial fetch (will notify visualizer)
    scheduler._run_once()

    # Initialize RTC manager
    print("Initializing RTC manager...")
    rtc_manager = RTCManager()

    # Initialize BLE interface
    print("Initializing BLE interface...")
    ble_manager = BLEManager(
        config_manager=config_manager,
        tide_calculator=calculator,
        tide_cache=cache,
        config_path=CONFIG_PATH,
        rtc_manager=rtc_manager
    )
    ble_manager.start()

    print("System initialized. Running main loop.")
    print(f"  Current tide location: ({scheduler.current_lat}, {scheduler.current_lon})")
    print(f"  LED pattern: {config['color']['pattern']}")
    print(f"  LED brightness: {config['led_strip']['brightness']}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down Tide Light...")
        ldr.stop()
        ble_manager.stop()
        visualizer.stop()
        scheduler.stop()
        light.cleanup()

if __name__ == "__main__":
    main()
