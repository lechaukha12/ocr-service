#!/usr/bin/env python3
"""
Comprehensive test script for the enhanced OCR service
Tests all new features including URL-based OCR and format options
"""

import requests
import json
import time

BASE_URL = "http://localhost:8010"

def test_health_check():
    """Test health check endpoint"""
    print("🔍 Testing health check...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_root_endpoint():
    """Test root endpoint"""
    print("\n🔍 Testing root endpoint...")
    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Service: {data['message']}")
    print(f"Version: {data['version']}")
    print("Available endpoints:")
    for endpoint, description in data['endpoints'].items():
        print(f"  {endpoint}: {description}")
    return response.status_code == 200

def test_languages_endpoint():
    """Test languages endpoint"""
    print("\n🔍 Testing languages endpoint...")
    response = requests.get(f"{BASE_URL}/languages")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Languages: {data['languages']}")
    print(f"Primary: {data['primary']}")
    print(f"Message: {data['message']}")
    return response.status_code == 200

def test_ocr_upload_text_format():
    """Test OCR with image upload - text format"""
    print("\n🔍 Testing OCR upload with text format...")
    
    # Use a test image
    image_path = "/Users/lechaukha12/Desktop/ocr-service/IMG_4620.png"
    
    with open(image_path, 'rb') as f:
        files = {'image': f}
        data = {'format': 'text'}
        
        start_time = time.time()
        response = requests.post(f"{BASE_URL}/ocr", files=files, data=data)
        end_time = time.time()
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Success: {result['success']}")
        print(f"Model: {result['model']}")
        print(f"Confidence: {result['confidence']:.4f}")
        print(f"Processing time: {result['processing_time']:.4f}s")
        print(f"Request time: {end_time - start_time:.4f}s")
        print(f"Text length: {len(result['text'])} characters")
        print(f"Text blocks: {result['text_blocks']}")
        print(f"First 100 chars: {result['text'][:100]}...")
        return True
    else:
        print(f"Error: {response.text}")
        return False

def test_ocr_upload_json_format():
    """Test OCR with image upload - JSON format"""
    print("\n🔍 Testing OCR upload with JSON format...")
    
    image_path = "/Users/lechaukha12/Desktop/ocr-service/IMG_4620.png"
    
    with open(image_path, 'rb') as f:
        files = {'image': f}
        data = {'format': 'json'}
        
        start_time = time.time()
        response = requests.post(f"{BASE_URL}/ocr", files=files, data=data)
        end_time = time.time()
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Success: {result['success']}")
        print(f"Model: {result['model']}")
        print(f"Confidence: {result['confidence']:.4f}")
        print(f"Processing time: {result['processing_time']:.4f}s")
        print(f"Request time: {end_time - start_time:.4f}s")
        print(f"Text blocks count: {len(result['text_blocks']) if result['text_blocks'] else 0}")
        if result['text_blocks'] and len(result['text_blocks']) > 0:
            first_block = result['text_blocks'][0]
            print(f"First block: '{first_block['text']}' (confidence: {first_block['confidence']:.4f})")
            print(f"First block bbox: {first_block['bbox']}")
        return True
    else:
        print(f"Error: {response.text}")
        return False

def test_ocr_url_text_format():
    """Test OCR with URL - text format"""
    print("\n🔍 Testing OCR from URL with text format...")
    
    # Use a publicly accessible image URL
    test_url = "https://via.placeholder.com/800x400/000000/FFFFFF?text=Hello+World+Test+Image"
    
    payload = {
        "url": test_url,
        "format": "text"
    }
    
    start_time = time.time()
    response = requests.post(f"{BASE_URL}/ocr/url", json=payload)
    end_time = time.time()
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Success: {result['success']}")
        print(f"Model: {result['model']}")
        print(f"Confidence: {result['confidence']:.4f}")
        print(f"Processing time: {result['processing_time']:.4f}s")
        print(f"Request time: {end_time - start_time:.4f}s")
        print(f"Text: '{result['text']}'")
        print(f"Text blocks: {result['text_blocks']}")
        return True
    else:
        print(f"Error: {response.text}")
        return False

def test_ocr_url_json_format():
    """Test OCR with URL - JSON format"""
    print("\n🔍 Testing OCR from URL with JSON format...")
    
    test_url = "https://via.placeholder.com/800x400/000000/FFFFFF?text=JSON+Format+Test"
    
    payload = {
        "url": test_url,
        "format": "json"
    }
    
    start_time = time.time()
    response = requests.post(f"{BASE_URL}/ocr/url", json=payload)
    end_time = time.time()
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Success: {result['success']}")
        print(f"Model: {result['model']}")
        print(f"Confidence: {result['confidence']:.4f}")
        print(f"Processing time: {result['processing_time']:.4f}s")
        print(f"Request time: {end_time - start_time:.4f}s")
        print(f"Text blocks count: {len(result['text_blocks']) if result['text_blocks'] else 0}")
        return True
    else:
        print(f"Error: {response.text}")
        return False

def test_error_handling():
    """Test error handling scenarios"""
    print("\n🔍 Testing error handling...")
    
    # Test invalid URL
    print("Testing invalid URL...")
    payload = {
        "url": "https://invalid-url-that-does-not-exist.com/image.png",
        "format": "text"
    }
    response = requests.post(f"{BASE_URL}/ocr/url", json=payload)
    print(f"Invalid URL Status: {response.status_code}")
    if response.status_code == 422 or response.status_code == 400:
        print("✅ Invalid URL handled correctly")
    else:
        print(f"⚠️  Unexpected response: {response.text}")
    
    # Test non-image URL
    print("\nTesting non-image URL...")
    payload = {
        "url": "https://www.google.com",
        "format": "text"
    }
    response = requests.post(f"{BASE_URL}/ocr/url", json=payload)
    print(f"Non-image URL Status: {response.status_code}")
    if response.status_code == 400:
        result = response.json()
        print(f"✅ Non-image URL handled correctly: {result.get('detail', 'No detail')}")
    else:
        print(f"⚠️  Unexpected response: {response.text}")

def main():
    """Run all tests"""
    print("🚀 Starting Enhanced OCR Service Comprehensive Test Suite")
    print("=" * 60)
    
    tests = [
        ("Health Check", test_health_check),
        ("Root Endpoint", test_root_endpoint),
        ("Languages Endpoint", test_languages_endpoint),
        ("OCR Upload (Text Format)", test_ocr_upload_text_format),
        ("OCR Upload (JSON Format)", test_ocr_upload_json_format),
        ("OCR URL (Text Format)", test_ocr_url_text_format),
        ("OCR URL (JSON Format)", test_ocr_url_json_format),
        ("Error Handling", test_error_handling),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, "✅ PASSED" if result else "❌ FAILED"))
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append((test_name, f"❌ FAILED ({str(e)})"))
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    for test_name, status in results:
        print(f"{status}: {test_name}")
        if "PASSED" in status:
            passed += 1
    
    print(f"\n✅ Tests passed: {passed}/{len(results)}")
    print(f"📈 Success rate: {(passed/len(results)*100):.1f}%")
    
    if passed == len(results):
        print("\n🎉 ALL TESTS PASSED! Enhanced OCR service is working perfectly!")
    else:
        print(f"\n⚠️  {len(results) - passed} tests failed. Please check the logs above.")

if __name__ == "__main__":
    main()
