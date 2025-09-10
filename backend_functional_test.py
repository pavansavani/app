#!/usr/bin/env python3
"""
Additional functional tests for RemindSave Backend API
Tests specific functionality and edge cases
"""

import requests
import json

BACKEND_URL = "https://remindsave.preview.emergentagent.com/api"

def test_cors_headers():
    """Test CORS configuration"""
    print("\n=== Testing CORS Configuration ===")
    try:
        response = requests.options(f"{BACKEND_URL}/auth/me", 
                                  headers={"Origin": "https://remindsave.preview.emergentagent.com"})
        
        cors_headers = [
            "Access-Control-Allow-Origin",
            "Access-Control-Allow-Methods", 
            "Access-Control-Allow-Headers",
            "Access-Control-Allow-Credentials"
        ]
        
        found_headers = []
        for header in cors_headers:
            if header in response.headers:
                found_headers.append(header)
        
        print(f"✅ CORS headers found: {len(found_headers)}/{len(cors_headers)}")
        print(f"   Headers: {found_headers}")
        
    except Exception as e:
        print(f"❌ CORS test failed: {str(e)}")

def test_api_documentation():
    """Test if FastAPI auto-generated docs are accessible"""
    print("\n=== Testing API Documentation ===")
    try:
        # Test OpenAPI schema
        response = requests.get(f"{BACKEND_URL.replace('/api', '')}/openapi.json")
        if response.status_code == 200:
            print("✅ OpenAPI schema accessible")
            schema = response.json()
            if "paths" in schema:
                print(f"   Found {len(schema['paths'])} API endpoints in schema")
        else:
            print(f"❌ OpenAPI schema not accessible: {response.status_code}")
            
    except Exception as e:
        print(f"❌ API documentation test failed: {str(e)}")

def test_error_handling():
    """Test error handling for various scenarios"""
    print("\n=== Testing Error Handling ===")
    
    # Test invalid JSON
    try:
        response = requests.post(f"{BACKEND_URL}/auth/session", 
                               data="invalid json",
                               headers={"Content-Type": "application/json"})
        if response.status_code == 422:
            print("✅ Invalid JSON properly handled")
        else:
            print(f"❌ Invalid JSON handling: expected 422, got {response.status_code}")
    except Exception as e:
        print(f"❌ Invalid JSON test failed: {str(e)}")
    
    # Test missing required fields
    try:
        response = requests.post(f"{BACKEND_URL}/websites", json={})
        if response.status_code in [401, 422]:  # 401 for auth, 422 for validation
            print("✅ Missing required fields properly handled")
        else:
            print(f"❌ Missing fields handling: expected 401/422, got {response.status_code}")
    except Exception as e:
        print(f"❌ Missing fields test failed: {str(e)}")

def test_database_connection():
    """Test if database connection is working"""
    print("\n=== Testing Database Connection ===")
    
    # Since we can't directly test DB without auth, we'll test if the server
    # starts properly (which requires DB connection)
    try:
        response = requests.get(f"{BACKEND_URL}/auth/me")
        # If we get 401, it means the server is running and DB connection is working
        # If we get 500, it might indicate DB connection issues
        if response.status_code == 401:
            print("✅ Database connection appears to be working")
        elif response.status_code == 500:
            print("❌ Possible database connection issue (500 error)")
        else:
            print(f"✅ Server responding (status: {response.status_code})")
    except Exception as e:
        print(f"❌ Database connection test failed: {str(e)}")

def test_request_validation():
    """Test request validation for different endpoints"""
    print("\n=== Testing Request Validation ===")
    
    test_cases = [
        {
            "endpoint": "/auth/session",
            "method": "POST",
            "data": {"session_id": ""},  # Empty session_id
            "expected": [400, 422]
        },
        {
            "endpoint": "/auth/set-app-lock", 
            "method": "POST",
            "data": {"password": ""},  # Empty password
            "expected": [401, 422]  # 401 for auth, 422 for validation
        }
    ]
    
    for test_case in test_cases:
        try:
            if test_case["method"] == "POST":
                response = requests.post(f"{BACKEND_URL}{test_case['endpoint']}", 
                                       json=test_case["data"])
            
            if response.status_code in test_case["expected"]:
                print(f"✅ Validation for {test_case['endpoint']} working correctly")
            else:
                print(f"❌ Validation for {test_case['endpoint']}: expected {test_case['expected']}, got {response.status_code}")
                
        except Exception as e:
            print(f"❌ Validation test for {test_case['endpoint']} failed: {str(e)}")

def test_http_methods():
    """Test that endpoints respond to correct HTTP methods"""
    print("\n=== Testing HTTP Methods ===")
    
    method_tests = [
        {"endpoint": "/auth/session", "method": "POST", "should_work": True},
        {"endpoint": "/auth/session", "method": "GET", "should_work": False},
        {"endpoint": "/auth/me", "method": "GET", "should_work": True},
        {"endpoint": "/auth/me", "method": "POST", "should_work": False},
        {"endpoint": "/websites", "method": "GET", "should_work": True},
        {"endpoint": "/websites", "method": "POST", "should_work": True},
        {"endpoint": "/websites", "method": "DELETE", "should_work": False},  # Needs ID
    ]
    
    for test in method_tests:
        try:
            if test["method"] == "GET":
                response = requests.get(f"{BACKEND_URL}{test['endpoint']}")
            elif test["method"] == "POST":
                response = requests.post(f"{BACKEND_URL}{test['endpoint']}", json={})
            elif test["method"] == "DELETE":
                response = requests.delete(f"{BACKEND_URL}{test['endpoint']}")
            
            if test["should_work"]:
                # Should not return 405 (Method Not Allowed)
                if response.status_code != 405:
                    print(f"✅ {test['method']} {test['endpoint']} - method allowed")
                else:
                    print(f"❌ {test['method']} {test['endpoint']} - method not allowed")
            else:
                # Should return 405 (Method Not Allowed)
                if response.status_code == 405:
                    print(f"✅ {test['method']} {test['endpoint']} - correctly rejected")
                else:
                    print(f"❌ {test['method']} {test['endpoint']} - should be rejected but got {response.status_code}")
                    
        except Exception as e:
            print(f"❌ HTTP method test failed for {test['method']} {test['endpoint']}: {str(e)}")

def run_functional_tests():
    """Run all functional tests"""
    print("🔧 Starting RemindSave Backend Functional Tests")
    print("=" * 60)
    
    test_cors_headers()
    test_api_documentation()
    test_error_handling()
    test_database_connection()
    test_request_validation()
    test_http_methods()
    
    print("\n" + "=" * 60)
    print("🔧 Functional Tests Complete")

if __name__ == "__main__":
    run_functional_tests()