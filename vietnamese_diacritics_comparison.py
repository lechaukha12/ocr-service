#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script so sánh PaddleOCR vs Google Gemini cho dấu tiếng Việt
Chạy test cả hai engine và so sánh kết quả chi tiết
"""

import os
import sys
import time
import json
import requests
from typing import Dict, List, Any
from datetime import datetime

# Test PaddleOCR qua API
def test_paddleocr_api(image_path: str) -> Dict[str, Any]:
    """Test PaddleOCR qua API container"""
    try:
        start_time = time.time()
        
        with open(image_path, 'rb') as f:
            files = {'image': f}
            data = {'format': 'json'}
            
            response = requests.post(
                'http://localhost:8010/ocr',
                files=files,
                data=data,
                timeout=30
            )
        
        processing_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            return {
                "engine": "PaddleOCR API",
                "success": True,
                "text": result.get("text", ""),
                "confidence": result.get("confidence", 0),
                "processing_time": processing_time,
                "text_blocks": result.get("text_blocks", []),
                "total_blocks": len(result.get("text_blocks", []))
            }
        else:
            return {
                "engine": "PaddleOCR API", 
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text}",
                "processing_time": processing_time
            }
            
    except Exception as e:
        return {
            "engine": "PaddleOCR API",
            "success": False,
            "error": str(e),
            "processing_time": time.time() - start_time if 'start_time' in locals() else 0
        }

# Test Google Gemini (nếu có API key)
def test_gemini_api(image_path: str) -> Dict[str, Any]:
    """Test Google Gemini với ảnh"""
    try:
        import google.generativeai as genai
        from PIL import Image
        
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            return {
                "engine": "Google Gemini",
                "success": False,
                "error": "GOOGLE_API_KEY environment variable not set",
                "processing_time": 0
            }
        
        start_time = time.time()
        
        # Configure Gemini
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Load image
        image = Image.open(image_path)
        
        # Vietnamese OCR prompt
        prompt = """
        Hãy nhận diện và trích xuất toàn bộ văn bản tiếng Việt trong ảnh này.
        Đặc biệt chú ý đến các dấu tiếng Việt (á, à, ả, ã, ạ, ă, ắ, ằ, ẳ, ẵ, ặ, â, ấ, ầ, ẩ, ẫ, ậ, v.v.).
        Chỉ trả về văn bản được nhận diện, không thêm bất kỳ giải thích nào.
        """
        
        response = model.generate_content([prompt, image])
        processing_time = time.time() - start_time
        
        if response and response.text:
            return {
                "engine": "Google Gemini",
                "success": True,
                "text": response.text.strip(),
                "processing_time": processing_time,
                "confidence": None,  # Gemini không cung cấp confidence score
                "text_blocks": None,
                "total_blocks": None
            }
        else:
            return {
                "engine": "Google Gemini",
                "success": False,
                "error": "No response from Gemini",
                "processing_time": processing_time
            }
            
    except ImportError:
        return {
            "engine": "Google Gemini",
            "success": False,
            "error": "google-generativeai package not installed. Run: pip install google-generativeai",
            "processing_time": 0
        }
    except Exception as e:
        return {
            "engine": "Google Gemini",
            "success": False,
            "error": str(e),
            "processing_time": time.time() - start_time if 'start_time' in locals() else 0
        }

def analyze_vietnamese_diacritics(text: str) -> Dict[str, Any]:
    """Phân tích dấu tiếng Việt trong văn bản"""
    if not text:
        return {"total_chars": 0, "vietnamese_chars": 0, "percentage": 0, "diacritics_found": []}
    
    vietnamese_chars = "áàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđ"
    vietnamese_chars += vietnamese_chars.upper()
    
    found_diacritics = []
    vietnamese_count = 0
    
    for char in text:
        if char in vietnamese_chars:
            vietnamese_count += 1
            if char not in found_diacritics:
                found_diacritics.append(char)
    
    return {
        "total_chars": len(text),
        "vietnamese_chars": vietnamese_count,
        "percentage": (vietnamese_count / len(text)) * 100 if len(text) > 0 else 0,
        "diacritics_found": sorted(found_diacritics)
    }

def compare_results(paddle_result: Dict, gemini_result: Dict) -> Dict[str, Any]:
    """So sánh kết quả giữa PaddleOCR và Gemini"""
    comparison = {
        "timestamp": datetime.now().isoformat(),
        "paddle_analysis": {},
        "gemini_analysis": {},
        "summary": {}
    }
    
    # Analyze PaddleOCR
    if paddle_result.get("success"):
        paddle_text = paddle_result.get("text", "")
        comparison["paddle_analysis"] = {
            "text_preview": paddle_text[:200] + "..." if len(paddle_text) > 200 else paddle_text,
            "diacritics": analyze_vietnamese_diacritics(paddle_text),
            "confidence": paddle_result.get("confidence"),
            "processing_time": paddle_result.get("processing_time"),
            "text_blocks": paddle_result.get("total_blocks")
        }
    
    # Analyze Gemini
    if gemini_result.get("success"):
        gemini_text = gemini_result.get("text", "")
        comparison["gemini_analysis"] = {
            "text_preview": gemini_text[:200] + "..." if len(gemini_text) > 200 else gemini_text,
            "diacritics": analyze_vietnamese_diacritics(gemini_text),
            "confidence": "Not available",
            "processing_time": gemini_result.get("processing_time"),
            "text_blocks": "Not available"
        }
    
    # Summary
    paddle_diacritics = comparison["paddle_analysis"].get("diacritics", {}).get("vietnamese_chars", 0)
    gemini_diacritics = comparison["gemini_analysis"].get("diacritics", {}).get("vietnamese_chars", 0)
    
    comparison["summary"] = {
        "paddle_vietnamese_chars": paddle_diacritics,
        "gemini_vietnamese_chars": gemini_diacritics,
        "diacritics_difference": gemini_diacritics - paddle_diacritics,
        "winner": "Gemini" if gemini_diacritics > paddle_diacritics else "PaddleOCR" if paddle_diacritics > gemini_diacritics else "Tie"
    }
    
    return comparison

def main():
    """Main function"""
    print("🚀 VIETNAMESE DIACRITICS COMPARISON TEST")
    print("=" * 50)
    
    # Test image
    image_path = "/Users/lechaukha12/Desktop/ocr-service/IMG_4620.png"
    
    if not os.path.exists(image_path):
        print(f"❌ Image file not found: {image_path}")
        sys.exit(1)
    
    print(f"📸 Testing image: {os.path.basename(image_path)}")
    
    # Test PaddleOCR
    print(f"\n🔧 Testing PaddleOCR API...")
    paddle_result = test_paddleocr_api(image_path)
    
    if paddle_result.get("success"):
        print(f"✅ PaddleOCR completed in {paddle_result['processing_time']:.2f}s")
        print(f"   Confidence: {paddle_result.get('confidence', 0):.2f}")
        print(f"   Text blocks: {paddle_result.get('total_blocks', 0)}")
    else:
        print(f"❌ PaddleOCR failed: {paddle_result.get('error', 'Unknown error')}")
    
    # Test Gemini
    print(f"\n🤖 Testing Google Gemini...")
    gemini_result = test_gemini_api(image_path)
    
    if gemini_result.get("success"):
        print(f"✅ Gemini completed in {gemini_result['processing_time']:.2f}s")
    else:
        print(f"❌ Gemini failed: {gemini_result.get('error', 'Unknown error')}")
    
    # Compare results
    if paddle_result.get("success") or gemini_result.get("success"):
        print(f"\n📊 COMPARISON RESULTS:")
        comparison = compare_results(paddle_result, gemini_result)
        
        # Print summary
        print(f"┌─ PaddleOCR Vietnamese chars: {comparison['summary']['paddle_vietnamese_chars']}")
        print(f"├─ Gemini Vietnamese chars: {comparison['summary']['gemini_vietnamese_chars']}")
        print(f"├─ Difference: {comparison['summary']['diacritics_difference']}")
        print(f"└─ Winner: {comparison['summary']['winner']}")
        
        # Print text previews
        if paddle_result.get("success"):
            print(f"\n📝 PaddleOCR Text Preview:")
            print(f"   {comparison['paddle_analysis']['text_preview']}")
            print(f"   Diacritics found: {comparison['paddle_analysis']['diacritics']['diacritics_found']}")
        
        if gemini_result.get("success"):
            print(f"\n📝 Gemini Text Preview:")
            print(f"   {comparison['gemini_analysis']['text_preview']}")
            print(f"   Diacritics found: {comparison['gemini_analysis']['diacritics']['diacritics_found']}")
        
        # Save detailed results
        output_file = "/Users/lechaukha12/Desktop/ocr-service/VIETNAMESE_DIACRITICS_COMPARISON.json"
        detailed_results = {
            "paddle_result": paddle_result,
            "gemini_result": gemini_result,
            "comparison": comparison
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(detailed_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Detailed results saved to: {output_file}")
    
    else:
        print(f"\n❌ Both engines failed, cannot compare results")

if __name__ == "__main__":
    main()
