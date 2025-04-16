\"""Core VPN Connection Interface Module.

This module defines the common interface that all VPN protocol implementations must adhere to.
It provides a consistent API for connecting, disconnecting, and checking status regardless of
the underlying VPN protocol being used.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from enum import Enum


class ConnectionStatus(Enum):
    """Enum representing the possible states of a VPN connection."""
    DISCONNECTED = 0
    CONNECTING = 1
    CONNECTED = 2
    DISCONNECTING = 3
    ERROR = 4


class VPNConnection(ABC):
    """Abstract base class defining the interface for all VPN protocol implementations.
    
    All protocol-specific implementations must inherit from this class and implement
    its abstract methods to provide a consistent interface for the application.
    """
    
    @abstractmethod
    def connect(self, config: Dict[str, Any]) -> bool:
        """Establish a VPN connection using the provided configuration.
        
        Args:
            config: A dictionary containing protocol-specific configuration parameters.
                   This may include server address, port, credentials, etc.
        
        Returns:
            bool: True if connection was successfully initiated, False otherwise.
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """Terminate the current VPN connection.
        
        Returns:
            bool: True if disconnection was successful, False otherwise.
        """
        pass
    
    @abstractmethod
    def get_status(self) -> ConnectionStatus:
        """Get the current status of the VPN connection.
        
        Returns:
            ConnectionStatus: An enum value representing the current connection status.
        """
        pass
    
    @abstractmethod
    def get_connection_info(self) -> Dict[str, Any]:
        """Get detailed information about the current connection.
        
        Returns:
            Dict[str, Any]: A dictionary containing connection details such as:
                - assigned_ip: The IP address assigned by the VPN server
                - server_ip: The IP address of the VPN server
                - protocol: The protocol being used
                - connected_since: Timestamp when the connection was established
                - bytes_sent: Number of bytes sent through the VPN tunnel
                - bytes_received: Number of bytes received through the VPN tunnel
        """
        pass
    
    @abstractmethod
    def test_latency(self) -> Optional[float]:
        """Test the latency of the current VPN connection.
        
        Returns:
            Optional[float]: The latency in milliseconds, or None if the test failed or no connection exists.
        """
        pass
    
    @abstractmethod
    def test_throughput(self) -> Dict[str, float]:
        """Test the throughput of the current VPN connection.
        
        Returns:
            Dict[str, float]: A dictionary containing throughput metrics:
                - download_speed: Download speed in Mbps
                - upload_speed: Upload speed in Mbps
        """
        pass