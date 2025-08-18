#!/usr/bin/env python3
"""
Test script for the Sample OpenRouter Backend API endpoints.
This script helps verify that the application is working correctly.
"""

import requests
import json
import sys
import os
from datetime import datetime

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

BASE_URL = "http://localhost:8000"


def test_health_check():
    """Test the health check endpoint."""
    print("🔍 Testing health check endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ Health check failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {str(e)}")
        return False


def test_root_endpoint():
    """Test the root endpoint."""
    print("\n🔍 Testing root endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/", timeout=10)
        if response.status_code == 200:
            print("✅ Root endpoint passed")
            data = response.json()
            print(f"   Service: {data.get('service')}")
            print(f"   Version: {data.get('version')}")
            print(f"   Available endpoints: {list(data.get('endpoints', {}).keys())}")
            return True
        else:
            print(f"❌ Root endpoint failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Root endpoint error: {str(e)}")
        return False


def test_token_generation():
    """Test token generation endpoint."""
    print("\n🔍 Testing token generation...")
    
    try:
        # Test with a sample user ID
        user_id = "test_user"
        response = requests.post(f"{BASE_URL}/auth/token", params={"user_id": user_id}, timeout=10)
        
        if response.status_code == 200:
            print("✅ Token generation passed")
            data = response.json()
            print(f"   Token type: {data.get('token_type')}")
            print(f"   Expires in: {data.get('expires_in')} seconds")
            return data.get('access_token')
        else:
            print(f"❌ Token generation failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Token generation error: {str(e)}")
        return None


def test_authenticated_endpoints(token):
    """Test endpoints that require authentication."""
    if not token:
        print("\n⚠️  Skipping authenticated endpoint tests (no token)")
        return False
    
    print(f"\n🔍 Testing authenticated endpoints with token...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test prompts endpoint
    print("   Testing /prompts endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/prompts", headers=headers, timeout=10)
        if response.status_code == 200:
            print("   ✅ /prompts endpoint passed")
            data = response.json()
            print(f"      Available prompts: {list(data.get('prompts', {}).keys())}")
        else:
            print(f"   ❌ /prompts endpoint failed with status {response.status_code}")
    except Exception as e:
        print(f"   ❌ /prompts endpoint error: {str(e)}")
    
    # Test models endpoint
    print("   Testing /models endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/models", headers=headers, timeout=10)
        if response.status_code == 200:
            print("   ✅ /models endpoint passed")
            data = response.json()
            print(f"      Available models: {data.get('models', [])}")
        else:
            print(f"   ❌ /models endpoint failed with status {response.status_code}")
    except Exception as e:
        print(f"   ❌ /models endpoint error: {str(e)}")
    
    return True


def test_llm_endpoint(token):
    """Test the main LLM endpoint."""
    if not token:
        print("\n⚠️  Skipping LLM endpoint test (no token)")
        return False
    
    print(f"\n🔍 Testing LLM endpoint...")
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # Test with a simple prompt
    test_data = {
        "prompt_text": "What is 2 + 2? Please provide a simple answer."
    }
    
    try:
        response = requests.post(f"{BASE_URL}/ask-llm", headers=headers, json=test_data, timeout=60)
        
        if response.status_code == 200:
            print("✅ LLM endpoint passed")
            data = response.json()
            print(f"   Success: {data.get('success')}")
            print(f"   Model used: {data.get('model_used')}")
            print(f"   Request ID: {data.get('request_id')}")
            if data.get('tokens_used'):
                print(f"   Tokens used: {data.get('tokens_used')}")
            print(f"   Response: {data.get('response', '')[:100]}...")
            return True
        else:
            print(f"❌ LLM endpoint failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ LLM endpoint error: {str(e)}")
        return False


def main():
    """Main test function."""
    print("🚀 Starting Sample OpenRouter Backend API Tests")
    print("=" * 50)
    print(f"Base URL: {BASE_URL}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # Check if service is running
    print("\n🔍 Checking if service is running...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Service is running")
        else:
            print("❌ Service is not responding correctly")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to service. Make sure it's running on http://localhost:8000")
        print("   Start the service with: python app/main.py")
        return
    except Exception as e:
        print(f"❌ Error checking service: {str(e)}")
        return
    
    # Run tests
    tests_passed = 0
    total_tests = 5
    
    if test_health_check():
        tests_passed += 1
    
    if test_root_endpoint():
        tests_passed += 1
    
    token = test_token_generation()
    if token:
        tests_passed += 1
    
    if test_authenticated_endpoints(token):
        tests_passed += 1
    
    if test_llm_endpoint(token):
        tests_passed += 1
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary")
    print("=" * 50)
    print(f"Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! The service is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    print("\n💡 Next steps:")
    print("1. Visit http://localhost:8000/docs for interactive API documentation")
    print("2. Use the token above to make authenticated requests")
    print("3. Test with different prompt templates and models")


if __name__ == "__main__":
    main()
