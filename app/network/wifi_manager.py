"""
WiFi Manager for Raspberry Pi.

Handles WiFi network scanning and connection using NetworkManager (nmcli).
Falls back to wpa_cli if nmcli is not available.
"""

import subprocess
import logging
import re
from typing import List, Dict, Optional


class WiFiManager:
    """
    Manages WiFi operations on Raspberry Pi.
    Uses nmcli (NetworkManager) as primary tool, wpa_cli as fallback.
    """
    
    def __init__(self):
        """Initialize WiFi manager and detect available tools."""
        self._tool = self._detect_tool()
        self._interface = self._detect_interface()
        logging.info(f"[WiFi Manager] Initialized with tool: {self._tool}, interface: {self._interface}")
    
    def _detect_tool(self) -> str:
        """
        Detect which WiFi management tool is available.
        
        Returns:
            'nmcli', 'wpa_cli', or 'none'
        """
        try:
            subprocess.run(['nmcli', '--version'], capture_output=True, check=True)
            return 'nmcli'
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        try:
            subprocess.run(['wpa_cli', '-v'], capture_output=True, check=True)
            return 'wpa_cli'
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        return 'none'
    
    def _detect_interface(self) -> Optional[str]:
        """
        Detect WiFi interface name.
        
        Returns:
            Interface name (e.g., 'wlan0') or None if not found
        """
        try:
            result = subprocess.run(
                ['ls', '/sys/class/net'],
                capture_output=True,
                text=True,
                check=True
            )
            interfaces = result.stdout.strip().split('\n')
            
            # Look for wlan interface
            for iface in interfaces:
                if iface.startswith('wlan'):
                    return iface
            
            return None
        except Exception as e:
            logging.error(f"[WiFi Manager] Error detecting interface: {e}")
            return None
    
    def is_wifi_available(self) -> bool:
        """
        Check if WiFi hardware and management tools are available.
        
        Returns:
            True if WiFi is available, False otherwise
        """
        return self._tool != 'none' and self._interface is not None
    
    def scan_networks(self) -> List[Dict[str, any]]:
        """
        Scan for available WiFi networks.
        
        Returns:
            List of network dictionaries with keys:
            - ssid: Network name
            - signal: Signal strength in dBm (e.g., -45)
            - security: Security type (e.g., "WPA2", "Open")
        """
        if not self.is_wifi_available():
            logging.warning("[WiFi Manager] WiFi not available")
            return []
        
        if self._tool == 'nmcli':
            return self._scan_nmcli()
        elif self._tool == 'wpa_cli':
            return self._scan_wpa_cli()
        
        return []
    
    def _scan_nmcli(self) -> List[Dict[str, any]]:
        """
        Scan networks using nmcli.
        
        Returns:
            List of network dictionaries
        """
        try:
            # Rescan networks
            subprocess.run(
                ['nmcli', 'device', 'wifi', 'rescan'],
                capture_output=True,
                timeout=10
            )
            
            # Get network list
            result = subprocess.run(
                ['nmcli', '-t', '-f', 'SSID,SIGNAL,SECURITY', 'device', 'wifi', 'list'],
                capture_output=True,
                text=True,
                check=True,
                timeout=10
            )
            
            networks = []
            seen_ssids = set()
            
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                
                parts = line.split(':')
                if len(parts) < 3:
                    continue
                
                ssid = parts[0].strip()
                signal_str = parts[1].strip()
                security = parts[2].strip()
                
                # Skip empty SSIDs (hidden networks)
                if not ssid or ssid == '--':
                    continue
                
                # Skip duplicates (same SSID can appear multiple times)
                if ssid in seen_ssids:
                    continue
                seen_ssids.add(ssid)
                
                # Convert signal percentage to approximate dBm
                try:
                    signal_percent = int(signal_str)
                    signal_dbm = -100 + (signal_percent * 70 // 100)  # Approximate conversion
                except ValueError:
                    signal_dbm = -100
                
                # Simplify security string
                if not security or security == '--':
                    security_type = "Open"
                elif 'WPA3' in security:
                    security_type = "WPA3"
                elif 'WPA2' in security:
                    security_type = "WPA2"
                elif 'WPA' in security:
                    security_type = "WPA"
                elif 'WEP' in security:
                    security_type = "WEP"
                else:
                    security_type = "Secured"
                
                networks.append({
                    'ssid': ssid,
                    'signal': signal_dbm,
                    'security': security_type
                })
            
            # Sort by signal strength (strongest first)
            networks.sort(key=lambda x: x['signal'], reverse=True)
            
            logging.info(f"[WiFi Manager] Found {len(networks)} networks via nmcli")
            return networks
            
        except subprocess.TimeoutExpired:
            logging.error("[WiFi Manager] Scan timeout with nmcli")
            return []
        except subprocess.CalledProcessError as e:
            logging.error(f"[WiFi Manager] nmcli scan error: {e}")
            return []
        except Exception as e:
            logging.error(f"[WiFi Manager] Unexpected scan error: {e}")
            return []
    
    def _scan_wpa_cli(self) -> List[Dict[str, any]]:
        """
        Scan networks using wpa_cli (fallback method).
        
        Returns:
            List of network dictionaries
        """
        try:
            # Trigger scan
            subprocess.run(
                ['wpa_cli', '-i', self._interface, 'scan'],
                capture_output=True,
                timeout=5
            )
            
            # Wait a bit for scan to complete
            import time
            time.sleep(2)
            
            # Get scan results
            result = subprocess.run(
                ['wpa_cli', '-i', self._interface, 'scan_results'],
                capture_output=True,
                text=True,
                check=True,
                timeout=5
            )
            
            networks = []
            seen_ssids = set()
            
            for line in result.stdout.strip().split('\n')[1:]:  # Skip header
                if not line:
                    continue
                
                parts = line.split('\t')
                if len(parts) < 5:
                    continue
                
                ssid = parts[4].strip()
                
                # Skip empty SSIDs
                if not ssid:
                    continue
                
                # Skip duplicates
                if ssid in seen_ssids:
                    continue
                seen_ssids.add(ssid)
                
                # Parse signal strength
                try:
                    signal_dbm = int(parts[2])
                except ValueError:
                    signal_dbm = -100
                
                # Parse security
                flags = parts[3]
                if 'WPA3' in flags:
                    security_type = "WPA3"
                elif 'WPA2' in flags:
                    security_type = "WPA2"
                elif 'WPA' in flags:
                    security_type = "WPA"
                elif 'WEP' in flags:
                    security_type = "WEP"
                else:
                    security_type = "Open"
                
                networks.append({
                    'ssid': ssid,
                    'signal': signal_dbm,
                    'security': security_type
                })
            
            # Sort by signal strength
            networks.sort(key=lambda x: x['signal'], reverse=True)
            
            logging.info(f"[WiFi Manager] Found {len(networks)} networks via wpa_cli")
            return networks
            
        except Exception as e:
            logging.error(f"[WiFi Manager] wpa_cli scan error: {e}")
            return []
    
    def connect_network(self, ssid: str, password: str) -> bool:
        """
        Connect to a WiFi network.
        
        Args:
            ssid: Network SSID to connect to
            password: WPA password (empty string for open networks)
        
        Returns:
            True if connection successful, False otherwise
        """
        if not self.is_wifi_available():
            logging.error("[WiFi Manager] WiFi not available")
            return False
        
        if self._tool == 'nmcli':
            return self._connect_nmcli(ssid, password)
        elif self._tool == 'wpa_cli':
            return self._connect_wpa_cli(ssid, password)
        
        return False
    
    def _connect_nmcli(self, ssid: str, password: str) -> bool:
        """
        Connect to network using nmcli.
        
        Args:
            ssid: Network SSID
            password: WPA password
        
        Returns:
            True if successful
        """
        try:
            logging.info(f"[WiFi Manager] Connecting to '{ssid}' via nmcli")
            
            if password:
                # Connect with password
                result = subprocess.run(
                    ['nmcli', 'device', 'wifi', 'connect', ssid, 'password', password],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
            else:
                # Connect to open network
                result = subprocess.run(
                    ['nmcli', 'device', 'wifi', 'connect', ssid],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
            
            success = result.returncode == 0
            
            if success:
                logging.info(f"[WiFi Manager] Successfully connected to '{ssid}'")
            else:
                logging.error(f"[WiFi Manager] Connection failed: {result.stderr}")
            
            return success
            
        except subprocess.TimeoutExpired:
            logging.error(f"[WiFi Manager] Connection timeout for '{ssid}'")
            return False
        except Exception as e:
            logging.error(f"[WiFi Manager] Connection error: {e}")
            return False
    
    def _connect_wpa_cli(self, ssid: str, password: str) -> bool:
        """
        Connect to network using wpa_cli (fallback method).
        
        Args:
            ssid: Network SSID
            password: WPA password
        
        Returns:
            True if successful
        """
        try:
            logging.info(f"[WiFi Manager] Connecting to '{ssid}' via wpa_cli")
            
            # This is a simplified implementation
            # For production, you'd need to properly configure wpa_supplicant
            
            # Add network
            result = subprocess.run(
                ['wpa_cli', '-i', self._interface, 'add_network'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            network_id = result.stdout.strip()
            
            # Set SSID
            subprocess.run(
                ['wpa_cli', '-i', self._interface, 'set_network', network_id, 'ssid', f'"{ssid}"'],
                capture_output=True,
                timeout=5
            )
            
            if password:
                # Set password
                subprocess.run(
                    ['wpa_cli', '-i', self._interface, 'set_network', network_id, 'psk', f'"{password}"'],
                    capture_output=True,
                    timeout=5
                )
            else:
                # Open network
                subprocess.run(
                    ['wpa_cli', '-i', self._interface, 'set_network', network_id, 'key_mgmt', 'NONE'],
                    capture_output=True,
                    timeout=5
                )
            
            # Enable network
            subprocess.run(
                ['wpa_cli', '-i', self._interface, 'enable_network', network_id],
                capture_output=True,
                timeout=5
            )
            
            # Save configuration
            subprocess.run(
                ['wpa_cli', '-i', self._interface, 'save_config'],
                capture_output=True,
                timeout=5
            )
            
            logging.info(f"[WiFi Manager] Configured '{ssid}' via wpa_cli")
            return True
            
        except Exception as e:
            logging.error(f"[WiFi Manager] wpa_cli connection error: {e}")
            return False
    
    def get_current_network(self) -> Optional[str]:
        """
        Get currently connected network SSID.
        
        Returns:
            SSID of connected network, or None if not connected
        """
        if not self.is_wifi_available():
            return None
        
        if self._tool == 'nmcli':
            return self._get_current_nmcli()
        elif self._tool == 'wpa_cli':
            return self._get_current_wpa_cli()
        
        return None
    
    def _get_current_nmcli(self) -> Optional[str]:
        """Get current network using nmcli."""
        try:
            result = subprocess.run(
                ['nmcli', '-t', '-f', 'ACTIVE,SSID', 'device', 'wifi'],
                capture_output=True,
                text=True,
                check=True,
                timeout=5
            )
            
            for line in result.stdout.strip().split('\n'):
                if line.startswith('yes:'):
                    ssid = line.split(':', 1)[1]
                    return ssid if ssid and ssid != '--' else None
            
            return None
            
        except Exception as e:
            logging.error(f"[WiFi Manager] Error getting current network: {e}")
            return None
    
    def _get_current_wpa_cli(self) -> Optional[str]:
        """Get current network using wpa_cli."""
        try:
            result = subprocess.run(
                ['wpa_cli', '-i', self._interface, 'status'],
                capture_output=True,
                text=True,
                check=True,
                timeout=5
            )
            
            for line in result.stdout.strip().split('\n'):
                if line.startswith('ssid='):
                    return line.split('=', 1)[1]
            
            return None
            
        except Exception as e:
            logging.error(f"[WiFi Manager] Error getting current network: {e}")
            return None
    
    def get_connection_status(self) -> Dict[str, any]:
        """
        Get detailed WiFi connection status.
        
        Returns:
            Dictionary with:
            - connected: bool
            - ssid: str or None
            - signal: int (dBm) or None
            - ip: str or None
            - status: str ("connected", "disconnected", "connecting")
        """
        if not self.is_wifi_available():
            return {
                'connected': False,
                'ssid': None,
                'signal': None,
                'ip': None,
                'status': 'unavailable'
            }
        
        ssid = self.get_current_network()
        
        if not ssid:
            return {
                'connected': False,
                'ssid': None,
                'signal': None,
                'ip': None,
                'status': 'disconnected'
            }
        
        # Get signal strength and IP
        signal = self._get_signal_strength()
        ip = self._get_ip_address()
        
        return {
            'connected': True,
            'ssid': ssid,
            'signal': signal,
            'ip': ip,
            'status': 'connected'
        }
    
    def _get_signal_strength(self) -> Optional[int]:
        """Get current signal strength in dBm."""
        if self._tool == 'nmcli':
            try:
                result = subprocess.run(
                    ['nmcli', '-t', '-f', 'ACTIVE,SIGNAL', 'device', 'wifi'],
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=5
                )
                
                for line in result.stdout.strip().split('\n'):
                    if line.startswith('yes:'):
                        signal_str = line.split(':', 1)[1]
                        try:
                            signal_percent = int(signal_str)
                            return -100 + (signal_percent * 70 // 100)
                        except ValueError:
                            pass
                
            except Exception:
                pass
        
        return None
    
    def _get_ip_address(self) -> Optional[str]:
        """Get IP address of WiFi interface."""
        if not self._interface:
            return None
        
        try:
            result = subprocess.run(
                ['ip', '-4', 'addr', 'show', self._interface],
                capture_output=True,
                text=True,
                check=True,
                timeout=5
            )
            
            # Parse IP address from output
            match = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+)', result.stdout)
            if match:
                return match.group(1)
            
        except Exception:
            pass
        
        return None
