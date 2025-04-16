# Building Standalone Executables for VPN Client

This document provides instructions for building standalone executables of the VPN client application for different platforms (Windows, macOS, and Linux) without requiring users to install any dependencies.

## Prerequisites

To build the standalone executables, you need:

- Python 3.6 or higher
- pip (Python package manager)

All other dependencies will be automatically installed by the build script.

## Building the Executables

### Quick Start

To build an executable for your current platform:

```bash
python build.py
```

The executable will be created in the `dist` directory.

### Building for Specific Platforms

To build for a specific platform:

```bash
python build.py --platform windows  # Build for Windows
python build.py --platform macos    # Build for macOS
python build.py --platform linux    # Build for Linux
```

### Building for All Platforms

To build for all supported platforms:

```bash
python build.py --platform all
```

Note: Cross-platform building may not work correctly on all systems. It's recommended to build on the target platform whenever possible.

### Additional Build Options

```bash
python build.py --skip-tests  # Skip running tests before building
python build.py --skip-deps   # Skip installing dependencies
```

## Testing the Executables

After building, you can test the executables using the provided test script:

```bash
python test_executable.py
```

This will run a series of tests to verify that the executable exists, runs correctly, and properly detects the platform.

To run specific tests:

```bash
python test_executable.py --test exists    # Test if executable exists
python test_executable.py --test runs      # Test if executable runs
python test_executable.py --test platform  # Test platform detection
```

## Executable Features

The standalone executables:

- Include all necessary dependencies
- Work without requiring Python installation
- Automatically detect the platform they're running on
- Support all VPN protocols implemented in the application

## Troubleshooting

### Common Issues

1. **Missing dependencies during build**
   - Run `python build.py` without the `--skip-deps` flag to install all required dependencies

2. **Permission denied when running executable**
   - On macOS/Linux: `chmod +x dist/vpnclient-macos` or `chmod +x dist/vpnclient-linux`

3. **Antivirus blocking the executable**
   - This is a false positive. You may need to add an exception in your antivirus software.

4. **Missing protocol dependencies**
   - Some VPN protocols may require system-level dependencies that cannot be bundled. Check the console output for specific errors.

### Getting Help

If you encounter issues not covered here, please open an issue in the project repository with detailed information about the problem, including:

- Your operating system and version
- The command you ran
- Any error messages
- Steps to reproduce the issue