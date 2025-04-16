\"""Network Metrics Module.

This module provides functionality for measuring and reporting network performance metrics
such as latency and throughput for VPN connections.
"""

import time
import socket
import threading
import statistics
from typing import List, Dict, Optional, Tuple
import requests

class NetworkMetrics:
    """Class for measuring various network performance metrics."""
    
    def __init__(self, target_host: str = None):
        """Initialize the NetworkMetrics instance.
        
        Args:
            target_host: The host to use for metrics measurements. If None,
                         the currently connected VPN server will be used.
        """
        self.target_host = target_host
        self.ping_count = 10  # Default number of pings for latency test
        self.throughput_test_duration = 5  # Default duration in seconds
        self.throughput_test_url = "https://speed.cloudflare.com/__down?bytes=100000000"  # 100MB test file
        self.throughput_upload_url = "https://speed.cloudflare.com/__up"  # Upload test endpoint
    
    def set_target_host(self, host: str) -> None:
        """Set the target host for metrics measurements.
        
        Args:
            host: The hostname or IP address to use for measurements.
        """
        self.target_host = host
    
    def measure_latency(self, count: int = None) -> Optional[Dict[str, float]]:
        """Measure the latency to the target host.
        
        Args:
            count: Number of ping measurements to take. If None, uses the default.
        
        Returns:
            Optional[Dict[str, float]]: A dictionary containing latency statistics:
                - min: Minimum latency in milliseconds
                - max: Maximum latency in milliseconds
                - avg: Average latency in milliseconds
                - median: Median latency in milliseconds
                - jitter: Jitter (standard deviation) in milliseconds
            Returns None if the measurement failed.
        """
        if not self.target_host:
            return None
        
        count = count or self.ping_count
        latencies: List[float] = []
        
        for _ in range(count):
            try:
                # Create a socket connection and measure time
                start_time = time.time()
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(2.0)
                s.connect((self.target_host, 80))
                s.close()
                latency = (time.time() - start_time) * 1000  # Convert to ms
                latencies.append(latency)
                time.sleep(0.2)  # Small delay between measurements
            except (socket.timeout, socket.error):
                continue
        
        if not latencies:
            return None
        
        return {
            "min": min(latencies),
            "max": max(latencies),
            "avg": sum(latencies) / len(latencies),
            "median": statistics.median(latencies),
            "jitter": statistics.stdev(latencies) if len(latencies) > 1 else 0
        }
    
    def measure_throughput(self, duration: int = None) -> Optional[Dict[str, float]]:
        """Measure the download and upload throughput.
        
        Args:
            duration: Duration of the test in seconds. If None, uses the default.
        
        Returns:
            Optional[Dict[str, float]]: A dictionary containing throughput metrics:
                - download_speed: Download speed in Mbps
                - upload_speed: Upload speed in Mbps
            Returns None if the measurement failed.
        """
        duration = duration or self.throughput_test_duration
        
        try:
            # Measure download speed
            start_time = time.time()
            response = requests.get(self.throughput_test_url, stream=True, timeout=duration+5)
            downloaded_bytes = 0
            
            for chunk in response.iter_content(chunk_size=8192):
                if time.time() - start_time > duration:
                    break
                downloaded_bytes += len(chunk)
            
            download_time = time.time() - start_time
            download_speed = (downloaded_bytes * 8) / (download_time * 1_000_000)  # Convert to Mbps
            
            # Measure upload speed
            data = b'0' * 1_000_000  # 1MB of data
            start_time = time.time()
            uploaded_bytes = 0
            
            while time.time() - start_time < duration:
                response = requests.post(self.throughput_upload_url, data=data, timeout=5)
                if response.status_code == 200:
                    uploaded_bytes += len(data)
            
            upload_time = time.time() - start_time
            upload_speed = (uploaded_bytes * 8) / (upload_time * 1_000_000)  # Convert to Mbps
            
            return {
                "download_speed": download_speed,
                "upload_speed": upload_speed
            }
        except Exception:
            return None
    
    def continuous_monitoring(self, interval: int = 60, callback=None) -> None:
        """Start continuous monitoring of network metrics.
        
        Args:
            interval: Time between measurements in seconds.
            callback: Function to call with the metrics results.
        """
        def monitor():
            while True:
                latency = self.measure_latency(count=3)
                throughput = None
                
                # Only measure throughput every 5 intervals to reduce bandwidth usage
                if int(time.time()) % (interval * 5) < interval:
                    throughput = self.measure_throughput(duration=2)
                
                if callback and (latency or throughput):
                    callback({
                        "timestamp": time.time(),
                        "latency": latency,
                        "throughput": throughput
                    })
                
                time.sleep(interval)
        
        # Start monitoring in a background thread
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
        return thread