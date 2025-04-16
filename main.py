#!/usr/bin/env python3
"""
Cross-Platform VPN Client Application

This is the main entry point for the VPN client application. It initializes the UI and
connects the various components together.
"""

import os
import sys
import time
import threading
import argparse
from typing import Dict, Any, Optional, List, Type

# Import core modules
from core.vpn_connection import VPNConnection, ConnectionStatus
from core.metrics import NetworkMetrics

# Import protocol implementations
from protocols.openvpn.openvpn_connection import OpenVPNConnection

# Import security module
from security.credentials import get_credential_storage

# Import platform utilities
from utils.platform import get_platform

# Define version
__version__ = "1.0.0"


class VPNProtocolFactory:
    _instance = None
    
    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance
    """Factory class for creating VPN protocol implementations."""
    
    @staticmethod
    def create_connection(protocol_type: str) -> Optional[VPNConnection]:
        try:
            if protocol_type == 'openvpn':
                return OpenVPNConnection()
            elif protocol_type == 'sstp':
                from protocols.sstp.sstp_connection import SSTPConnection
                return SSTPConnection()
            elif protocol_type == 'l2tp':
                from protocols.l2tp.l2tp_connection import L2TPConnection
                return L2TPConnection()
            elif protocol_type == 'pptp':
                from protocols.pptp.pptp_connection import PPTPConnection
                return PPTPConnection()
            else:
                raise ValueError(f"Unsupported protocol: {protocol_type}")
        except Exception as e:
            logging.error(f"Connection creation failed: {str(e)}")
            raise
        """Create a VPN connection instance for the specified protocol.
        
        Args:
            protocol_type: The type of VPN protocol to create ('openvpn', 'sstp', 'l2tp', 'pptp').
        
        Returns:
            Optional[VPNConnection]: A VPN connection instance, or None if the protocol is not supported.
        """
        protocol_type = protocol_type.lower()
        
        if protocol_type == 'openvpn':
            return OpenVPNConnection()
        elif protocol_type == 'sstp':
            # Placeholder for SSTP implementation
            print("SSTP protocol not yet implemented")
            return None
        elif protocol_type == 'l2tp':
            # Placeholder for L2TP implementation
            print("L2TP protocol not yet implemented")
            return None
        elif protocol_type == 'pptp':
            # Placeholder for PPTP implementation
            print("PPTP protocol not yet implemented")
            return None
        else:
            print(f"Unsupported protocol: {protocol_type}")
            return None


