"""Quick test script for Flask app"""
import requests
import json
import time
import sys

API_URL = "http://localhost:5000"

def test_endpoint(name, method="GET", endpoint="", data=None):
    """Test an endpoint"""
    try:
        url = f"{API_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url, timeout=5)
        else:
            response = requests.post(url, json=data, timeout=5)
        
        print(f"\n[{name}]")
        print(f"  Status: {response.status_code}")
        try:
            result = response.json()
            print(f"  Response: {json.dumps(result, indent=2)[:200]}...")
        except:
            print(f"  Response: {response.text[:200]}")
        return response.status_code == 200 or response.status_code == 503
    except requests.exceptions.ConnectionError:
        print(f"\n[{name}]")
        print("  ERROR: Could not connect to Flask app. Is it running?")
        print("  Start it with: python app.py")
        return False
    except Exception as e:
        print(f"\n[{name}]")
        print(f"  ERROR: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Trifecta AI Agent - Quick Test")
    print("=" * 50)
    print("\nMake sure Flask app is running: python app.py")
    print("Waiting 2 seconds for connection...")
    time.sleep(2)
    
    # Test 1: Root endpoint
    test_endpoint("Root Endpoint", "GET", "/")
    
    # Test 2: Health check
    test_endpoint("Health Check", "GET", "/health")
    
    # Test 3: Skills list
    test_endpoint("List Skills", "GET", "/api/skills")
    
    # Test 4: Chat endpoint (will fail without API key, but should return proper error)
    test_endpoint("Chat Endpoint", "POST", "/api/chat", {"message": "Hello"})
    
    # Test 5: Invalid JSON test
    try:
        response = requests.post(f"{API_URL}/api/chat", data="not json", headers={"Content-Type": "application/json"}, timeout=5)
        print(f"\n[Invalid JSON Test]")
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.json()}")
    except Exception as e:
        print(f"\n[Invalid JSON Test]")
        print(f"  ERROR: {e}")
    
    print("\n" + "=" * 50)
    print("Test Complete")
    print("=" * 50)
