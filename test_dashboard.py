"""Test dashboard server"""
import requests
import time

def test_dashboard():
    print("Testing dashboard server...")
    print("=" * 50)
    
    # Test 1: Check if server is running
    try:
        response = requests.get('http://localhost:3015/', timeout=5)
        print(f"\n[Test 1] Root path (/)")
        print(f"  Status: {response.status_code}")
        print(f"  Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
        print(f"  Content length: {len(response.content)} bytes")
        if response.status_code == 200:
            print("  [OK] Dashboard is accessible!")
        else:
            print(f"  [ERROR] Unexpected status code")
    except requests.exceptions.ConnectionError:
        print("\n[Test 1] Root path (/)")
        print("  [ERROR] Cannot connect to dashboard server")
        print("  Make sure to run: python dashboard_dev.py")
        return
    except Exception as e:
        print(f"\n[Test 1] Root path (/)")
        print(f"  [ERROR] {e}")
        return
    
    # Test 2: Check dashboard_index.html directly
    try:
        response = requests.get('http://localhost:3015/dashboard_index.html', timeout=5)
        print(f"\n[Test 2] Direct file (dashboard_index.html)")
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            print("  [OK] File is accessible!")
            # Check if it contains expected content
            if 'Trifecta Dashboard' in response.text:
                print("  [OK] Contains expected content")
            else:
                print("  [WARNING] Content may be different than expected")
    except Exception as e:
        print(f"\n[Test 2] Direct file (dashboard_index.html)")
        print(f"  [ERROR] {e}")
    
    # Test 3: Check if Flask API is accessible (for dashboard to work)
    try:
        response = requests.get('http://localhost:5000/health', timeout=5)
        print(f"\n[Test 3] Flask API health check")
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            print("  [OK] Flask API is running!")
        else:
            print("  [WARNING] Flask API returned non-200 status")
    except requests.exceptions.ConnectionError:
        print("\n[Test 3] Flask API health check")
        print("  [ERROR] Flask API is not running")
        print("  Make sure to run: python app.py")
    except Exception as e:
        print(f"\n[Test 3] Flask API health check")
        print(f"  [ERROR] {e}")
    
    print("\n" + "=" * 50)
    print("Test Complete")
    print("\nTo access the dashboard:")
    print("  1. Make sure Flask API is running: python app.py")
    print("  2. Make sure dashboard server is running: python dashboard_dev.py")
    print("  3. Open browser to: http://localhost:3015/")

if __name__ == "__main__":
    test_dashboard()
