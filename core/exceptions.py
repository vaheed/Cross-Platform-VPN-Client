\"""VPN Connection Exceptions Module.

This module defines custom exceptions for the VPN client application.
"""

class VPNException(Exception):
    """Base exception class for all VPN-related exceptions."""
    pass


class ConnectionError(VPNException):
    """Exception raised when a connection attempt fails."""
    pass


class AuthenticationError(VPNException):
    """Exception raised when authentication fails."""
    pass


class ConfigurationError(VPNException):
    """Exception raised when there is an error in the configuration."""
    pass


class DisconnectionError(VPNException):
    """Exception raised when a disconnection attempt fails."""
    pass


class PermissionError(VPNException):
    """Exception raised when the application lacks necessary permissions."""
    pass


class ProtocolError(VPNException):
    """Exception raised when there is an error with the VPN protocol."""
    pass


class NetworkError(VPNException):
    """Exception raised when there is a network-related error."""
    pass


class TimeoutError(VPNException):
    """Exception raised when an operation times out."""
    pass


class CredentialStorageError(VPNException):
    """Exception raised when there is an error with credential storage."""
    pass