#!/usr/bin/env python3
"""
Build Script for VPN Client

This script creates standalone executables for the VPN client application
using PyInstaller. It detects the current platform and builds accordingly,
but can also build for specific platforms when specified.
"""

import os
import sys
import platform
import subprocess
import shutil
from typing import List, Optional

# Import our platform detection module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.platform import get_platform


def ensure_pyinstaller():
    """Ensure PyInstaller is installed."""
    try:
        import PyInstaller
        print("PyInstaller is already installed.")
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])


def install_dependencies():
    """Install all dependencies from requirements.txt."""
    print("Installing dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])


def build_for_platform(target_platform: Optional[str] = None) -> bool:
    """Build the executable for the specified platform.
    
    Args:
        target_platform: The platform to build for. If None, builds for the current platform.
    
    Returns:
        bool: True if the build was successful, False otherwise.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    valid_platforms = ['windows', 'macos', 'linux']
    if target_platform not in valid_platforms:
        raise ValueError(f"Invalid platform: {target_platform}. Supported platforms: {valid_platforms}")

    try:
        logger.info(f"Starting build for {target_platform}")
        print(f"Building for platform: {target_platform}")
        
        # Validate build environment
        if target_platform == 'macos' and not sys.platform == 'darwin':
            raise EnvironmentError("macOS builds require Darwin environment")
        
        # Base PyInstaller command
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--onefile",  # Create a single executable file
            "--clean",    # Clean PyInstaller cache
            "--name", f"vpnclient-{target_platform}",
            "main.py"     # Entry point
        ]
    
    # Platform-specific options
    if target_platform == "windows":
        cmd.extend(["--windowed"])  # No console window
        # Add Windows icon if available
        if os.path.exists("resources/icons/vpnclient.ico"):
            cmd.extend(["--icon", "resources/icons/vpnclient.ico"])
    elif target_platform == "macos":
        # Add macOS icon if available
        if os.path.exists("resources/icons/vpnclient.icns"):
            cmd.extend(["--icon", "resources/icons/vpnclient.icns"])
    
    # Add data files and resources
    cmd.extend(["--add-data", f"protocols:protocols"])
    
    # Run PyInstaller
    try:
        subprocess.check_call(cmd)
        print(f"Successfully built executable for {target_platform}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error building executable for {target_platform}: {e}")
        return False


def run_tests():
    """Run the test suite to verify functionality."""
    print("Running tests...")
    try:
        subprocess.check_call([sys.executable, "-m", "pytest", "-xvs"])
        print("All tests passed!")
        return True
    except subprocess.CalledProcessError:
        print("Some tests failed.")
        return False


def main():
    """Main entry point for the build script."""
    import argparse
    import logging
    
    logging.basicConfig(level=logging.INFO)
    
    parser = argparse.ArgumentParser(description="Build VPN Client executables")
    parser.add_argument(
        "--platform", 
        choices=["windows", "macos", "linux", "all"], 
        help="Target platform to build for"
    )
    parser.add_argument(
        "--skip-tests", 
        action="store_true", 
        help="Skip running tests before building"
    )
    parser.add_argument(
        "--skip-deps", 
        action="store_true", 
        help="Skip installing dependencies"
    )
    
    args = parser.parse_args()
    
    # Ensure PyInstaller is installed
    ensure_pyinstaller()
    
    # Install dependencies if not skipped
    if not args.skip_deps:
        install_dependencies()
    
    # Run tests if not skipped
    if not args.skip_tests:
        if not run_tests():
            print("Warning: Tests failed, but continuing with build...")
    
    # Determine which platforms to build for
    platforms_to_build = []
    if args.platform == "all":
        platforms_to_build = ["windows", "macos", "linux"]
    elif args.platform:
        platforms_to_build = [args.platform]
    else:
        # Build for current platform only
        platforms_to_build = [get_platform()]
    
    # Build for each platform
    success = True
    for platform_name in platforms_to_build:
        if not build_for_platform(platform_name):
            success = False
    
    if success:
        print("\nBuild completed successfully!")
        print("Executables can be found in the 'dist' directory.")
    else:
        print("\nBuild completed with errors.")
        sys.exit(1)


if __name__ == "__main__":
    main()