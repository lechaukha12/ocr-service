#!/usr/bin/env python3
"""
Test script for VLM Core service
"""
import requests
import json
import sys

def test_health():
    """Test health endpoint"""
    print("Testing health endpoint...")
    try:
        response = requests.get("http://localhost:8010/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_languages():
    """Test languages endpoint"""
    print("\nTesting languages endpoint...")
    try:
        response = requests.get("http://localhost:8010/languages")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_ocr():
    """Test OCR endpoint"""
    print("\nTesting OCR endpoint...")
    try:
        files = {"image": open("IMG_4620.png", "rb")}
        data = {"language": "vie"}
        response = requests.post("http://localhost:8010/ocr", files=files, data=data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 50)
    print("VLM Core Service Test Suite")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health),
        ("Languages", test_languages),
        ("OCR", test_ocr)
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n{'-' * 30}")
        result = test_func()
        results.append((name, result))
        print(f"{name}: {'PASS' if result else 'FAIL'}")
    
    print(f"\n{'=' * 50}")
    print("Test Results Summary:")
    print("=" * 50)
    for name, result in results:
        print(f"{name}: {'PASS' if result else 'FAIL'}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("All tests passed! ✓")
        sys.exit(0)
    else:
        print("Some tests failed! ✗")
        sys.exit(1)

if __name__ == "__main__":
    main()
