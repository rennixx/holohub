"""
Test Device Client Simulator

Quick test of device connection and heartbeat.
"""
import os
import sys
from pathlib import Path

# Add device client to path
sys.path.insert(0, str(Path(__file__).parent))

# Import after adding to path
from src.api_client import DeviceAPIClient


def test_device_connection():
    """Test device authentication and heartbeat."""

    # Use the device we registered earlier
    API_URL = "http://localhost:8000"
    HARDWARE_ID = "HP-CONN-002"
    DEVICE_SECRET = "qEhczlnzHb3DwJWn0B3gsBm6t0IpOquZfjHulxfhBS0"

    print("=" * 60)
    print("Testing HoloHub Device Client Simulator")
    print("=" * 60)
    print(f"API URL: {API_URL}")
    print(f"Hardware ID: {HARDWARE_ID}")
    print("=" * 60)

    # Create API client
    client = DeviceAPIClient(
        api_base_url=API_URL,
        hardware_id=HARDWARE_ID,
        device_secret=DEVICE_SECRET,
    )

    try:
        # Test 1: Authentication
        print("\n[1/3] Testing authentication...")
        token = client.authenticate()
        print(f"[OK] Authenticated successfully!")
        print(f"  Device ID: {token.device_id}")
        print(f"  Token expires in: {token.expires_in}s")
        print(f"  Organization ID: {token.organization_id}")

        # Test 2: Send heartbeat
        print("\n[2/2] Sending heartbeat...")
        response = client.send_heartbeat(
            cpu_percent=25.5,
            memory_percent=45.2,
            temperature_celsius=42,
            firmware_version="1.0.0",
            client_version="1.0.0",
        )
        print(f"[OK] Heartbeat sent!")
        print(f"  Status: {response['status']}")
        print(f"  Message: {response['message']}")

        print("\n" + "=" * 60)
        print("All tests passed! Device simulator is working.")
        print("=" * 60)

    except Exception as e:
        print(f"\n[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        client.close()


if __name__ == "__main__":
    test_device_connection()
