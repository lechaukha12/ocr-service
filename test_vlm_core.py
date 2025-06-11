#!/usr/bin/env python3
"""
Test VLM Core service with a simple OCR request
"""
import os
import requests
import argparse
import time
from PIL import Image
import io
import json

def test_vlm_core_ocr(image_path, base_url="http://localhost:8010"):
    """Test VLM Core OCR functionality"""
    print(f"Testing VLM Core OCR with image: {image_path}")
    
    # Check if image exists
    if not os.path.exists(image_path):
        print(f"Error: Image not found at {image_path}")
        return False
    
    # Check health endpoint
    try:
        resp = requests.get(f"{base_url}/health")
        if resp.status_code == 200:
            health_info = resp.json()
            print(f"✅ Health check passed:")
            print(f"  - Status: {health_info.get('status', 'unknown')}")
            print(f"  - Model: {health_info.get('model', 'unknown')}")
            print(f"  - Deployment: {health_info.get('deployment_type', 'container')}")
            print(f"  - Version: {health_info.get('version', 'unknown')}")
        else:
            print(f"❌ Health check failed: {resp.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error connecting to VLM Core service: {e}")
        return False
    
    # Test OCR endpoint
    try:
        with open(image_path, "rb") as img_file:
            files = {"image": (os.path.basename(image_path), img_file, "image/jpeg")}
            data = {"language": "vie"}
            
            start_time = time.time()
            resp = requests.post(f"{base_url}/ocr", files=files, data=data)
            processing_time = time.time() - start_time
            
            if resp.status_code == 200:
                result = resp.json()
                print(f"\n✅ OCR successful in {processing_time:.2f}s")
                print(f"Confidence: {result.get('confidence', 'N/A')}")
                print(f"Language: {result.get('language', 'N/A')}")
                print("\nText detected:")
                print("-" * 50)
                print(result.get("text", "No text found"))
                print("-" * 50)
                return True
            else:
                print(f"\n❌ OCR failed: {resp.status_code}")
                print(resp.text)
                return False
    except Exception as e:
        print(f"\n❌ Error during OCR: {e}")
        return False

def test_extract_info(image_path, base_url="http://localhost:8010"):
    """Test VLM Core info extraction functionality"""
    print(f"\nTesting VLM Core info extraction with image: {image_path}")
    
    # Check if image exists
    if not os.path.exists(image_path):
        print(f"Error: Image not found at {image_path}")
        return False
    
    # Test extract_info endpoint
    try:
        with open(image_path, "rb") as img_file:
            files = {"image": (os.path.basename(image_path), img_file, "image/jpeg")}
            data = {"language": "vie"}
            
            start_time = time.time()
            resp = requests.post(f"{base_url}/extract_info", files=files, data=data)
            processing_time = time.time() - start_time
            
            if resp.status_code == 200:
                result = resp.json()
                print(f"\n✅ Information extraction successful in {processing_time:.2f}s")
                print(f"Confidence: {result.get('confidence', 'N/A')}")
                print("\nExtracted Information:")
                print("-" * 50)
                print(f"ID Number: {result.get('id_number', 'N/A')}")
                print(f"Full Name: {result.get('full_name', 'N/A')}")
                print(f"Date of Birth: {result.get('date_of_birth', 'N/A')}")
                print(f"Gender: {result.get('gender', 'N/A')}")
                print(f"Nationality: {result.get('nationality', 'N/A')}")
                print(f"Place of Origin: {result.get('place_of_origin', 'N/A')}")
                print(f"Place of Residence: {result.get('place_of_residence', 'N/A')}")
                print(f"Expiry Date: {result.get('expiry_date', 'N/A')}")
                print(f"Document Type: {result.get('document_type', 'N/A')}")
                print("-" * 50)
                return True
            else:
                print(f"\n❌ Information extraction failed: {resp.status_code}")
                print(resp.text)
                return False
    except Exception as e:
        print(f"\n❌ Error during information extraction: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test VLM Core OCR and information extraction")
    parser.add_argument("image", help="Path to image file for testing")
    parser.add_argument("--url", default="http://localhost:8010", help="Base URL of VLM Core service")
    parser.add_argument("--extract-only", action="store_true", help="Test only information extraction")
    parser.add_argument("--ocr-only", action="store_true", help="Test only OCR")
    
    args = parser.parse_args()
    
    if not args.extract_only:
        ocr_success = test_vlm_core_ocr(args.image, args.url)
    else:
        ocr_success = True
        
    if not args.ocr_only:
        extract_success = test_extract_info(args.image, args.url)
    else:
        extract_success = True
    
    if ocr_success and extract_success:
        print("\n✅ All tests passed successfully!")
        exit(0)
    else:
        print("\n❌ Some tests failed!")
        exit(1)
