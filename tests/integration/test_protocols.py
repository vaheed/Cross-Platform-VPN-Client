import pytest
from core.vpn_connection import VPNConnection
from protocols.openvpn.openvpn_connection import OpenVPNConnection
from protocols.sstp.sstp_connection import SSTPConnection
from protocols.l2tp.l2tp_connection import L2TPConnection
from protocols.pptp.pptp_connection import PPTPConnection

@pytest.mark.parametrize("protocol_class,config", [
    (OpenVPNConnection, {'config_file': 'client.ovpn'}),
    (SSTPConnection, {'server': 'vpn.example.com', 'username': 'test'}),
    (L2TPConnection, {'server': 'vpn.example.com', 'psk': 'secret'}),
    (PPTPConnection, {'server': 'vpn.example.com', 'username': 'test', 'password': 'pass'})
])
def test_protocol_connections(protocol_class, config):
    conn = protocol_class(config)
    assert isinstance(conn, VPNConnection)
    
    # Test configuration validation
    with pytest.raises(ValueError):
        invalid_config = config.copy()
        invalid_config.pop(next(iter(config)))
        protocol_class(invalid_config)

    # Test connection lifecycle
    try:
        conn.connect()
        assert conn.status()['connected'] is True
    finally:
        conn.disconnect()
        assert conn.status()['connected'] is False

@pytest.mark.parametrize("protocol_class", [SSTPConnection, L2TPConnection, PPTPConnection])
def test_platform_support(protocol_class, monkeypatch):
    # Test Windows platform
    monkeypatch.setattr('utils.platform.is_windows', lambda: True)
    assert protocol_class({}).validate_platform()
    
    # Test macOS platform
    monkeypatch.setattr('utils.platform.is_macos', lambda: True)
    if protocol_class != PPTPConnection:
        assert protocol_class({}).validate_platform()
    
    # Test Linux platform
    monkeypatch.setattr('utils.platform.is_linux', lambda: True)
    assert protocol_class({}).validate_platform()