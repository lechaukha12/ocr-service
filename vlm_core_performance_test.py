#!/usr/bin/env python3
"""
Performance and functionality test for VLM Core service
"""
import requests
import json
import time
import sys
from pathlib import Path

class VLMCorePerformanceTest:
    def __init__(self, base_url="http://localhost:8010"):
        self.base_url = base_url
        self.results = []

    def test_health_check(self):
        """Test service health and availability"""
        print("🔍 Testing service health...")
        try:
            start_time = time.time()
            response = requests.get(f"{self.base_url}/health")
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Service is healthy")
                print(f"   📊 Response time: {response_time:.3f}s")
                print(f"   🔧 Model: {data.get('model', 'unknown')}")
                print(f"   🚀 Deployment: {data.get('deployment_type', 'unknown')}")
                return True, response_time
            else:
                print(f"   ❌ Health check failed: {response.status_code}")
                return False, response_time
        except Exception as e:
            print(f"   ❌ Health check error: {e}")
            return False, 0

    def test_ocr_performance(self, image_path):
        """Test OCR functionality and performance"""
        print(f"🖼️  Testing OCR with {image_path}...")
        
        if not Path(image_path).exists():
            print(f"   ❌ Image file not found: {image_path}")
            return False, 0, ""
        
        try:
            start_time = time.time()
            
            with open(image_path, 'rb') as f:
                files = {"image": f}
                data = {"language": "vie"}
                response = requests.post(f"{self.base_url}/ocr", files=files, data=data, timeout=120)
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                text = result.get('text', '')
                confidence = result.get('confidence', 0)
                processing_time = result.get('processing_time', 0)
                
                print(f"   ✅ OCR completed successfully")
                print(f"   ⏱️  Processing time: {processing_time:.2f}s")
                print(f"   📊 Confidence: {confidence:.2f}")
                print(f"   📝 Text length: {len(text)} characters")
                print(f"   📄 Text preview: {text[:100]}...")
                
                return True, processing_time, text
            else:
                print(f"   ❌ OCR failed: {response.status_code}")
                return False, response_time, ""
                
        except requests.exceptions.Timeout:
            print(f"   ⏰ OCR request timed out (>120s)")
            return False, 120, ""
        except Exception as e:
            print(f"   ❌ OCR error: {e}")
            return False, 0, ""

    def test_extract_info_performance(self, image_path):
        """Test information extraction functionality"""
        print(f"📋 Testing info extraction with {image_path}...")
        
        if not Path(image_path).exists():
            print(f"   ❌ Image file not found: {image_path}")
            return False, 0, {}
        
        try:
            start_time = time.time()
            
            with open(image_path, 'rb') as f:
                files = {"image": f}
                data = {"language": "vie"}
                response = requests.post(f"{self.base_url}/extract_info", files=files, data=data, timeout=120)
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                
                print(f"   ✅ Info extraction completed successfully")
                print(f"   ⏱️  Processing time: {response_time:.2f}s")
                print(f"   🆔 ID Number: {result.get('id_number', 'N/A')}")
                print(f"   👤 Full Name: {result.get('full_name', 'N/A')}")
                print(f"   🎂 Date of Birth: {result.get('date_of_birth', 'N/A')}")
                
                return True, response_time, result
            else:
                print(f"   ❌ Info extraction failed: {response.status_code}")
                return False, response_time, {}
                
        except requests.exceptions.Timeout:
            print(f"   ⏰ Info extraction request timed out (>120s)")
            return False, 120, {}
        except Exception as e:
            print(f"   ❌ Info extraction error: {e}")
            return False, 0, {}

    def run_comprehensive_test(self):
        """Run all tests and generate report"""
        print("🚀 Starting VLM Core Performance Test Suite")
        print("=" * 60)
        
        # Test health
        health_ok, health_time = self.test_health_check()
        
        # Test images
        test_images = ["IMG_4620.png", "IMG_4637.png", "IMG_5132.png"]
        ocr_results = []
        extract_results = []
        
        for image in test_images:
            print(f"\n{'-' * 40}")
            if Path(image).exists():
                # Test OCR
                ocr_ok, ocr_time, ocr_text = self.test_ocr_performance(image)
                ocr_results.append((image, ocr_ok, ocr_time, len(ocr_text)))
                
                # Test extraction
                extract_ok, extract_time, extract_data = self.test_extract_info_performance(image)
                extract_results.append((image, extract_ok, extract_time, extract_data))
            else:
                print(f"   ⏭️  Skipping {image} (not found)")
        
        # Generate report
        self.generate_report(health_ok, health_time, ocr_results, extract_results)

    def generate_report(self, health_ok, health_time, ocr_results, extract_results):
        """Generate performance report"""
        print(f"\n{'=' * 60}")
        print("📊 VLM CORE SERVICE PERFORMANCE REPORT")
        print("=" * 60)
        
        # Service Health
        print(f"🏥 Service Health: {'✅ HEALTHY' if health_ok else '❌ UNHEALTHY'}")
        print(f"⚡ Health Check Time: {health_time:.3f}s")
        
        # OCR Performance
        print(f"\n🖼️  OCR Performance:")
        successful_ocr = [r for r in ocr_results if r[1]]
        if successful_ocr:
            avg_time = sum(r[2] for r in successful_ocr) / len(successful_ocr)
            avg_length = sum(r[3] for r in successful_ocr) / len(successful_ocr)
            print(f"   ✅ Success Rate: {len(successful_ocr)}/{len(ocr_results)} ({len(successful_ocr)/len(ocr_results)*100:.1f}%)")
            print(f"   ⏱️  Average Processing Time: {avg_time:.2f}s")
            print(f"   📝 Average Text Length: {avg_length:.0f} characters")
        else:
            print(f"   ❌ No successful OCR operations")
        
        # Info Extraction Performance
        print(f"\n📋 Info Extraction Performance:")
        successful_extract = [r for r in extract_results if r[1]]
        if successful_extract:
            avg_extract_time = sum(r[2] for r in successful_extract) / len(successful_extract)
            print(f"   ✅ Success Rate: {len(successful_extract)}/{len(extract_results)} ({len(successful_extract)/len(extract_results)*100:.1f}%)")
            print(f"   ⏱️  Average Processing Time: {avg_extract_time:.2f}s")
        else:
            print(f"   ❌ No successful extraction operations")
        
        # Overall Assessment
        print(f"\n🎯 Overall Assessment:")
        total_tests = 1 + len(ocr_results) + len(extract_results)
        successful_tests = int(health_ok) + len(successful_ocr) + len(successful_extract)
        success_rate = successful_tests / total_tests * 100
        
        print(f"   📊 Overall Success Rate: {successful_tests}/{total_tests} ({success_rate:.1f}%)")
        
        if success_rate >= 80:
            print(f"   🎉 Service Status: EXCELLENT")
        elif success_rate >= 60:
            print(f"   ⚠️  Service Status: GOOD")
        elif success_rate >= 40:
            print(f"   ⚠️  Service Status: NEEDS IMPROVEMENT")
        else:
            print(f"   ❌ Service Status: POOR")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        if successful_ocr and avg_time > 60:
            print(f"   🐌 OCR processing is slow (>{avg_time:.0f}s). Consider optimizing model or hardware.")
        if len(successful_ocr) < len(ocr_results):
            print(f"   ⚠️  Some OCR operations failed. Check error logs.")
        if len(successful_extract) < len(extract_results):
            print(f"   ⚠️  Some extraction operations failed. Check LLM configuration.")
        
        print(f"\n{'=' * 60}")

def main():
    """Main test runner"""
    tester = VLMCorePerformanceTest()
    tester.run_comprehensive_test()

if __name__ == "__main__":
    main()