class VPNClientApp:
    """Main VPN client application class."""
    
    def __init__(self):
        """Initialize the VPN client application."""
        self.connection: Optional[VPNConnection] = None
        self.protocol_type: Optional[str] = None
        self.credential_storage = get_credential_storage()
        self.metrics = NetworkMetrics()
        self.monitoring_thread = None
        self.stop_monitoring = threading.Event()
    
    def connect(self, protocol_type: str, config: Dict[str, Any]) -> bool:
        """Connect to a VPN server using the specified protocol and configuration.
        
        Args:
            protocol_type: The type of VPN protocol to use.
            config: Configuration parameters for the connection.
        
        Returns:
            bool: True if connection was successfully initiated, False otherwise.
        """
        # Disconnect any existing connection
        if self.connection and self.connection.get_status() in [ConnectionStatus.CONNECTED, ConnectionStatus.CONNECTING]:
            self.disconnect()
        
        # Create a new connection
        self.connection = VPNProtocolFactory.create_connection(protocol_type)
        if not self.connection:
            return False
        
        # Store the protocol type
        self.protocol_type = protocol_type
        
        # Initiate the connection
        success = self.connection.connect(config)
        
        if success:
            # Start monitoring in a background thread
            self.stop_monitoring.clear()
            self.monitoring_thread = threading.Thread(target=self._monitor_connection)
            self.monitoring_thread.daemon = True
            self.monitoring_thread.start()
        
        return success
    
    def disconnect(self) -> bool:
        """Disconnect from the current VPN server.
        
        Returns:
            bool: True if disconnection was successful, False otherwise.
        """
        if not self.connection:
            return False
        
        # Stop the monitoring thread
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.stop_monitoring.set()
            self.monitoring_thread.join(timeout=2)
        
        # Disconnect the VPN connection
        return self.connection.disconnect()
    
    def get_status(self) -> ConnectionStatus:
        """Get the current status of the VPN connection.
        
        Returns:
            ConnectionStatus: The current connection status.
        """
        if not self.connection:
            return ConnectionStatus.DISCONNECTED
        
        return self.connection.get_status()
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get detailed information about the current connection.
        
        Returns:
            Dict[str, Any]: A dictionary containing connection details.
        """
        if not self.connection:
            return {}
        
        return self.connection.get_connection_info()
    
    def test_latency(self) -> Optional[float]:
        """Test the latency of the current VPN connection.
        
        Returns:
            Optional[float]: The latency in milliseconds, or None if the test failed.
        """
        if not self.connection or self.connection.get_status() != ConnectionStatus.CONNECTED:
            return None
        
        return self.connection.test_latency()
    
    def test_throughput(self) -> Dict[str, float]:
        """Test the throughput of the current VPN connection.
        
        Returns:
            Dict[str, float]: A dictionary containing throughput metrics.
        """
        if not self.connection or self.connection.get_status() != ConnectionStatus.CONNECTED:
            return {"download_speed": 0.0, "upload_speed": 0.0}
        
        return self.connection.test_throughput()
    
    def save_credentials(self, service_name: str, credentials: Dict[str, str]) -> bool:
        """Save VPN credentials securely.
        
        Args:
            service_name: A unique identifier for the VPN service.
            credentials: Dictionary containing credentials to store.
        
        Returns:
            bool: True if credentials were stored successfully, False otherwise.
        """
        return self.credential_storage.store_credentials(service_name, credentials)
    
    def load_credentials(self, service_name: str) -> Optional[Dict[str, str]]:
        """Load saved VPN credentials.
        
        Args:
            service_name: The unique identifier for the VPN service.
        
        Returns:
            Optional[Dict[str, str]]: The stored credentials, or None if not found.
        """
        return self.credential_storage.retrieve_credentials(service_name)
    
    def _monitor_connection(self) -> None:
        """Monitor the VPN connection and update metrics."""
        while not self.stop_monitoring.is_set() and self.connection:
            # Check if the connection is still active
            status = self.connection.get_status()
            if status != ConnectionStatus.CONNECTED:
                # Connection was lost or disconnected
                if status == ConnectionStatus.DISCONNECTED:
                    print("Connection was lost. Attempting to reconnect...")
                    # TODO: Implement reconnection logic
                break
            
            # Sleep for a short time
            time.sleep(1)


def parse_arguments():
    """Parse command-line arguments.
    
    Returns:
        argparse.Namespace: The parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(description="VPN Client Application")
    parser.add_argument(
        "--version", 
        action="store_true", 
        help="Show version information and exit"
    )
    parser.add_argument(
        "--platform", 
        action="store_true", 
        help="Show platform information and exit"
    )
    parser.add_argument(
        "--protocol", 
        choices=["openvpn", "sstp", "l2tp", "pptp"], 
        help="VPN protocol to use"
    )
    parser.add_argument(
        "--server", 
        help="VPN server address"
    )
    parser.add_argument(
        "--username", 
        help="VPN username"
    )
    parser.add_argument(
        "--password", 
        help="VPN password"
    )
    parser.add_argument(
        "--config", 
        help="Path to VPN configuration file"
    )
    
    return parser.parse_args()


