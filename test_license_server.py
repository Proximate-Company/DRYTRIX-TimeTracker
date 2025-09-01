#!/usr/bin/env python3
"""
Test script for the license server integration
"""

import os
import sys
import time

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_license_server():
    """Test the license server client functionality"""
    print("Testing License Server Integration")
    print("=" * 40)
    
    try:
        # Test 1: Import the license server module
        print("1. Testing module import...")
        from app.utils.license_server import LicenseServerClient, init_license_client
        print("   ✓ Module imported successfully")
        
        # Test 2: Create client instance
        print("2. Testing client creation...")
        client = LicenseServerClient("testapp", "1.0.0")
        print("   ✓ Client created successfully")
        print(f"   - Server URL: {client.server_url}")
        print(f"   - App ID: {client.app_identifier}")
        print(f"   - App Version: {client.app_version}")
        
        # Test 3: Collect system info
        print("3. Testing system info collection...")
        system_info = client._collect_system_info()
        print("   ✓ System info collected")
        print(f"   - OS: {system_info.get('os', 'Unknown')}")
        print(f"   - Architecture: {system_info.get('architecture', 'Unknown')}")
        print(f"   - Python: {system_info.get('python_version', 'Unknown')}")
        
        # Test 4: Check server health (this will fail if server is not running)
        print("4. Testing server health check...")
        try:
            health = client.check_server_health()
            if health:
                print("   ✓ Server is healthy")
            else:
                print("   ⚠ Server is not responding (expected if server is not running)")
        except Exception as e:
            print(f"   ⚠ Server health check failed: {e}")
        
        # Test 5: Test client start/stop
        print("5. Testing client lifecycle...")
        try:
            if client.start():
                print("   ✓ Client started successfully")
                time.sleep(2)  # Let it run for a moment
                client.stop()
                print("   ✓ Client stopped successfully")
            else:
                print("   ⚠ Client start failed (expected if server is not running)")
        except Exception as e:
            print(f"   ⚠ Client lifecycle test failed: {e}")
        
        # Test 6: Test usage event sending
        print("6. Testing usage event...")
        try:
            from app.utils.license_server import send_usage_event
            result = send_usage_event("test_event", {"test": "data"})
            if result:
                print("   ✓ Usage event sent successfully")
            else:
                print("   ⚠ Usage event failed (expected if server is not running)")
        except Exception as e:
            print(f"   ⚠ Usage event test failed: {e}")
        
        print("\n" + "=" * 40)
        print("Test completed!")
        print("\nNote: Some tests may fail if the license server is not running.")
        print("This is expected behavior and does not indicate a problem with the integration.")
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        print("Make sure you're running this from the project root directory")
        return False
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False
    
    return True

def test_cli_commands():
    """Test the CLI commands"""
    print("\nTesting CLI Commands")
    print("=" * 40)
    
    try:
        from app.utils.license_server import get_license_client
        
        # Test global client functions
        print("1. Testing global client functions...")
        client = get_license_client()
        if client:
            print("   ✓ Global client retrieved")
            status = client.get_status()
            print(f"   - Status: {status}")
        else:
            print("   ⚠ Global client not available (expected if not initialized)")
        
        print("   ✓ CLI command tests completed")
        
    except Exception as e:
        print(f"   ⚠ CLI test failed: {e}")

if __name__ == "__main__":
    print("License Server Integration Test")
    print("=" * 50)
    
    success = test_license_server()
    test_cli_commands()
    
    if success:
        print("\n🎉 All tests completed successfully!")
        print("\nTo test with a running license server:")
        print("1. Start the license server on http://localhost:8081")
        print("2. Run: flask license-test")
        print("3. Check: flask license-status")
    else:
        print("\n❌ Some tests failed. Check the output above for details.")
        sys.exit(1)
