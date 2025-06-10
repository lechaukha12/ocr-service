#!/usr/bin/env python3
"""
Test script to debug OCR functionality
"""
import requests
import json

def test_ocr_service():
    """Test the OCR service with different configurations"""
    
    # Test health endpoint
    print("=== Testing Health Endpoint ===")
    try:
        response = requests.get("http://localhost:8010/health")
        print(f"Health Status: {response.status_code}")
        print(f"Health Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Health test failed: {e}")
        return
    
    # Test OCR with different images
    images = [
        "IMG_5132.png",
        "IMG_4620.png", 
        "test_image.png"
    ]
    
    for image_name in images:
        print(f"\n=== Testing OCR with {image_name} ===")
        try:
            with open(f"/Users/lechaukha12/Desktop/ocr-service/{image_name}", "rb") as f:
                files = {"image": f}
                response = requests.post("http://localhost:8010/ocr", files=files)
                
            print(f"Status Code: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
            
            # Check if text was detected
            result = response.json()
            if result.get("success") and result.get("text") and result.get("confidence", 0) > 0:
                print("✅ OCR successful - text detected!")
            else:
                print("⚠️  OCR completed but no text detected")
                
        except FileNotFoundError:
            print(f"❌ File {image_name} not found")
        except Exception as e:
            print(f"❌ Error testing {image_name}: {e}")

if __name__ == "__main__":
    test_ocr_service()
