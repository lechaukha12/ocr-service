#!/usr/bin/env python3
"""
Final comprehensive test for enhanced OCR service
Tests all features and creates a summary report
"""

import requests
import json
import time
from datetime import datetime
import os

BASE_URL = "http://localhost:8010"
TEST_IMAGE_PATH = "/Users/lechaukha12/Desktop/ocr-service/IMG_4620.png"

def print_header(title):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print(f"{'='*60}")

def print_test_result(test_name, success, details=None):
    """Print formatted test result"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status}: {test_name}")
    if details:
        for key, value in details.items():
            print(f"   {key}: {value}")

def test_health_and_info():
    """Test basic service health and information endpoints"""
    print_header("BASIC SERVICE TESTS")
    
    results = []
    
    # Health check
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        success = response.status_code == 200
        details = {
            "Status Code": response.status_code,
            "Response": response.json() if success else response.text
        }
        print_test_result("Health Check", success, details)
        results.append(("Health Check", success))
    except Exception as e:
        print_test_result("Health Check", False, {"Error": str(e)})
        results.append(("Health Check", False))
    
    # Root endpoint
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        success = response.status_code == 200
        data = response.json() if success else {}
        details = {
            "Status Code": response.status_code,
            "Service": data.get("message", "N/A"),
            "Version": data.get("version", "N/A"),
            "Endpoints": len(data.get("endpoints", {}))
        }
        print_test_result("Root Endpoint", success, details)
        results.append(("Root Endpoint", success))
    except Exception as e:
        print_test_result("Root Endpoint", False, {"Error": str(e)})
        results.append(("Root Endpoint", False))
    
    # Languages endpoint
    try:
        response = requests.get(f"{BASE_URL}/languages", timeout=5)
        success = response.status_code == 200
        data = response.json() if success else {}
        details = {
            "Status Code": response.status_code,
            "Languages": data.get("languages", []),
            "Primary": data.get("primary", "N/A")
        }
        print_test_result("Languages Endpoint", success, details)
        results.append(("Languages Endpoint", success))
    except Exception as e:
        print_test_result("Languages Endpoint", False, {"Error": str(e)})
        results.append(("Languages Endpoint", False))
    
    return results

def test_ocr_upload():
    """Test OCR with file upload"""
    print_header("OCR FILE UPLOAD TESTS")
    
    results = []
    
    if not os.path.exists(TEST_IMAGE_PATH):
        print_test_result("OCR Upload Tests", False, {"Error": "Test image not found"})
        return [("OCR Upload Text", False), ("OCR Upload JSON", False)]
    
    # Test text format
    try:
        with open(TEST_IMAGE_PATH, 'rb') as f:
            files = {'image': f}
            data = {'format': 'text'}
            
            start_time = time.time()
            response = requests.post(f"{BASE_URL}/ocr", files=files, data=data, timeout=30)
            end_time = time.time()
        
        success = response.status_code == 200
        if success:
            result = response.json()
            details = {
                "Status Code": response.status_code,
                "Success": result.get("success", False),
                "Model": result.get("model", "N/A"),
                "Confidence": f"{result.get('confidence', 0):.4f}",
                "Processing Time": f"{result.get('processing_time', 0):.4f}s",
                "Request Time": f"{end_time - start_time:.4f}s",
                "Text Length": len(result.get("text", "")),
                "Has Text Blocks": result.get("text_blocks") is not None
            }
            print_test_result("OCR Upload (Text Format)", success, details)
        else:
            print_test_result("OCR Upload (Text Format)", False, {"Error": response.text})
        results.append(("OCR Upload Text", success))
    except Exception as e:
        print_test_result("OCR Upload (Text Format)", False, {"Error": str(e)})
        results.append(("OCR Upload Text", False))
    
    # Test JSON format
    try:
        with open(TEST_IMAGE_PATH, 'rb') as f:
            files = {'image': f}
            data = {'format': 'json'}
            
            start_time = time.time()
            response = requests.post(f"{BASE_URL}/ocr", files=files, data=data, timeout=30)
            end_time = time.time()
        
        success = response.status_code == 200
        if success:
            result = response.json()
            text_blocks = result.get("text_blocks", [])
            details = {
                "Status Code": response.status_code,
                "Success": result.get("success", False),
                "Model": result.get("model", "N/A"),
                "Confidence": f"{result.get('confidence', 0):.4f}",
                "Processing Time": f"{result.get('processing_time', 0):.4f}s",
                "Request Time": f"{end_time - start_time:.4f}s",
                "Text Blocks Count": len(text_blocks),
                "Has Bounding Boxes": len(text_blocks) > 0 and 'bbox' in text_blocks[0]
            }
            print_test_result("OCR Upload (JSON Format)", success, details)
        else:
            print_test_result("OCR Upload (JSON Format)", False, {"Error": response.text})
        results.append(("OCR Upload JSON", success))
    except Exception as e:
        print_test_result("OCR Upload (JSON Format)", False, {"Error": str(e)})
        results.append(("OCR Upload JSON", False))
    
    return results

def test_ocr_url():
    """Test OCR with URL"""
    print_header("OCR URL TESTS")
    
    results = []
    
    # Test URLs to try
    test_urls = [
        ("HTTPBin PNG", "https://httpbin.org/image/png"),
        ("HTTPBin JPEG", "https://httpbin.org/image/jpeg"),
    ]
    
    for test_name, test_url in test_urls:
        # Text format
        try:
            payload = {"url": test_url, "format": "text"}
            start_time = time.time()
            response = requests.post(f"{BASE_URL}/ocr/url", json=payload, timeout=30)
            end_time = time.time()
            
            success = response.status_code == 200
            if success:
                result = response.json()
                details = {
                    "URL": test_url,
                    "Status Code": response.status_code,
                    "Success": result.get("success", False),
                    "Confidence": f"{result.get('confidence', 0):.4f}",
                    "Processing Time": f"{result.get('processing_time', 0):.4f}s",
                    "Request Time": f"{end_time - start_time:.4f}s",
                    "Text": result.get("text", "")[:50] + "..." if len(result.get("text", "")) > 50 else result.get("text", "")
                }
                print_test_result(f"OCR URL {test_name} (Text)", success, details)
            else:
                print_test_result(f"OCR URL {test_name} (Text)", False, {"Error": response.text})
            results.append((f"OCR URL {test_name} Text", success))
        except Exception as e:
            print_test_result(f"OCR URL {test_name} (Text)", False, {"Error": str(e)})
            results.append((f"OCR URL {test_name} Text", False))
        
        # JSON format
        try:
            payload = {"url": test_url, "format": "json"}
            start_time = time.time()
            response = requests.post(f"{BASE_URL}/ocr/url", json=payload, timeout=30)
            end_time = time.time()
            
            success = response.status_code == 200
            if success:
                result = response.json()
                text_blocks = result.get("text_blocks", [])
                details = {
                    "URL": test_url,
                    "Status Code": response.status_code,
                    "Success": result.get("success", False),
                    "Confidence": f"{result.get('confidence', 0):.4f}",
                    "Processing Time": f"{result.get('processing_time', 0):.4f}s",
                    "Request Time": f"{end_time - start_time:.4f}s",
                    "Text Blocks": len(text_blocks)
                }
                print_test_result(f"OCR URL {test_name} (JSON)", success, details)
            else:
                print_test_result(f"OCR URL {test_name} (JSON)", False, {"Error": response.text})
            results.append((f"OCR URL {test_name} JSON", success))
        except Exception as e:
            print_test_result(f"OCR URL {test_name} (JSON)", False, {"Error": str(e)})
            results.append((f"OCR URL {test_name} JSON", False))
    
    return results

def test_error_handling():
    """Test error handling scenarios"""
    print_header("ERROR HANDLING TESTS")
    
    results = []
    
    # Test invalid URL
    try:
        payload = {"url": "https://invalid-url-that-definitely-does-not-exist.com/image.png", "format": "text"}
        response = requests.post(f"{BASE_URL}/ocr/url", json=payload, timeout=10)
        
        # We expect this to fail gracefully
        success = response.status_code in [400, 422, 500]  # Any reasonable error code
        details = {
            "Status Code": response.status_code,
            "Expected": "400/422/500 (Error)",
            "Response": response.json() if response.status_code == 200 else "Error response (expected)"
        }
        print_test_result("Invalid URL Handling", success, details)
        results.append(("Invalid URL Handling", success))
    except Exception as e:
        print_test_result("Invalid URL Handling", False, {"Error": str(e)})
        results.append(("Invalid URL Handling", False))
    
    # Test non-image URL
    try:
        payload = {"url": "https://httpbin.org/get", "format": "text"}
        response = requests.post(f"{BASE_URL}/ocr/url", json=payload, timeout=10)
        
        # We expect this to fail gracefully
        success = response.status_code in [400, 422] or (response.status_code == 200 and not response.json().get("success", True))
        details = {
            "Status Code": response.status_code,
            "Expected": "400/422 or success=false",
            "Response": response.json() if response.status_code == 200 else "Error response"
        }
        print_test_result("Non-Image URL Handling", success, details)
        results.append(("Non-Image URL Handling", success))
    except Exception as e:
        print_test_result("Non-Image URL Handling", False, {"Error": str(e)})
        results.append(("Non-Image URL Handling", False))
    
    return results

def generate_summary_report(all_results):
    """Generate final summary report"""
    print_header("FINAL SUMMARY REPORT")
    
    total_tests = len(all_results)
    passed_tests = sum(1 for _, success in all_results if success)
    failed_tests = total_tests - passed_tests
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print(f"📊 TEST EXECUTION SUMMARY")
    print(f"   Total Tests: {total_tests}")
    print(f"   ✅ Passed: {passed_tests}")
    print(f"   ❌ Failed: {failed_tests}")
    print(f"   📈 Success Rate: {success_rate:.1f}%")
    
    print(f"\n📋 DETAILED RESULTS:")
    for test_name, success in all_results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status}: {test_name}")
    
    print(f"\n🎯 FEATURE VALIDATION:")
    features = {
        "Health Check": any("Health" in name for name, success in all_results if success),
        "Service Info": any("Root" in name or "Languages" in name for name, success in all_results if success),
        "File Upload OCR": any("Upload" in name for name, success in all_results if success),
        "URL-based OCR": any("URL" in name for name, success in all_results if success),
        "Text Format": any("Text" in name for name, success in all_results if success),
        "JSON Format": any("JSON" in name for name, success in all_results if success),
        "Error Handling": any("Handling" in name for name, success in all_results if success),
    }
    
    for feature, working in features.items():
        status = "✅ WORKING" if working else "❌ NOT WORKING"
        print(f"   {status}: {feature}")
    
    print(f"\n📝 REPORT GENERATED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if success_rate >= 80:
        print(f"\n🎉 EXCELLENT! Enhanced OCR service is working very well!")
    elif success_rate >= 60:
        print(f"\n👍 GOOD! Enhanced OCR service is working with minor issues.")
    else:
        print(f"\n⚠️  NEEDS IMPROVEMENT! Several features need attention.")
    
    return success_rate

def main():
    """Run comprehensive test suite"""
    print_header("ENHANCED OCR SERVICE - COMPREHENSIVE TEST SUITE")
    print(f"🚀 Starting tests at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔗 Testing service at: {BASE_URL}")
    print(f"📁 Test image: {TEST_IMAGE_PATH}")
    
    all_results = []
    
    # Run all test suites
    all_results.extend(test_health_and_info())
    all_results.extend(test_ocr_upload())
    all_results.extend(test_ocr_url())
    all_results.extend(test_error_handling())
    
    # Generate final report
    success_rate = generate_summary_report(all_results)
    
    return success_rate >= 80

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)