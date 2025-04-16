"""Platform Utility Module.

This module provides utility functions for detecting the current platform and
performing platform-specific operations.
"""

import os
import sys
import platform
from typing import Literal, Optional

# Platform type definitions
PlatformType = Literal['windows', 'macos', 'linux', 'android', 'ios', 'unknown']


def get_platform() -> PlatformType:
    """Detect the current platform.
    
    Returns:
        PlatformType: The detected platform type.
    """
    system = platform.system().lower()
    
    if system == 'windows' or system == 'win32':
        return 'windows'
    elif system == 'darwin':
        return 'macos'
    elif system == 'linux':
        # Check if running on Android
        if 'ANDROID_ROOT' in os.environ or os.path.exists('/system/bin/adb'):
            return 'android'
        else:
            return 'linux'
    elif system == 'ios':
        return 'ios'
    else:
        return 'unknown'


def is_admin() -> bool:
    """Check if the application is running with administrator/root privileges.
    
    Returns:
        bool: True if running with elevated privileges, False otherwise.
    """
    platform_type = get_platform()
    
    if platform_type == 'windows':
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False
    else:  # Unix-like systems (macOS, Linux, Android)
        return os.geteuid() == 0


def get_config_dir() -> str:
    """Get the platform-specific configuration directory for the application.
    
    Returns:
        str: Path to the configuration directory.
    """
    app_name = 'vpnclient'
    platform_type = get_platform()
    
    if platform_type == 'windows':
        base_dir = os.environ.get('APPDATA', os.path.expanduser('~'))
        return os.path.join(base_dir, app_name)
    elif platform_type == 'macos':
        return os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', app_name)
    elif platform_type == 'linux':
        xdg_config_home = os.environ.get('XDG_CONFIG_HOME')
        if xdg_config_home:
            return os.path.join(xdg_config_home, app_name)
        else:
            return os.path.join(os.path.expanduser('~'), '.config', app_name)
    elif platform_type == 'android':
        # On Android, app-specific directories are typically managed by the system
        # This is a fallback for Python apps running on Android
        return os.path.join(os.path.expanduser('~'), '.config', app_name)
    else:
        return os.path.join(os.path.expanduser('~'), f'.{app_name}')


def get_logs_dir() -> str:
    """Get the platform-specific logs directory for the application.
    
    Returns:
        str: Path to the logs directory.
    """
    app_name = 'vpnclient'
    platform_type = get_platform()
    
    if platform_type == 'windows':
        base_dir = os.environ.get('APPDATA', os.path.expanduser('~'))
        return os.path.join(base_dir, app_name, 'logs')
    elif platform_type == 'macos':
        return os.path.join(os.path.expanduser('~'), 'Library', 'Logs', app_name)
    elif platform_type == 'linux':
        xdg_state_home = os.environ.get('XDG_STATE_HOME')
        if xdg_state_home:
            return os.path.join(xdg_state_home, app_name, 'logs')
        else:
            return os.path.join(os.path.expanduser('~'), '.local', 'state', app_name, 'logs')
    elif platform_type == 'android':
        return os.path.join(os.path.expanduser('~'), '.local', 'share', app_name, 'logs')
    else:
        return os.path.join(os.path.expanduser('~'), f'.{app_name}', 'logs')


def ensure_directory_exists(directory: str) -> None:
    """Ensure that the specified directory exists, creating it if necessary.
    
    Args:
        directory: The directory path to ensure exists.
    """
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)


def get_network_interfaces() -> list:
    """Get a list of network interfaces on the current system.
    
    Returns:
        list: A list of network interface names.
    """
    platform_type = get_platform()
    interfaces = []
    
    try:
        if platform_type == 'windows':
            # On Windows, use ipconfig
            import subprocess
            output = subprocess.check_output(['ipconfig', '/all'], text=True)
            for line in output.splitlines():
                if 'adapter' in line.lower() and ':' in line:
                    interfaces.append(line.split(':')[0].strip())
        else:  # Unix-like systems
            # Use the more portable approach of reading from /sys/class/net
            if os.path.exists('/sys/class/net'):
                interfaces = os.listdir('/sys/class/net')
            else:
                # Fallback to ifconfig
                import subprocess
                output = subprocess.check_output(['ifconfig'], text=True)
                current_if = None
                for line in output.splitlines():
                    if not line.startswith(' ') and ':' in line:
                        current_if = line.split(':')[0].strip()
                        if current_if:
                            interfaces.append(current_if)
    except Exception:
        pass
    
    return interfaces


def is_vpn_supported(protocol: str) -> bool:
    """Check if the specified VPN protocol is supported on the current platform.
    
    Args:
        protocol: The VPN protocol to check ('openvpn', 'sstp', 'l2tp', 'pptp').
    
    Returns:
        bool: True if the protocol is supported, False otherwise.
    """
    protocol = protocol.lower()
    platform_type = get_platform()
    
    # OpenVPN is supported on all platforms if the client is installed
    if protocol == 'openvpn':
        try:
            import subprocess
            subprocess.check_output(['openvpn', '--version'], stderr=subprocess.STDOUT)
            return True
        except Exception:
            return False
    
    # SSTP is primarily supported on Windows, but can be used on other platforms with appropriate packages
    elif protocol == 'sstp':
        if platform_type == 'windows':
            return True
        else:
            try:
                import subprocess
                subprocess.check_output(['sstpc', '--version'], stderr=subprocess.STDOUT)
                return True
            except Exception:
                return False
    
    # L2TP/IPsec is supported on most platforms
    elif protocol == 'l2tp':
        if platform_type == 'windows':
            return True
        elif platform_type == 'macos':
            return True
        else:  # Linux/Android
            try:
                import subprocess
                subprocess.check_output(['xl2tpd', '-v'], stderr=subprocess.STDOUT)
                return True
            except Exception:
                return False
    
    # PPTP is supported on most platforms but is considered insecure
    elif protocol == 'pptp':
        if platform_type == 'windows':
            return True
        elif platform_type == 'macos':
            return True
        else:  # Linux/Android
            try:
                import subprocess
                subprocess.check_output(['pptpd', '--version'], stderr=subprocess.STDOUT)
                return True
            except Exception:
                return False
    
    return False