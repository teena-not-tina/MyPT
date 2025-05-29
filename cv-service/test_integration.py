# test_integration.py
# Run this script to test if your exercise analyzer is working properly

import requests
import json
import sys

BASE_URL = "http://localhost:8001"

def test_endpoints():
    """Test all exercise analyzer endpoints"""
    
    print("Testing Exercise Analyzer Integration...")
    print("=" * 50)
    
    # Test 1: Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print("❌ Server health check failed")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to server at {BASE_URL}")
        print(f"   Error: {e}")
        print("\n   Make sure the server is running: python main.py")
        return False
    
    # Test 2: Check pose endpoint
    try:
        response = requests.get(f"{BASE_URL}/api/pose")
        if response.status_code == 200:
            data = response.json()
            print("✅ Pose endpoint is working")
            print(f"   Available exercises: {len(data['available_exercises'])}")
        else:
            print("❌ Pose endpoint failed")
    except Exception as e:
        print(f"❌ Pose endpoint error: {e}")
    
    # Test 3: Check exercise list endpoint
    try:
        response = requests.get(f"{BASE_URL}/exercise/exercises")
        if response.status_code == 200:
            data = response.json()
            print("✅ Exercise list endpoint is working")
            print("   Available exercises:")
            for ex in data['exercises']:
                print(f"     - {ex['name']} ({ex['id']}): {ex['description']}")
        else:
            print("❌ Exercise list endpoint failed")
    except Exception as e:
        print(f"❌ Exercise list endpoint error: {e}")
    
    # Test 4: Check WebSocket endpoint info
    print("\n📡 WebSocket endpoint for live analysis:")
    print(f"   ws://localhost:8001/exercise/live-analysis")
    
    # Test 5: Check CORS headers
    try:
        response = requests.options(f"{BASE_URL}/exercise/exercises", 
                                   headers={"Origin": "http://localhost:3000"})
        if 'access-control-allow-origin' in response.headers:
            print("\n✅ CORS is properly configured")
            print(f"   Allowed origin: {response.headers.get('access-control-allow-origin')}")
        else:
            print("\n⚠️  CORS might not be properly configured")
    except Exception as e:
        print(f"\n⚠️  Could not test CORS: {e}")
    
    print("\n" + "=" * 50)
    print("Integration test complete!")
    print("\nNext steps:")
    print("1. Make sure you have pose_landmarker_full.task in cv-service/")
    print("2. Start your React app and test the ExerciseAnalyzer component")
    print("3. Check the browser console for any errors")
    
    return True

if __name__ == "__main__":
    success = test_endpoints()
    sys.exit(0 if success else 1)