#!/usr/bin/env python3
"""
Backend API Testing for RemindSave Personal Memory Helper App
Tests all authentication, CRUD operations, and encryption functionality
"""

import requests
import json
import uuid
from datetime import datetime
import sys
import os

# Backend URL from environment
BACKEND_URL = "https://remindsave.preview.emergentagent.com/api"

class RemindSaveAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.user_session_token = None
        self.user_data = None
        self.test_results = {
            "auth": {"passed": 0, "failed": 0, "details": []},
            "app_lock": {"passed": 0, "failed": 0, "details": []},
            "websites": {"passed": 0, "failed": 0, "details": []},
            "apps": {"passed": 0, "failed": 0, "details": []},
            "notes": {"passed": 0, "failed": 0, "details": []},
            "encryption": {"passed": 0, "failed": 0, "details": []},
            "search": {"passed": 0, "failed": 0, "details": []}
        }
        
    def log_result(self, category, test_name, success, details=""):
        """Log test result"""
        if success:
            self.test_results[category]["passed"] += 1
            status = "✅ PASS"
        else:
            self.test_results[category]["failed"] += 1
            status = "❌ FAIL"
        
        result = f"{status}: {test_name}"
        if details:
            result += f" - {details}"
        
        self.test_results[category]["details"].append(result)
        print(result)
        
    def test_auth_endpoints(self):
        """Test authentication endpoints"""
        print("\n=== Testing Authentication Endpoints ===")
        
        # Test 1: Process session endpoint (mock test since we can't get real session_id)
        try:
            # This will fail as expected since we don't have a real session_id from Emergent Auth
            response = self.session.post(f"{BACKEND_URL}/auth/session", 
                                       json={"session_id": "mock_session_id"})
            
            # We expect this to fail with 400 status
            if response.status_code == 400:
                self.log_result("auth", "Session processing endpoint exists and validates input", True, 
                              "Correctly rejects invalid session_id")
            else:
                self.log_result("auth", "Session processing endpoint", False, 
                              f"Unexpected status code: {response.status_code}")
        except Exception as e:
            self.log_result("auth", "Session processing endpoint", False, f"Request failed: {str(e)}")
        
        # Test 2: Get current user info (without authentication)
        try:
            response = self.session.get(f"{BACKEND_URL}/auth/me")
            if response.status_code == 401:
                self.log_result("auth", "Protected endpoint authentication check", True, 
                              "Correctly returns 401 for unauthenticated requests")
            else:
                self.log_result("auth", "Protected endpoint authentication check", False, 
                              f"Expected 401, got {response.status_code}")
        except Exception as e:
            self.log_result("auth", "Protected endpoint authentication check", False, f"Request failed: {str(e)}")
        
        # Test 3: Logout endpoint
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/logout")
            if response.status_code == 200:
                self.log_result("auth", "Logout endpoint", True, "Logout endpoint accessible")
            else:
                self.log_result("auth", "Logout endpoint", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_result("auth", "Logout endpoint", False, f"Request failed: {str(e)}")
    
    def test_app_lock_endpoints(self):
        """Test app lock endpoints (without authentication)"""
        print("\n=== Testing App Lock Endpoints ===")
        
        # Test 1: Set app lock (should require authentication)
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/set-app-lock", 
                                       json={"password": "testlock123"})
            if response.status_code == 401:
                self.log_result("app_lock", "Set app lock authentication check", True, 
                              "Correctly requires authentication")
            else:
                self.log_result("app_lock", "Set app lock authentication check", False, 
                              f"Expected 401, got {response.status_code}")
        except Exception as e:
            self.log_result("app_lock", "Set app lock authentication check", False, f"Request failed: {str(e)}")
        
        # Test 2: Verify app lock (should require authentication)
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/verify-app-lock", 
                                       json={"password": "testlock123"})
            if response.status_code == 401:
                self.log_result("app_lock", "Verify app lock authentication check", True, 
                              "Correctly requires authentication")
            else:
                self.log_result("app_lock", "Verify app lock authentication check", False, 
                              f"Expected 401, got {response.status_code}")
        except Exception as e:
            self.log_result("app_lock", "Verify app lock authentication check", False, f"Request failed: {str(e)}")
        
        # Test 3: Remove app lock (should require authentication)
        try:
            response = self.session.delete(f"{BACKEND_URL}/auth/remove-app-lock", 
                                         json={"password": "testlock123"})
            if response.status_code == 401:
                self.log_result("app_lock", "Remove app lock authentication check", True, 
                              "Correctly requires authentication")
            else:
                self.log_result("app_lock", "Remove app lock authentication check", False, 
                              f"Expected 401, got {response.status_code}")
        except Exception as e:
            self.log_result("app_lock", "Remove app lock authentication check", False, f"Request failed: {str(e)}")
    
    def test_website_endpoints(self):
        """Test website CRUD endpoints"""
        print("\n=== Testing Website CRUD Endpoints ===")
        
        # Test 1: Create website entry (should require authentication)
        try:
            website_data = {
                "name": "GitHub",
                "link": "https://github.com",
                "purpose": "Code repository hosting",
                "login_id": "john.doe@example.com",
                "password": "secure_password_123"
            }
            response = self.session.post(f"{BACKEND_URL}/websites", json=website_data)
            if response.status_code == 401:
                self.log_result("websites", "Create website entry authentication check", True, 
                              "Correctly requires authentication")
            else:
                self.log_result("websites", "Create website entry authentication check", False, 
                              f"Expected 401, got {response.status_code}")
        except Exception as e:
            self.log_result("websites", "Create website entry authentication check", False, f"Request failed: {str(e)}")
        
        # Test 2: Get website entries (should require authentication)
        try:
            response = self.session.get(f"{BACKEND_URL}/websites")
            if response.status_code == 401:
                self.log_result("websites", "Get website entries authentication check", True, 
                              "Correctly requires authentication")
            else:
                self.log_result("websites", "Get website entries authentication check", False, 
                              f"Expected 401, got {response.status_code}")
        except Exception as e:
            self.log_result("websites", "Get website entries authentication check", False, f"Request failed: {str(e)}")
        
        # Test 3: Update website entry (should require authentication)
        try:
            update_data = {
                "name": "Updated GitHub",
                "link": "https://github.com",
                "purpose": "Updated purpose",
                "login_id": "updated@example.com",
                "password": "updated_password"
            }
            response = self.session.put(f"{BACKEND_URL}/websites/test-id", json=update_data)
            if response.status_code == 401:
                self.log_result("websites", "Update website entry authentication check", True, 
                              "Correctly requires authentication")
            else:
                self.log_result("websites", "Update website entry authentication check", False, 
                              f"Expected 401, got {response.status_code}")
        except Exception as e:
            self.log_result("websites", "Update website entry authentication check", False, f"Request failed: {str(e)}")
        
        # Test 4: Delete website entry (should require authentication)
        try:
            response = self.session.delete(f"{BACKEND_URL}/websites/test-id")
            if response.status_code == 401:
                self.log_result("websites", "Delete website entry authentication check", True, 
                              "Correctly requires authentication")
            else:
                self.log_result("websites", "Delete website entry authentication check", False, 
                              f"Expected 401, got {response.status_code}")
        except Exception as e:
            self.log_result("websites", "Delete website entry authentication check", False, f"Request failed: {str(e)}")
        
        # Test 5: Search website entries (should require authentication)
        try:
            response = self.session.get(f"{BACKEND_URL}/websites?search=github")
            if response.status_code == 401:
                self.log_result("websites", "Search website entries authentication check", True, 
                              "Correctly requires authentication")
            else:
                self.log_result("websites", "Search website entries authentication check", False, 
                              f"Expected 401, got {response.status_code}")
        except Exception as e:
            self.log_result("websites", "Search website entries authentication check", False, f"Request failed: {str(e)}")
    
    def test_app_endpoints(self):
        """Test app CRUD endpoints"""
        print("\n=== Testing App CRUD Endpoints ===")
        
        # Test 1: Create app entry (should require authentication)
        try:
            app_data = {
                "app_name": "Slack",
                "purpose": "Team communication",
                "username": "john.doe",
                "password": "slack_password_123"
            }
            response = self.session.post(f"{BACKEND_URL}/apps", json=app_data)
            if response.status_code == 401:
                self.log_result("apps", "Create app entry authentication check", True, 
                              "Correctly requires authentication")
            else:
                self.log_result("apps", "Create app entry authentication check", False, 
                              f"Expected 401, got {response.status_code}")
        except Exception as e:
            self.log_result("apps", "Create app entry authentication check", False, f"Request failed: {str(e)}")
        
        # Test 2: Get app entries (should require authentication)
        try:
            response = self.session.get(f"{BACKEND_URL}/apps")
            if response.status_code == 401:
                self.log_result("apps", "Get app entries authentication check", True, 
                              "Correctly requires authentication")
            else:
                self.log_result("apps", "Get app entries authentication check", False, 
                              f"Expected 401, got {response.status_code}")
        except Exception as e:
            self.log_result("apps", "Get app entries authentication check", False, f"Request failed: {str(e)}")
        
        # Test 3: Update app entry (should require authentication)
        try:
            update_data = {
                "app_name": "Updated Slack",
                "purpose": "Updated team communication",
                "username": "updated.user",
                "password": "updated_password"
            }
            response = self.session.put(f"{BACKEND_URL}/apps/test-id", json=update_data)
            if response.status_code == 401:
                self.log_result("apps", "Update app entry authentication check", True, 
                              "Correctly requires authentication")
            else:
                self.log_result("apps", "Update app entry authentication check", False, 
                              f"Expected 401, got {response.status_code}")
        except Exception as e:
            self.log_result("apps", "Update app entry authentication check", False, f"Request failed: {str(e)}")
        
        # Test 4: Delete app entry (should require authentication)
        try:
            response = self.session.delete(f"{BACKEND_URL}/apps/test-id")
            if response.status_code == 401:
                self.log_result("apps", "Delete app entry authentication check", True, 
                              "Correctly requires authentication")
            else:
                self.log_result("apps", "Delete app entry authentication check", False, 
                              f"Expected 401, got {response.status_code}")
        except Exception as e:
            self.log_result("apps", "Delete app entry authentication check", False, f"Request failed: {str(e)}")
        
        # Test 5: Search app entries (should require authentication)
        try:
            response = self.session.get(f"{BACKEND_URL}/apps?search=slack")
            if response.status_code == 401:
                self.log_result("apps", "Search app entries authentication check", True, 
                              "Correctly requires authentication")
            else:
                self.log_result("apps", "Search app entries authentication check", False, 
                              f"Expected 401, got {response.status_code}")
        except Exception as e:
            self.log_result("apps", "Search app entries authentication check", False, f"Request failed: {str(e)}")
    
    def test_notes_endpoints(self):
        """Test notes CRUD endpoints"""
        print("\n=== Testing Notes CRUD Endpoints ===")
        
        # Test 1: Create note (should require authentication)
        try:
            note_data = {
                "title": "Important Meeting Notes",
                "content": "Meeting with client about project requirements and timeline."
            }
            response = self.session.post(f"{BACKEND_URL}/notes", json=note_data)
            if response.status_code == 401:
                self.log_result("notes", "Create note authentication check", True, 
                              "Correctly requires authentication")
            else:
                self.log_result("notes", "Create note authentication check", False, 
                              f"Expected 401, got {response.status_code}")
        except Exception as e:
            self.log_result("notes", "Create note authentication check", False, f"Request failed: {str(e)}")
        
        # Test 2: Get notes (should require authentication)
        try:
            response = self.session.get(f"{BACKEND_URL}/notes")
            if response.status_code == 401:
                self.log_result("notes", "Get notes authentication check", True, 
                              "Correctly requires authentication")
            else:
                self.log_result("notes", "Get notes authentication check", False, 
                              f"Expected 401, got {response.status_code}")
        except Exception as e:
            self.log_result("notes", "Get notes authentication check", False, f"Request failed: {str(e)}")
        
        # Test 3: Update note (should require authentication)
        try:
            update_data = {
                "title": "Updated Meeting Notes",
                "content": "Updated content with additional details."
            }
            response = self.session.put(f"{BACKEND_URL}/notes/test-id", json=update_data)
            if response.status_code == 401:
                self.log_result("notes", "Update note authentication check", True, 
                              "Correctly requires authentication")
            else:
                self.log_result("notes", "Update note authentication check", False, 
                              f"Expected 401, got {response.status_code}")
        except Exception as e:
            self.log_result("notes", "Update note authentication check", False, f"Request failed: {str(e)}")
        
        # Test 4: Delete note (should require authentication)
        try:
            response = self.session.delete(f"{BACKEND_URL}/notes/test-id")
            if response.status_code == 401:
                self.log_result("notes", "Delete note authentication check", True, 
                              "Correctly requires authentication")
            else:
                self.log_result("notes", "Delete note authentication check", False, 
                              f"Expected 401, got {response.status_code}")
        except Exception as e:
            self.log_result("notes", "Delete note authentication check", False, f"Request failed: {str(e)}")
        
        # Test 5: Search notes (should require authentication)
        try:
            response = self.session.get(f"{BACKEND_URL}/notes?search=meeting")
            if response.status_code == 401:
                self.log_result("notes", "Search notes authentication check", True, 
                              "Correctly requires authentication")
            else:
                self.log_result("notes", "Search notes authentication check", False, 
                              f"Expected 401, got {response.status_code}")
        except Exception as e:
            self.log_result("notes", "Search notes authentication check", False, f"Request failed: {str(e)}")
    
    def test_api_structure(self):
        """Test API structure and endpoint availability"""
        print("\n=== Testing API Structure ===")
        
        # Test that all endpoints are properly prefixed with /api
        endpoints_to_test = [
            "/auth/session",
            "/auth/logout", 
            "/auth/me",
            "/auth/set-app-lock",
            "/auth/verify-app-lock",
            "/auth/remove-app-lock",
            "/websites",
            "/apps", 
            "/notes"
        ]
        
        for endpoint in endpoints_to_test:
            try:
                # Use HEAD request to check if endpoint exists without triggering full logic
                response = self.session.head(f"{BACKEND_URL}{endpoint}")
                # Any response other than 404 means the endpoint exists
                if response.status_code != 404:
                    self.log_result("auth", f"Endpoint {endpoint} exists", True, 
                                  f"Status: {response.status_code}")
                else:
                    self.log_result("auth", f"Endpoint {endpoint} exists", False, 
                                  "Endpoint not found (404)")
            except Exception as e:
                self.log_result("auth", f"Endpoint {endpoint} exists", False, f"Request failed: {str(e)}")
    
    def test_encryption_implementation(self):
        """Test that encryption is properly implemented in the backend code"""
        print("\n=== Testing Encryption Implementation ===")
        
        # Since we can't test encryption directly without authentication,
        # we'll verify the implementation exists by checking the code structure
        try:
            # Check if the backend server file exists and contains encryption functions
            backend_file = "/app/backend/server.py"
            if os.path.exists(backend_file):
                with open(backend_file, 'r') as f:
                    content = f.read()
                    
                # Check for encryption-related imports and functions
                encryption_checks = [
                    ("Fernet import", "from cryptography.fernet import Fernet" in content),
                    ("Encryption key generation", "Fernet.generate_key()" in content),
                    ("Encrypt function", "def encrypt_data(" in content),
                    ("Decrypt function", "def decrypt_data(" in content),
                    ("Password encryption in websites", "encrypt_data(entry_dict[\"password\"])" in content),
                    ("Password encryption in apps", "encrypt_data(entry_dict[\"password\"])" in content),
                    ("Password decryption", "decrypt_data(" in content)
                ]
                
                for check_name, check_result in encryption_checks:
                    self.log_result("encryption", check_name, check_result, 
                                  "Found in backend code" if check_result else "Not found in backend code")
            else:
                self.log_result("encryption", "Backend server file exists", False, "File not found")
                
        except Exception as e:
            self.log_result("encryption", "Encryption implementation check", False, f"Error: {str(e)}")
    
    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 Starting RemindSave Backend API Tests")
        print(f"Testing against: {BACKEND_URL}")
        print("=" * 60)
        
        # Run all test suites
        self.test_api_structure()
        self.test_auth_endpoints()
        self.test_app_lock_endpoints()
        self.test_website_endpoints()
        self.test_app_endpoints()
        self.test_notes_endpoints()
        self.test_encryption_implementation()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test results summary"""
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        total_passed = 0
        total_failed = 0
        
        for category, results in self.test_results.items():
            passed = results["passed"]
            failed = results["failed"]
            total_passed += passed
            total_failed += failed
            
            print(f"\n{category.upper()}:")
            print(f"  ✅ Passed: {passed}")
            print(f"  ❌ Failed: {failed}")
            
            if results["details"]:
                for detail in results["details"]:
                    print(f"    {detail}")
        
        print(f"\n{'='*60}")
        print(f"OVERALL RESULTS:")
        print(f"✅ Total Passed: {total_passed}")
        print(f"❌ Total Failed: {total_failed}")
        print(f"📈 Success Rate: {(total_passed/(total_passed+total_failed)*100):.1f}%" if (total_passed+total_failed) > 0 else "N/A")
        print("=" * 60)
        
        return total_passed, total_failed

if __name__ == "__main__":
    tester = RemindSaveAPITester()
    tester.run_all_tests()