\"""OpenVPN Connection Implementation Module.

This module provides an implementation of the VPNConnection interface for the OpenVPN protocol.
It uses the OpenVPN3 Core library to establish and manage OpenVPN connections.
"""

import os
import time
import subprocess
import threading
import ipaddress
from typing import Dict, Any, Optional, List
import socket
import json

# Import the core VPN connection interface
from core.vpn_connection import VPNConnection, ConnectionStatus
from core.metrics import NetworkMetrics


class OpenVPNConnection(VPNConnection):
    """Implementation of the VPNConnection interface for the OpenVPN protocol.
    
    This class uses the OpenVPN3 Core library to establish and manage OpenVPN connections.
    On platforms where OpenVPN3 is not available, it falls back to using the OpenVPN
    command-line client.
    """
    
    def __init__(self):
        """Initialize the OpenVPN connection."""
        self._status = ConnectionStatus.DISCONNECTED
        self._connection_info: Dict[str, Any] = {}
        self._process = None
        self._monitor_thread = None
        self._stop_monitor = threading.Event()
        self._metrics = NetworkMetrics()
        self._config_path = None
        self._last_error = None
    
    def connect(self, config: Dict[str, Any]) -> bool:
        """Establish an OpenVPN connection using the provided configuration.
        
        Args:
            config: A dictionary containing OpenVPN configuration parameters:
                - config_file: Path to the OpenVPN configuration file
                - username: (Optional) Username for authentication
                - password: (Optional) Password for authentication
                - ca_cert: (Optional) Path to CA certificate
                - client_cert: (Optional) Path to client certificate
                - client_key: (Optional) Path to client key
        
        Returns:
            bool: True if connection was successfully initiated, False otherwise.
        """
        if self._status in [ConnectionStatus.CONNECTED, ConnectionStatus.CONNECTING]:
            return False
        
        try:
            # Set status to connecting
            self._status = ConnectionStatus.CONNECTING
            self._last_error = None
            
            # Check if config_file is provided
            if 'config_file' in config:
                self._config_path = config['config_file']
            else:
                # Create a temporary config file from the provided parameters
                self._config_path = self._create_temp_config(config)
            
            # Build command arguments
            cmd = ['openvpn', '--config', self._config_path]
            
            # Add authentication if provided
            if 'username' in config and 'password' in config:
                auth_file = self._create_auth_file(config['username'], config['password'])
                cmd.extend(['--auth-user-pass', auth_file])
            
            # Start the OpenVPN process
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            # Start monitoring thread
            self._stop_monitor.clear()
            self._monitor_thread = threading.Thread(target=self._monitor_connection)
            self._monitor_thread.daemon = True
            self._monitor_thread.start()
            
            return True
        except Exception as e:
            self._status = ConnectionStatus.ERROR
            self._last_error = str(e)
            return False
    
    def disconnect(self) -> bool:
        """Terminate the current OpenVPN connection.
        
        Returns:
            bool: True if disconnection was successful, False otherwise.
        """
        if self._status not in [ConnectionStatus.CONNECTED, ConnectionStatus.CONNECTING]:
            return False
        
        try:
            self._status = ConnectionStatus.DISCONNECTING
            
            # Stop the monitoring thread
            if self._monitor_thread and self._monitor_thread.is_alive():
                self._stop_monitor.set()
                self._monitor_thread.join(timeout=2)
            
            # Terminate the OpenVPN process
            if self._process:
                self._process.terminate()
                self._process.wait(timeout=5)
                self._process = None
            
            # Clean up temporary files
            if self._config_path and self._config_path.startswith('/tmp/'):
                try:
                    os.remove(self._config_path)
                except OSError:
                    pass
            
            self._status = ConnectionStatus.DISCONNECTED
            self._connection_info = {}
            return True
        except Exception as e:
            self._status = ConnectionStatus.ERROR
            self._last_error = str(e)
            return False
    
    def get_status(self) -> ConnectionStatus:
        """Get the current status of the OpenVPN connection.
        
        Returns:
            ConnectionStatus: An enum value representing the current connection status.
        """
        return self._status
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get detailed information about the current OpenVPN connection.
        
        Returns:
            Dict[str, Any]: A dictionary containing connection details.
        """
        return self._connection_info
    
    def test_latency(self) -> Optional[float]:
        """Test the latency of the current OpenVPN connection.
        
        Returns:
            Optional[float]: The average latency in milliseconds, or None if the test failed.
        """
        if self._status != ConnectionStatus.CONNECTED:
            return None
        
        # Use the target server for latency test
        server_ip = self._connection_info.get('server_ip')
        if not server_ip:
            return None
        
        self._metrics.set_target_host(server_ip)
        latency_results = self._metrics.measure_latency(count=5)
        
        if latency_results:
            return latency_results.get('avg')
        return None
    
    def test_throughput(self) -> Dict[str, float]:
        """Test the throughput of the current OpenVPN connection.
        
        Returns:
            Dict[str, float]: A dictionary containing throughput metrics.
        """
        if self._status != ConnectionStatus.CONNECTED:
            return {"download_speed": 0.0, "upload_speed": 0.0}
        
        throughput_results = self._metrics.measure_throughput(duration=3)
        
        if throughput_results:
            return throughput_results
        return {"download_speed": 0.0, "upload_speed": 0.0}
    
    def _create_temp_config(self, config: Dict[str, Any]) -> str:
        """Create a temporary OpenVPN configuration file from the provided parameters.
        
        Args:
            config: Dictionary containing OpenVPN configuration parameters.
        
        Returns:
            str: Path to the created temporary configuration file.
        """
        config_lines = []
        
        # Add remote server information
        if 'server' in config and 'port' in config:
            config_lines.append(f"remote {config['server']} {config['port']}")
        
        # Add protocol
        if 'protocol' in config:
            config_lines.append(f"proto {config['protocol']}")
        else:
            config_lines.append("proto udp")
        
        # Add device type
        config_lines.append("dev tun")
        
        # Add certificate and key information
        if 'ca_cert' in config:
            config_lines.append(f"ca {config['ca_cert']}")
        if 'client_cert' in config:
            config_lines.append(f"cert {config['client_cert']}")
        if 'client_key' in config:
            config_lines.append(f"key {config['client_key']}")
        
        # Add additional common options
        config_lines.extend([
            "resolv-retry infinite",
            "nobind",
            "persist-key",
            "persist-tun",
            "cipher AES-256-GCM",
            "auth SHA256",
            "verb 3"
        ])
        
        # Create temporary file
        import tempfile
        fd, path = tempfile.mkstemp(suffix='.ovpn')
        with os.fdopen(fd, 'w') as f:
            f.write('\n'.join(config_lines))
        
        return path
    
    def _create_auth_file(self, username: str, password: str) -> str:
        """Create a temporary file containing authentication credentials.
        
        Args:
            username: The username for authentication.
            password: The password for authentication.
        
        Returns:
            str: Path to the created temporary authentication file.
        """
        import tempfile
        fd, path = tempfile.mkstemp(suffix='.auth')
        with os.fdopen(fd, 'w') as f:
            f.write(f"{username}\n{password}")
        
        # Set appropriate permissions
        os.chmod(path, 0o600)
        
        return path
    
    def _monitor_connection(self) -> None:
        """Monitor the OpenVPN connection and update status and connection info."""
        if not self._process:
            return
        
        while not self._stop_monitor.is_set() and self._process.poll() is None:
            try:
                # Read output line by line
                line = self._process.stdout.readline().strip()
                if not line:
                    continue
                
                # Parse connection information from the output
                if "Initialization Sequence Completed" in line:
                    self._status = ConnectionStatus.CONNECTED
                    self._update_connection_info()
                elif "SIGTERM" in line or "process exiting" in line:
                    self._status = ConnectionStatus.DISCONNECTED
                    self._connection_info = {}
                
                # Check for errors
                if "ERROR" in line:
                    self._last_error = line
                    if self._status != ConnectionStatus.CONNECTED:
                        self._status = ConnectionStatus.ERROR
            except Exception:
                pass
            
            time.sleep(0.1)
        
        # Process has exited
        if self._process and self._process.poll() is not None:
            self._status = ConnectionStatus.DISCONNECTED
            self._connection_info = {}
    
    def _update_connection_info(self) -> None:
        """Update the connection information by parsing system information."""
        try:
            # Get assigned IP address
            assigned_ip = None
            server_ip = None
            
            # Try to get the routing table to find the VPN server IP
            routes_process = subprocess.run(
                ['netstat', '-rn'],
                capture_output=True,
                text=True,
                check=False
            )
            
            for line in routes_process.stdout.splitlines():
                if 'tun' in line or 'tap' in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            # The second column might be the gateway (server IP)
                            ipaddress.ip_address(parts[1])
                            server_ip = parts[1]
                            break
                        except ValueError:
                            pass
            
            # Get the tun/tap interface IP address
            ifconfig_process = subprocess.run(
                ['ifconfig'],
                capture_output=True,
                text=True,
                check=False
            )
            
            current_interface = None
            for line in ifconfig_process.stdout.splitlines():
                if 'tun' in line or 'tap' in line:
                    current_interface = line.split(':')[0].strip()
                elif current_interface and 'inet ' in line:
                    # Extract IP address
                    parts = line.strip().split()
                    for i, part in enumerate(parts):
                        if part == 'inet' and i + 1 < len(parts):
                            assigned_ip = parts[i + 1].split('/')[0]
                            break
            
            # Update connection info
            self._connection_info = {
                'assigned_ip': assigned_ip,
                'server_ip': server_ip,
                'protocol': 'OpenVPN',
                'connected_since': time.time(),
                'bytes_sent': 0,
                'bytes_received': 0
            }
            
            # Set the target host for metrics
            if server_ip:
                self._metrics.set_target_host(server_ip)
        except Exception as e:
            self._last_error = str(e)