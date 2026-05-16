# Raspberry Pi Setup Guide - Tide Light v3

Complete first-time setup guide for installing Tide Light v3 on a fresh Raspberry Pi.

---

## Table of Contents

1. [Hardware Requirements](#hardware-requirements)
2. [Raspberry Pi OS Installation](#raspberry-pi-os-installation)
3. [Initial System Configuration](#initial-system-configuration)
4. [Hardware Assembly](#hardware-assembly)
5. [Network Configuration](#network-configuration)
6. [Software Installation](#software-installation)
7. [Post-Installation Configuration](#post-installation-configuration)
8. [Verification](#verification)
9. [Creating a Master Image for Replication](#creating-a-master-image-for-replication)
10. [Troubleshooting](#troubleshooting)

---

## Hardware Requirements

### Required Components

- **Raspberry Pi** (any model with GPIO pins)
  - Recommended: Raspberry Pi 3B+, 4, or Zero 2 W
  - Must support: GPIO, I2C, Bluetooth LE
- **MicroSD Card** (16GB minimum, Class 10 recommended)
- **Power Supply** (5V, appropriate amperage for your Pi model)
- **WS281x LED Strip** (addressable RGB LEDs)
  - Supported: WS2811, WS2812, WS2812B
  - External power supply required (5V, sufficient amperage for LED count)
- **DS3231 RTC Module** (optional but recommended)
  - High-precision I2C real-time clock
  - Includes CR2032 battery for backup
- **LDR Photoresistor** (optional)
  - For automatic brightness adjustment
  - Connected via I2C ADC module

### Optional Components

- Case/enclosure for weatherproofing
- Level shifter (3.3V to 5V) for LED data line
- Heat sinks for Raspberry Pi (if running continuously)

---

## Raspberry Pi OS Installation

### Download Raspberry Pi Imager

1. Download **Raspberry Pi Imager** from: https://www.raspberrypi.com/software/
2. Install on your computer (Windows, macOS, or Linux)

### Flash Raspberry Pi OS

1. **Insert microSD card** into your computer
2. **Launch Raspberry Pi Imager**
3. **Choose OS:**
   - Recommended: **Raspberry Pi OS Lite (64-bit)** - Headless, minimal
   - Alternative: **Raspberry Pi OS (64-bit)** - With desktop GUI
4. **Choose Storage:** Select your microSD card
5. **Configure Settings** (click gear icon ⚙️):
   - **Enable SSH** ✅ (CRITICAL for headless setup)
   - **Set username:** `pi` (recommended, or choose your own)
   - **Set password:** Choose a strong password
   - **Configure WiFi** (optional, recommended for wireless setup):
     - SSID: Your WiFi network name
     - Password: Your WiFi password
     - Country: Your country code (e.g., US, GB, NO)
   - **Set locale settings:**
     - Timezone: Your timezone (e.g., Europe/Oslo)
     - Keyboard layout: Your keyboard layout
6. **Write** to microSD card (will erase all data!)
7. **Wait for completion** and safely eject

### First Boot

1. **Insert microSD card** into Raspberry Pi
2. **Connect hardware:**
   - For headless: Only power supply needed (SSH via network)
   - For desktop: Connect monitor, keyboard, mouse, power
3. **Power on** - wait 1-2 minutes for first boot
4. **Connect via SSH** (headless):
   ```bash
   ssh pi@raspberrypi.local
   # Or if .local doesn't work, find IP via router and use:
   ssh pi@192.168.1.XXX
   ```

---

## Initial System Configuration

### Using raspi-config (Recommended)

If you didn't configure settings during imaging, or need to change them:

```bash
sudo raspi-config
```

#### Required Settings

1. **Enable SSH** (if not enabled during imaging)
   - Navigate: `Interface Options` → `SSH` → `Enable`
   - This allows remote access via SSH

2. **Enable I2C** (required for RTC module)
   - Navigate: `Interface Options` → `I2C` → `Enable`
   - This enables I2C bus for DS3231 RTC communication

#### Optional Settings

3. **Set Locale** (if not set during imaging)
   - Navigate: `Localisation Options` → `Locale`
   - Select your locale (e.g., `en_US.UTF-8`)

4. **Set Timezone** (if not set during imaging)
   - Navigate: `Localisation Options` → `Timezone`
   - Select your region and city

5. **Set Keyboard Layout** (if not set during imaging)
   - Navigate: `Localisation Options` → `Keyboard`
   - Select your keyboard layout

6. **Expand Filesystem** (usually auto-done on first boot)
   - Navigate: `Advanced Options` → `Expand Filesystem`
   - Ensures full microSD card space is available

7. **Finish** and **Reboot** when prompted

### System Update

**IMPORTANT:** Always update system packages before installing anything:

```bash
sudo apt-get update
sudo apt-get upgrade -y
```

This may take 5-15 minutes depending on how outdated the image is.

### Install Git

```bash
sudo apt-get install -y git
```

---

## Hardware Assembly

### DS3231 RTC Module Wiring

Connect the DS3231 RTC module to the Raspberry Pi I2C pins:

```
DS3231          Raspberry Pi GPIO
------          -----------------
VCC       →     Pin 1  (3.3V)
GND       →     Pin 6  (Ground)
SDA       →     Pin 3  (GPIO 2 / I2C SDA)
SCL       →     Pin 5  (GPIO 3 / I2C SCL)
```

**Important Notes:**
- Use **3.3V**, NOT 5V (will damage the Pi)
- SDA/SCL are pulled up internally, no external resistors needed
- Ensure CR2032 battery is installed in RTC module

**Verification after installation:**
```bash
# After running installation scripts and rebooting:
sudo i2cdetect -y 1
```

You should see `68` or `UU` at address 0x68:
- `68` = RTC detected but no driver loaded
- `UU` = RTC detected and driver using it (correct state after setup)

### WS281x LED Strip Wiring

Connect the LED strip to the Raspberry Pi:

```
LED Strip       Raspberry Pi GPIO
---------       -----------------
GND       →     Pin 6  (Ground) - Shared with LED power supply ground
DIN/Data  →     Pin 12 (GPIO 18 / PWM0) - Hardcoded in LightController
+5V       →     External 5V Power Supply (NOT Raspberry Pi!)
```

**CRITICAL Safety Notes:**
- **NEVER power LED strip from Raspberry Pi 5V pins** - will overdraw and damage Pi
- **Always use external 5V power supply** rated for LED count:
  - Each LED draws ~60mA at full white brightness
  - Example: 30 LEDs × 60mA = 1.8A minimum power supply
  - Recommended: 20-30% overhead (e.g., 3A supply for 30 LEDs)
- **Connect grounds together:** Raspberry Pi ground MUST be connected to LED power supply ground
- **Use appropriate wire gauge** for power (18-22 AWG for short runs)
- **Optional but recommended:** 3.3V-to-5V level shifter on data line for reliability

### LDR Photoresistor (Optional)

**Note:** The application will work without LDR hardware. If no LDR is detected, brightness control remains manual.

Connect via I2C ADC module (e.g., ADS1115 or similar):

```
ADC Module      Raspberry Pi GPIO
----------      -----------------
VCC       →     Pin 1  (3.3V)
GND       →     Pin 6  (Ground)
SDA       →     Pin 3  (GPIO 2 / I2C SDA)
SCL       →     Pin 5  (GPIO 3 / I2C SCL)

LDR       →     ADC Analog Input (e.g., A0)
```

Configuration via BLE or `config.json` after installation.

---

## Network Configuration

### WiFi Configuration

#### Option 1: Via Raspberry Pi Imager (Recommended)
Already configured during imaging - skip to verification.

#### Option 2: Via raspi-config (If not set during imaging)
```bash
sudo raspi-config
# Navigate: System Options → Wireless LAN
# Enter SSID and password
```

#### Option 3: Manual wpa_supplicant.conf (Headless, no imaging config)

If you need to add WiFi after flashing without Imager configuration:

1. **Mount boot partition** on your computer (before first boot)
2. **Create file:** `wpa_supplicant.conf` in boot partition root
3. **Add configuration:**

```
country=NO
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

network={
    ssid="YourNetworkName"
    psk="YourNetworkPassword"
    key_mgmt=WPA-PSK
}
```

Replace `country`, `ssid`, and `psk` with your values.

4. **Save and eject** - WiFi will configure on first boot

#### Verification

Check WiFi connection:
```bash
ip a
# Look for wlan0 interface with IP address

ping -c 3 google.com
# Should get responses if internet connected
```

### Ethernet Configuration

Plug in Ethernet cable - should work automatically via DHCP.

Verify:
```bash
ip a
# Look for eth0 interface with IP address
```

---

## Software Installation

### Clone Repository

```bash
cd /home/pi
git clone https://github.com/matsjp/tide-light-v3.git
cd tide-light-v3
```

### Run Master Installation Script

The installation is fully automated via a master script:

```bash
cd /home/pi/tide-light-v3/app/scripts
sudo ./install_complete.sh
```

**What this does:**

1. **Step 1 - Install System Dependencies:**
   - Installs required apt packages (python3, pip, git, etc.)
   - Enables `systemd-networkd-wait-online.service` (for auto-updater)

2. **Step 2 - Configure Bluetooth HCI:**
   - Disables `bluetoothd` daemon (conflicts with pybleno)
   - Creates `bluetooth-hci0-up.service` (brings up HCI0 for BLE peripheral mode)

3. **Step 3 - Setup RTC (Optional):**
   - Prompts whether to install RTC hardware support
   - If yes:
     - Enables I2C in `/boot/config.txt` or `/boot/firmware/config.txt`
     - Configures DS3231 kernel module (`dtoverlay=i2c-rtc,ds3231`)
     - Disables `fake-hwclock` (conflicts with real RTC)
     - Installs `i2c-tools` package
     - Creates `tide-light-rtc-sync.service` (syncs time from RTC on boot)
     - Creates helper script: `/usr/local/bin/tide-rtc`

4. **Step 4 - Install Application:**
   - Installs Python packages from `requirements.txt` (system-wide via `sudo pip3`)
   - Creates `tide-light.service` (runs main application as root)
   - Creates `tide-light-updater.service` (auto-updates from GitHub)
   - Creates `tide-light-updater.timer` (triggers updater 2 minutes after boot)
   - Enables all services

5. **Prompts for reboot**

### Reboot

After installation completes:

```bash
sudo reboot
```

---

## Post-Installation Configuration

### Automatic Processes After Reboot

1. **RTC sync** (if RTC installed): `tide-light-rtc-sync.service` runs immediately
2. **HCI0 up**: `bluetooth-hci0-up.service` runs immediately
3. **Auto-updater** (if internet connected): `tide-light-updater.timer` triggers after 2 minutes
4. **Main application**: `tide-light.service` starts (or restarts after updater)

### Initial Configuration

The application starts with default configuration from `ConfigManager.DEFAULT_CONFIG`. You **must** configure your location before the tide visualization will work correctly.

#### Option 1: Configure via BLE (Recommended)

1. **Pair via BLE:**
   - Use Web Bluetooth interface (Chrome/Edge on desktop/mobile)
   - Or native BLE app on phone/tablet
   - Service Name: **"Tide Light"**
   - Service UUID: `ec00` (custom tide light service)

2. **Set location:**
   - Latitude: Your location's latitude (decimal degrees)
   - Longitude: Your location's longitude (decimal degrees)
   - Example: Oslo, Norway = 59.9139° N, 10.7522° E

3. **Optional settings:**
   - Brightness: 0-100%
   - LED pattern: "none" (solid) or "wave" (animated)
   - Wave speed: 0.1-2.0 seconds per step
   - LED count: Number of LEDs in your strip
   - Invert: Flip LED orientation if strip mounted upside-down

#### Option 2: Configure via Web Interface

**Note:** Web interface requires the Raspberry Pi to be accessible on your network.

1. **Find Pi IP address:**
   ```bash
   hostname -I
   ```

2. **Open browser** to: `http://<pi-ip-address>:3000` (or configured port)

3. **Configure settings** via web UI

#### Option 3: Edit config.json Directly

**Advanced users only:**

```bash
sudo nano /home/pi/tide-light-v3/app/config.json
```

Edit location coordinates, save, and restart service:

```bash
sudo systemctl restart tide-light
```

### Set Correct Time (If Using RTC)

After installation, the RTC module has factory default time. You must set it once:

#### Option 1: Via BLE/Web Interface (Easiest)

Use the web interface "Sync Device to Browser Time" button - automatically sets both system time and RTC time.

#### Option 2: Via Command Line

If connected to internet, system time auto-syncs via NTP. Then write to RTC:

```bash
# Verify system time is correct
date

# Write system time to RTC
sudo hwclock --systohc

# Verify RTC time
sudo hwclock --show
```

#### RTC Helper Commands

The installation creates a helper script for RTC management:

```bash
# Check RTC status
tide-rtc status

# Sync system time FROM RTC (on boot or manually)
tide-rtc sync-from-rtc

# Sync system time TO RTC (after setting time online)
tide-rtc sync-to-rtc

# View RTC sync service logs
tide-rtc logs
```

---

## Verification

### Check Service Status

```bash
# Main application
sudo systemctl status tide-light

# Auto-updater
sudo systemctl status tide-light-updater

# RTC sync (if installed)
sudo systemctl status tide-light-rtc-sync

# Bluetooth HCI
sudo systemctl status bluetooth-hci0-up
```

All should show **`active`** or **`inactive (dead)`** after successful one-shot run.

### Check Logs

```bash
# Main application logs
sudo journalctl -u tide-light -f

# Auto-updater logs
sudo journalctl -u tide-light-updater -f

# RTC sync logs
tide-rtc logs
```

### Check LED Strip

If configured correctly:
- LEDs should light up with tide visualization
- If no tide data yet: LEDs blink RED (error state) until first data fetch

### Check BLE Advertising

```bash
# Check if HCI0 is up
hciconfig hci0

# Should show: UP RUNNING
```

From phone/computer:
- Scan for BLE devices
- Should see **"Tide Light"** advertising

### Check RTC (If Installed)

```bash
tide-rtc status
```

Should show:
- RTC device at `/dev/rtc0` or `/dev/rtc`
- RTC time and system time matching (or close)
- I2C device at address `0x68` showing `UU`

---

## Creating a Master Image for Replication

Once you have successfully set up one Raspberry Pi with Tide Light v3, you can create a master image to deploy on multiple Pis without repeating the entire setup process.

### Use Case

This is ideal for:
- Deploying Tide Light to multiple locations
- Backup and disaster recovery
- Distributing pre-configured images to users
- Reducing setup time (install once, replicate many times)

### Prerequisites

- Completed setup on one Raspberry Pi (all steps above)
- Tested and verified working installation
- Windows PC with WSL (Windows Subsystem for Linux) installed
- SD card reader for imaging
- Sufficient disk space (at least 2x the SD card size)

### Step 1: Prepare the Master Pi

Before creating the image, clean up the Pi to remove any device-specific data:

#### Remove Device-Specific Configuration

```bash
# SSH into your master Pi
ssh pi@raspberrypi.local

# Stop services
sudo systemctl stop tide-light tide-light-updater.timer

# Clear tide data cache (will be fetched fresh on first boot)
sudo rm -f /home/pi/tide-light-v3/app/tide_cache.sqlite

# Reset configuration to defaults (optional - only if you want clean config)
# sudo /home/pi/tide-light-v3/app/scripts/factory_reset.sh

# Clear bash history (optional - privacy)
history -c && history -w

# Clear logs (optional - reduces image size)
sudo journalctl --rotate
sudo journalctl --vacuum-time=1s

# Shutdown
sudo shutdown -h now
```

**Important:** Do NOT run `factory_reset.sh` if you want to keep your configuration (location, brightness, etc.). Only use it if you want each Pi to start with default settings.

### Step 2: Create SD Card Image on Windows

Remove the SD card from the Pi and insert it into your Windows PC's card reader.

Use **Win32 Disk Imager** to create the image:

1. Download [Win32 Disk Imager](https://sourceforge.net/projects/win32diskimager/)
2. Launch Win32 Disk Imager as Administrator
3. Select your SD card device from the dropdown
4. Choose output location and filename: `C:\Users\YourName\Documents\tide-light-master.img`
5. Click "Read" to create the image
6. Wait for completion (10-30 minutes depending on SD card size)

**Result:** Full-size image file (e.g., 32GB .img file)

### Step 3: Shrink the Image with PiShrink (in WSL)

PiShrink automatically shrinks the image to the minimum size needed and configures it to auto-expand on first boot.

#### Install WSL (if not already installed)

1. Open PowerShell as Administrator
2. Run: `wsl --install -d Debian`
3. Reboot when prompted
4. Open the "Debian" app from Start menu
5. Follow Microsoft's WSL setup guide for initial configuration

**Note:** WSL installation is a one-time setup. Once installed, you can use it for all future image shrinking operations.

#### Install PiShrink in WSL

Open your WSL terminal (Debian) and run:

```bash
# Install required dependencies
sudo apt update && sudo apt install -y wget parted gzip pigz xz-utils udev e2fsprogs

# Download PiShrink script
wget https://raw.githubusercontent.com/Drewsif/PiShrink/master/pishrink.sh

# Make it executable
chmod +x pishrink.sh

# Move to system path for easy access
sudo mv pishrink.sh /usr/local/bin/pishrink
```

**One-time setup complete!** You can now use `pishrink` command in WSL.

# Clone PiShrink repo
git clone https://github.com/Drewsif/PiShrink && cd PiShrink

# Build Docker image
docker build -t pishrink .

# Create alias (for bash)
echo "alias pishrink='docker run -it --rm --platform linux/amd64 --privileged=true -v \$(pwd):/workdir pishrink'" >> ~/.bashrc && source ~/.bashrc

# Or for zsh (Apple Silicon)
echo "alias pishrink='docker run -it --rm --platform linux/arm64 --privileged=true -v \$(pwd):/workdir pishrink'" >> ~/.zshrc && source ~/.zshrc
```

#### Shrink the Image

In your WSL terminal, navigate to the Windows folder where your image is stored:

```bash
# Windows C:\ drive is mounted at /mnt/c/ in WSL
# Navigate to your image location
cd /mnt/c/Users/YourName/Documents

# Verify the image file exists
ls -lh tide-light-master.img
# Should show file size (e.g., 32GB)

# Shrink and compress with gzip (recommended)
sudo pishrink -z tide-light-master.img
# This will:
# 1. Shrink the partition and filesystem
# 2. Add auto-expansion script for first boot
# 3. Compress with gzip
# Output: tide-light-master.img.gz

# Process takes 5-15 minutes depending on image size and compression
```

**Alternative Compression Options:**

```bash
# Best compression (slower, smallest file)
sudo pishrink -Z tide-light-master.img
# Output: tide-light-master.img.xz (e.g., 900MB)

# Parallel compression (faster on multi-core CPUs)
sudo pishrink -az tide-light-master.img
# Output: tide-light-master.img.gz (compressed using multiple cores)

# No compression (shrink only)
sudo pishrink tide-light-master.img
# Modifies image in-place
```

**Compression Options:**
- `-z` - Compress with gzip (fast, good compression) - **Recommended**
- `-Z` - Compress with xz (slow, best compression)
- `-a` - Use parallel compression (faster on multi-core systems)
- `-v` - Verbose output (shows detailed progress)

**Example Size Reduction:**
- Original: 32GB (full SD card size)
- After shrink: 3.5GB (actual used space)
- After gzip: 1.2GB (70% smaller)
- After xz: 900MB (80% smaller)

**What PiShrink Does:**
1. ✅ Shrinks partition to minimum size needed
2. ✅ Shrinks ext4 filesystem to match partition
3. ✅ Adds boot script for automatic expansion on first boot
4. ✅ Compresses the image (if `-z` or `-Z` used)

**How Auto-Expansion Works:**
- PiShrink modifies the boot process to run an expansion script on first boot
- Script runs early during boot (before services start)
- Expands partition to fill entire SD card
- Expands filesystem to fill partition
- Removes itself after successful expansion
- All subsequent boots are normal (no expansion)

### Step 4: Flash Shrunken Image to New Pis

Your compressed image (`tide-light-master.img.gz`) is now ready to deploy to multiple Raspberry Pis.

#### Using Raspberry Pi Imager (Recommended)

1. **Launch Raspberry Pi Imager** on Windows
2. Click **"Choose OS"** → **"Use custom"**
3. **Select** your compressed image: `tide-light-master.img.gz`
   - Imager natively supports .gz and .xz compressed images!
4. Click **"Choose Storage"** and select your SD card
5. **Optional - Customize settings** (click gear icon ⚙️):
   - **Hostname:** Change from default (e.g., `tide-light-01`, `tide-light-02`)
   - **WiFi credentials:** Update if different from master Pi
   - **Leave other settings as-is** (SSH, locale, etc. already configured in image)
6. Click **"Write"**
7. Wait for completion and eject SD card

**Repeat for each Pi** - Takes only 5-10 minutes per SD card!

### Step 5: First Boot of Cloned Pi

1. **Insert SD card** into new Raspberry Pi
2. **Power on** and wait 2-3 minutes for first boot

**What Happens Automatically:**

**During first boot:**
- ⏳ PiShrink expansion script runs (early in boot)
- ⏳ Partition expands to fill entire SD card
- ⏳ Filesystem expands to fill partition
- ⏳ Expansion script removes itself
- ✅ RTC sync (if RTC hardware installed)
- ✅ Bluetooth HCI0 brought up
- ✅ Auto-updater runs (pulls latest code from GitHub main branch)
- ✅ Main application starts
- ✅ BLE advertising begins

**After 2-3 minutes:**
- SSH available: `ssh pi@tide-light-01.local` (or whatever hostname you set)
- BLE scannable: "Tide Light" device visible
- LEDs active: Showing tide state (or red blink if no location configured yet)

**Note:** Each cloned Pi is independent - configure location and settings via BLE/web interface per device.

### Summary: Complete Workflow

**One-time setup (per master image):**
1. ✅ Set up and test Tide Light on one Pi (~2 hours)
2. ✅ Clean up device-specific data (~5 minutes)
3. ✅ Create image with Win32 Disk Imager (~15 minutes)
4. ✅ Shrink with PiShrink in WSL (~10 minutes)
5. ✅ Result: 1-2GB compressed image ready to deploy

**Per-device deployment (repeatable):**
1. ✅ Flash image with Raspberry Pi Imager (~5 minutes)
2. ✅ Customize hostname/WiFi in Imager (optional)
3. ✅ First boot auto-expands and starts services (~2 minutes)
4. ✅ Configure location via BLE/web interface (~2 minutes)

**Time saved:** Setup once in ~2.5 hours, deploy to 10 Pis in ~1 hour (vs ~25 hours without image replication!)

### What Gets Preserved in Master Image

✅ **Included:**
- Complete Tide Light installation
- All systemd services (tide-light, auto-updater, RTC sync, Bluetooth HCI)
- Python packages and dependencies
- Configuration files (if you didn't run factory reset)
- System packages and updates

❌ **Not Included (Device-Specific):**
- Hostname (customize in Imager per device)
- WiFi credentials (if different - customize in Imager)
- Device-specific tide data cache (cleared, fetched fresh on first boot)
- Logs (cleared to reduce image size)

### Image Maintenance

#### When to Update Master Image

**Recreate master image for:**
- ✅ System package updates (`apt upgrade`)
- ✅ New Python dependencies added to `requirements.txt`
- ✅ Installation script changes
- ✅ Major architectural changes

**Don't recreate for:**
- ❌ Code updates (auto-updater pulls from GitHub automatically)
- ❌ Configuration changes (per-device via BLE/web)
- ❌ Tide data updates (fetched automatically)

#### Update Process

When needed:
1. Update master Pi with changes
2. Test thoroughly
3. Repeat Steps 1-3 (clean, image, shrink)
4. Deploy new image to Pis (or let auto-updater handle code changes)

### Benefits of This Workflow

✅ **Massive time savings** - Hours → Minutes per device
✅ **Consistent deployments** - Every Pi identical, tested
✅ **95% smaller images** - 32GB → 1-2GB compressed
✅ **Auto-expansion** - No manual resizing needed
✅ **Easy updates** - Auto-updater handles code, image for system
✅ **Simple distribution** - Small files, cloud/USB friendly

---

## Troubleshooting

### LED Strip Not Working

**LEDs not lighting up:**
- Check external power supply is connected and ON
- Verify data wire connected to GPIO 18 (Pin 12)
- Check grounds connected: Pi GND ↔ LED GND ↔ Power supply GND
- Check LED count in config matches physical strip
- Check `invert` flag if LEDs seem reversed
- Review logs: `sudo journalctl -u tide-light -f`

**LEDs blink RED:**
- Normal error state: No tide data available yet
- Wait 1-2 minutes after boot for data fetch (requires internet)
- Check location is configured correctly via BLE/web/config.json
- Check logs for API errors: `sudo journalctl -u tide-light -f`

**Colors wrong:**
- Check `led_strip.invert` flag (try toggling)
- Ensure WS281x strip type matches configuration (GRB color order)

### BLE Not Advertising

**Cannot find "Tide Light" device:**
- Check HCI0 is up: `hciconfig hci0` (should show UP RUNNING)
- Check bluetoothd is disabled: `systemctl status bluetooth` (should be inactive)
- Restart service: `sudo systemctl restart bluetooth-hci0-up tide-light`
- Check logs: `sudo journalctl -u tide-light -f` (look for BLE errors)
- Verify pybleno installed: `pip3 list | grep pybleno`

**BLE characteristics not readable/writable:**
- Check service is running: `sudo systemctl status tide-light`
- Try disconnecting and reconnecting
- Check browser supports Web Bluetooth (Chrome/Edge, not Firefox/Safari)
- Check phone OS supports BLE (iOS 10+, Android 5+)

### RTC Not Working

**RTC time incorrect after reboot:**
- Check RTC detected: `tide-rtc status` (should show `/dev/rtc0`)
- Check I2C device: `sudo i2cdetect -y 1` (should show `UU` at 0x68)
- Check wiring: VCC=3.3V, GND=GND, SDA=Pin3, SCL=Pin5
- Check CR2032 battery installed and not dead (>2.5V)
- Manually sync time to RTC: `sudo hwclock --systohc`
- Check boot config: `grep -E "i2c|rtc" /boot/firmware/config.txt`
  - Should show: `dtparam=i2c_arm=on` and `dtoverlay=i2c-rtc,ds3231`
- Reboot and check again

**I2C shows `68` instead of `UU`:**
- RTC detected but driver not loaded
- Check boot config has RTC overlay: `grep rtc /boot/firmware/config.txt`
- Reboot to load driver

**No RTC device at all:**
- Check I2C enabled: `lsmod | grep i2c` (should show i2c_bcm2835)
- Check wiring connections
- Try manual I2C scan: `sudo i2cdetect -y 1`
- If nothing at 0x68, hardware issue (bad module or wiring)

### WiFi Not Connecting

**Cannot connect to WiFi:**
- Check SSID and password in `wpa_supplicant.conf` or raspi-config
- Check country code matches your location
- Check WiFi signal strength: `iwconfig wlan0`
- Restart WiFi: `sudo systemctl restart wpa_supplicant`
- Check WiFi enabled: `rfkill list` (should not be blocked)
- Try Ethernet temporarily to configure via raspi-config

### Service Crashes/Restarts

**tide-light.service keeps restarting:**
- Check logs for errors: `sudo journalctl -u tide-light -n 100`
- Common issues:
  - Missing Python packages: Reinstall via `sudo pip3 install -r requirements.txt`
  - Permission issues: Service runs as root, shouldn't occur
  - GPIO conflicts: Ensure no other services using GPIO 18
  - Config syntax errors: Validate `config.json` format
- Manual test run: `cd /home/pi/tide-light-v3/app && sudo python3 main.py`

### Auto-Updater Issues

**Updates not pulling:**
- Check internet connectivity: `ping -c 3 github.com`
- Check timer enabled: `systemctl status tide-light-updater.timer`
- Check updater logs: `sudo journalctl -u tide-light-updater -n 50`
- Manual trigger: `sudo systemctl start tide-light-updater`
- Check GitHub repository accessible: `git -C /home/pi/tide-light-v3 remote -v`

### SSH Connection Refused

**Cannot connect via SSH:**
- Check SSH enabled: `sudo systemctl status ssh` (on Pi with monitor/keyboard)
- Check SSH enabled during imaging (must be set explicitly)
- Check firewall rules (usually not an issue on Raspberry Pi OS)
- Check IP address: `hostname -I` (on Pi with monitor/keyboard)
- Try alternative IP lookup via router admin panel
- If using `.local`: try IP address directly instead

### Factory Reset

If configuration is corrupted or you want to start fresh:

```bash
sudo /home/pi/tide-light-v3/app/scripts/factory_reset.sh
```

This will:
1. Stop the tide-light service
2. Reset configuration to defaults (from `ConfigManager.DEFAULT_CONFIG`)
3. Clear tide data cache
4. Restart the service

**Note:** Does NOT uninstall services or system packages.

### Complete Reinstallation

If something is severely broken:

```bash
# Stop and disable all services
sudo systemctl stop tide-light tide-light-updater.timer tide-light-updater bluetooth-hci0-up
sudo systemctl disable tide-light tide-light-updater.timer tide-light-updater bluetooth-hci0-up

# Remove service files
sudo rm /etc/systemd/system/tide-light.service
sudo rm /etc/systemd/system/tide-light-updater.service
sudo rm /etc/systemd/system/tide-light-updater.timer
sudo rm /etc/systemd/system/bluetooth-hci0-up.service

# Reload systemd
sudo systemctl daemon-reload

# Re-clone repository (or git pull)
cd /home/pi
rm -rf tide-light-v3
git clone https://github.com/matsjp/tide-light-v3.git

# Re-run installation
cd tide-light-v3/app/scripts
sudo ./install_complete.sh

# Reboot
sudo reboot
```

---

## Additional Resources

- **Main README:** See project `README.md` for feature overview
- **Installation Plan:** See `docs/RASPBERRY_PI_INSTALLATION_PLAN.md` for technical details
- **Architecture:** See `docs/AGENTS.md` for code architecture and patterns
- **GitHub Repository:** https://github.com/matsjp/tide-light-v3
- **Raspberry Pi Documentation:** https://www.raspberrypi.com/documentation/

---

## Support

If you encounter issues not covered in this guide:

1. Check logs: `sudo journalctl -u tide-light -n 100`
2. Check GitHub Issues: https://github.com/matsjp/tide-light-v3/issues
3. File new issue with:
   - Raspberry Pi model
   - Raspberry Pi OS version
   - Hardware configuration
   - Relevant log output
   - Steps to reproduce

---

**Last Updated:** 2026-05-16
