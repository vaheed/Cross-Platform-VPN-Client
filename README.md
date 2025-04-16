# Cross-Platform VPN Client

A modular, cross-platform VPN client application that supports multiple VPN protocols including OpenVPN, SSTP, L2TP, and PPTP. The client provides a unified interface for managing VPN connections across Windows, macOS, and Linux platforms.

## Architecture Overview

The application follows a modular architecture with clean separation of concerns:

```
├── core/                  # Core network module and interfaces
│   ├── vpn_connection.py  # Common VPN connection interface
│   ├── metrics.py         # Network metrics collection
│   └── exceptions.py      # Custom exceptions
│
├── protocols/             # Protocol-specific implementations
│   ├── openvpn/           # OpenVPN implementation
│   ├── sstp/              # SSTP implementation
│   ├── l2tp/              # L2TP implementation
│   └── pptp/              # PPTP implementation
│
├── security/              # Security-related functionality
│   └── credentials.py     # Secure credential storage
│
├── ui/                    # User interface components
│   ├── dashboard/         # Main dashboard UI
│   ├── settings/          # Settings UI
│   └── models/            # UI models (MVVM pattern)
│
└── utils/                 # Utility functions and helpers
    └── platform.py        # Platform-specific utilities
```

## Design Patterns

- **Dependency Injection**: Used for injecting dependencies into classes, making them more testable
- **Adapter Pattern**: Used for protocol-specific implementations to adapt to the common interface
- **MVVM Pattern**: Used for UI components to separate business logic from presentation
- **Factory Pattern**: Used for creating protocol-specific connections

## Key Components

### VPNConnection Interface

A common interface that all protocol implementations must adhere to, providing methods for connecting, disconnecting, and checking status.

### Protocol Adapters

Implementations of the VPNConnection interface for specific protocols, using appropriate libraries or native APIs:
- OpenVPN: Uses OpenVPN3 Core library
- SSTP: Uses Windows RAS APIs on Windows, custom implementation on other platforms
- L2TP/PPTP: Uses native VPN services

### Metrics Module

Provides functionality for measuring and reporting network performance metrics such as latency and throughput.

### Security Module

Handles secure storage of credentials using platform-specific mechanisms:
- Windows: Windows Credential Manager
- macOS: Keychain
- Linux: Secret Service API
- Android: Android Keystore

### Dashboard UI

Displays connection status, server details, and real-time performance metrics.

## Getting Started

### Prerequisites

- Python 3.8+
- Required libraries (see requirements.txt)

### Installation

```bash
pip install -r requirements.txt
```

### Running the Application

```bash
python main.py
```

### Testing

To run the test suite:

```bash
python -m pytest -xvs
```

## Supported Platforms

The VPN client is designed to work on:

- Windows 10 and later
- macOS 10.14 and later
- Ubuntu 18.04 and later (and other major Linux distributions)

## Security Features

- End-to-end encryption for all VPN protocols
- Secure credential storage using platform-native solutions
- Kill switch to prevent data leaks if VPN connection drops
- DNS leak protection

## Standalone Executables

Standalone executables are available for Windows, macOS, and Linux platforms. These executables don't require Python or any dependencies to be installed.

### Download

You can download the latest release from the [Releases](https://github.com/username/vpnclient/releases) page.

### Building from Source

To build the standalone executables yourself:

```bash
python build.py --platform [windows|macos|linux]
```

See the [BUILD_INSTRUCTIONS.md](BUILD_INSTRUCTIONS.md) file for detailed build instructions.

## Continuous Integration/Deployment

This project uses GitHub Actions for automated testing, building, and releasing:

- **Testing**: Automated tests run on every push and pull request
- **Building**: Cross-platform executables are built automatically
- **Releasing**: New releases are automatically created when version tags are pushed

The CI/CD pipeline ensures that all code changes are tested and that executables are built for all supported platforms.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT