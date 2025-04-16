#!/usr/bin/env python3
"""
Test Script for VPN Client Executable

This script tests the functionality of the standalone VPN client executable.
It can be used to verify that the executable works correctly after building.
"""

import os
import sys
import subprocess
import platform
import time
from typing import Optional

# Import our platform detection module if running as a script
if __name__ == "__main__":
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from utils.platform import get_platform
else:
    from utils.platform import get_platform


def get_executable_path() -> str:
    """Get the path to the VPN client executable for the current platform.
    
    Returns:
        str: Path to the executable
    """
    platform_name = get_platform()
    base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist")
    
    if platform_name == "windows":
        return os.path.join(base_dir, "vpnclient-windows.exe")
    elif platform_name == "macos":
        return os.path.join(base_dir, "vpnclient-macos")
    elif platform_name == "linux":
        return os.path.join(base_dir, "vpnclient-linux")
    else:
        raise ValueError(f"Unsupported platform: {platform_name}")


def test_executable_exists() -> bool:
    """Test if the executable exists.
    
    Returns:
        bool: True if the executable exists, False otherwise
    """
    executable_path = get_executable_path()
    exists = os.path.exists(executable_path)
    
    if exists:
        print(f"✅ Executable found at: {executable_path}")
    else:
        print(f"❌ Executable not found at: {executable_path}")
        print("   Run 'python build.py' to build the executable first.")
    
    return exists


def test_executable_runs() -> bool:
    """Test if the executable runs without errors.
    
    Returns:
        bool: True if the executable runs without errors, False otherwise
    """
    executable_path = get_executable_path()
    
    if not os.path.exists(executable_path):
        return False
    
    print(f"Running executable: {executable_path} --version")
    try:
        # Run with --version flag (assuming it's implemented)
        result = subprocess.run(
            [executable_path, "--version"], 
            capture_output=True, 
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            print(f"✅ Executable runs successfully")
            print(f"   Output: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ Executable returned error code: {result.returncode}")
            print(f"   Error: {result.stderr.strip()}")
            return False
    except subprocess.TimeoutExpired:
        print("❌ Executable timed out")
        return False
    except Exception as e:
        print(f"❌ Error running executable: {e}")
        return False


def test_platform_detection() -> bool:
    """Test if the executable correctly detects the platform.
    
    Returns:
        bool: True if platform detection works, False otherwise
    """
    executable_path = get_executable_path()
    
    if not os.path.exists(executable_path):
        return False
    
    print(f"Testing platform detection...")
    try:
        # Run with --platform flag (assuming it's implemented)
        result = subprocess.run(
            [executable_path, "--platform"], 
            capture_output=True, 
            text=True,
            timeout=5
        )
        
        expected_platform = get_platform()
        if result.returncode == 0 and expected_platform in result.stdout.lower():
            print(f"✅ Platform detection works correctly")
            print(f"   Detected platform: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ Platform detection failed or returned unexpected result")
            print(f"   Output: {result.stdout.strip()}")
            print(f"   Error: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"❌ Error testing platform detection: {e}")
        return False


def run_all_tests() -> bool:
    """Run all tests.
    
    Returns:
        bool: True if all tests pass, False otherwise
    """
    tests = [
        ("Executable exists", test_executable_exists),
        ("Executable runs", test_executable_runs),
        ("Platform detection", test_platform_detection),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n=== Testing: {test_name} ===")
        result = test_func()
        results.append(result)
        if not result:
            print(f"Test failed: {test_name}")
    
    success_count = sum(1 for r in results if r)
    print(f"\n=== Test Summary: {success_count}/{len(tests)} tests passed ===")
    
    return all(results)


def main():
    """Main entry point for the test script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test VPN Client executable")
    parser.add_argument(
        "--test", 
        choices=["exists", "runs", "platform", "all"], 
        default="all",
        help="Specific test to run"
    )
    
    args = parser.parse_args()
    
    if args.test == "exists":
        test_executable_exists()
    elif args.test == "runs":
        test_executable_runs()
    elif args.test == "platform":
        test_platform_detection()
    else:  # all
        run_all_tests()


if __name__ == "__main__":
    main()