class SimpleDashboardUI:
    """A simple text-based dashboard UI for the VPN client."""
    
    def __init__(self, app: VPNClientApp):
        """Initialize the dashboard UI.
        
        Args:
            app: The VPN client application instance.
        """
        self.app = app
    
    def display_status(self) -> None:
        """Display the current connection status."""
        status = self.app.get_status()
        print(f"\nConnection Status: {status.name}")
        
        if status == ConnectionStatus.CONNECTED:
            info = self.app.get_connection_info()
            print(f"Protocol: {info.get('protocol', 'Unknown')}")
            print(f"Server IP: {info.get('server_ip', 'Unknown')}")
            print(f"Assigned IP: {info.get('assigned_ip', 'Unknown')}")
            
            if 'connected_since' in info:
                connected_time = time.time() - info['connected_since']
                minutes, seconds = divmod(int(connected_time), 60)
                hours, minutes = divmod(minutes, 60)
                print(f"Connected for: {hours:02d}:{minutes:02d}:{seconds:02d}")
            
            print(f"Bytes sent: {info.get('bytes_sent', 0)}")
            print(f"Bytes received: {info.get('bytes_received', 0)}")
    
    def display_metrics(self) -> None:
        """Display network performance metrics."""
        if self.app.get_status() != ConnectionStatus.CONNECTED:
            print("\nMetrics not available: Not connected")
            return
        
        print("\nPerformance Metrics:")
        
        # Test latency
        print("Testing latency...")
        latency = self.app.test_latency()
        if latency is not None:
            print(f"Latency: {latency:.2f} ms")
        else:
            print("Latency test failed")
        
        # Test throughput
        print("Testing throughput...")
        throughput = self.app.test_throughput()
        print(f"Download speed: {throughput.get('download_speed', 0):.2f} Mbps")
        print(f"Upload speed: {throughput.get('upload_speed', 0):.2f} Mbps")
    
    def connect_dialog(self) -> None:
        """Display a dialog to connect to a VPN server."""
        print("\nConnect to VPN")
        print("Available protocols:")
        print("1. OpenVPN")
        print("2. SSTP")
        print("3. L2TP")
        print("4. PPTP")
        
        choice = input("Select protocol (1-4): ")
        protocol_map = {"1": "openvpn", "2": "sstp", "3": "l2tp", "4": "pptp"}
        
        if choice not in protocol_map:
            print("Invalid choice")
            return
        
        protocol = protocol_map[choice]
        
        # Get connection parameters
        if protocol == "openvpn":
            config_file = input("Enter path to OpenVPN config file: ")
            if not os.path.exists(config_file):
                print(f"Config file not found: {config_file}")
                return
            
            # Ask for credentials
            use_saved = input("Use saved credentials? (y/n): ").lower() == 'y'
            username = ""
            password = ""
            
            if use_saved:
                service_name = input("Enter service name: ")
                credentials = self.app.load_credentials(service_name)
                if credentials:
                    username = credentials.get("username", "")
                    password = credentials.get("password", "")
                    print(f"Loaded credentials for user: {username}")
                else:
                    print("No saved credentials found")
                    username = input("Username: ")
                    password = input("Password: ")
                    save = input("Save these credentials? (y/n): ").lower() == 'y'
                    if save:
                        self.app.save_credentials(service_name, {"username": username, "password": password})
            else:
                username = input("Username: ")
                password = input("Password: ")
                save = input("Save these credentials? (y/n): ").lower() == 'y'
                if save:
                    service_name = input("Enter service name: ")
                    self.app.save_credentials(service_name, {"username": username, "password": password})
            
            # Connect
            config = {
                "config_file": config_file,
                "username": username,
                "password": password
            }
            
            if self.app.connect(protocol, config):
                print("Connection initiated")
            else:
                print("Failed to initiate connection")
        else:
            print(f"{protocol.upper()} protocol not yet implemented")
    
    def disconnect_dialog(self) -> None:
        """Display a dialog to disconnect from the VPN server."""
        if self.app.get_status() in [ConnectionStatus.CONNECTED, ConnectionStatus.CONNECTING]:
            if self.app.disconnect():
                print("Disconnected successfully")
            else:
                print("Failed to disconnect")
        else:
            print("Not connected")
    
    def main_menu(self) -> None:
        """Display the main menu."""
        while True:
            print("\n===== VPN Client =====")
            self.display_status()
            
            print("\nOptions:")
            print("1. Connect")
            print("2. Disconnect")
            print("3. Show metrics")
            print("4. Exit")
            
            choice = input("Select option (1-4): ")
            
            if choice == "1":
                self.connect_dialog()
            elif choice == "2":
                self.disconnect_dialog()
            elif choice == "3":
                self.display_metrics()
            elif choice == "4":
                if self.app.get_status() in [ConnectionStatus.CONNECTED, ConnectionStatus.CONNECTING]:
                    confirm = input("You are still connected. Disconnect and exit? (y/n): ").lower()
                    if confirm == 'y':
                        self.app.disconnect()
                        break
                else:
                    break
            else:
                print("Invalid choice")


def main():
    """Main entry point for the application."""
    args = parse_arguments()
    
    # Handle version flag
    if args.version:
        print(f"VPN Client v{__version__}")
        return 0
    
    # Handle platform flag
    if args.platform:
        platform_name = get_platform()
        print(f"Running on platform: {platform_name}")
        return 0
    
    # Create the VPN client application
    app = VPNClientApp()
    
    # Handle command-line connection
    if args.protocol and args.server:
        config = {
            "server": args.server,
            "username": args.username,
            "password": args.password,
            "config_file": args.config
        }
        
        success = app.connect(args.protocol, config)
        if success:
            print(f"Connected to {args.server} using {args.protocol}")
            
            # Keep the application running
            try:
                while app.get_status() == ConnectionStatus.CONNECTED:
                    time.sleep(1.0)
            except KeyboardInterrupt:
                print("\nDisconnecting...")
                app.disconnect()
        else:
            print(f"Failed to connect to {args.server}")
            return 1
    else:
        # Create the dashboard UI
        ui = SimpleDashboardUI(app)
        
        # Display the main menu
        ui.main_menu()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())