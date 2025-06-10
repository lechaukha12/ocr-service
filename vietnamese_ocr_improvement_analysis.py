#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script so sánh PaddleOCR trước và sau khi cải thiện Vietnamese post-processing
Và so sánh với Google Gemini để demonstrate khả năng
"""

import os
import sys
import time
import json
import requests
from typing import Dict, List, Any
from datetime import datetime

class Vietnamese_OCR_Comparison:
    def __init__(self):
        self.before_results = {
            "text": "CONG HOAXA HOI CHU NGHiAVIET NAM\nDöc lap-Tudo-Hanh phüc\nSOCIALIST REPUBLIC OF VIET NAM\nIndependence-Freedom-Happiness\nCAN CUO'C CONG DAN\nCitizen ldentity Card \ns6/No.:060098002136\nHo va tenl Full name:\nLE CHAU KHA\nNgay sinh/Date of birth:12/04/1998\nGii tinh SexNamQuóc tich/NationalityViet Nam\nQué quän l Place of origin:\nChau Thanh,Long An\nNoi thuong trl Place of residenceTö 5.Phu Dien\nHam Hiep,Ham Thuan Bäc,Binh Thuan\nDate of expiry",
            "confidence": 0.9041,
            "processing_time": 1.95,
            "version": "PaddleOCR Original"
        }
    
    def test_enhanced_paddleocr(self, image_path: str) -> Dict[str, Any]:
        """Test enhanced PaddleOCR với Vietnamese post-processing"""
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
                    "engine": "PaddleOCR Enhanced v2.0",
                    "success": True,
                    "text": result.get("text", ""),
                    "confidence": result.get("confidence", 0),
                    "processing_time": processing_time,
                    "text_blocks": result.get("text_blocks", []),
                    "total_blocks": len(result.get("text_blocks", []))
                }
            else:
                return {
                    "engine": "PaddleOCR Enhanced v2.0", 
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "processing_time": processing_time
                }
                
        except Exception as e:
            return {
                "engine": "PaddleOCR Enhanced v2.0",
                "success": False,
                "error": str(e),
                "processing_time": time.time() - start_time if 'start_time' in locals() else 0
            }

    def test_gemini_api(self, image_path: str) -> Dict[str, Any]:
        """Test Google Gemini cho so sánh"""
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
                "error": "google-generativeai package not installed",
                "processing_time": 0
            }
        except Exception as e:
            return {
                "engine": "Google Gemini",
                "success": False,
                "error": str(e),
                "processing_time": time.time() - start_time if 'start_time' in locals() else 0
            }

    def analyze_vietnamese_diacritics(self, text: str) -> Dict[str, Any]:
        """Phân tích dấu tiếng Việt trong văn bản"""
        if not text:
            return {"total_chars": 0, "vietnamese_chars": 0, "percentage": 0, "diacritics_found": [], "specific_words": {}}
        
        vietnamese_chars = "áàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđ"
        vietnamese_chars += vietnamese_chars.upper()
        
        found_diacritics = []
        vietnamese_count = 0
        
        for char in text:
            if char in vietnamese_chars:
                vietnamese_count += 1
                if char not in found_diacritics:
                    found_diacritics.append(char)
        
        # Check specific Vietnamese words
        specific_words = {
            "Độc lập": "Độc lập" in text,
            "Tự do": "Tự do" in text,
            "Hạnh phúc": "Hạnh phúc" in text,
            "Nghĩa": "NGHĨA" in text or "nghĩa" in text,
            "Hòa": "HÒA" in text or "hòa" in text,
            "Quê quán": "Quê quán" in text,
            "Giới tính": "Giới tính" in text,
            "Quốc tịch": "Quốc tịch" in text,
            "Căn cước": "CĂN CƯỚC" in text or "căn cước" in text,
            "Thường trú": "thường trú" in text,
            "Bắc": "Bắc" in text
        }
        
        return {
            "total_chars": len(text),
            "vietnamese_chars": vietnamese_count,
            "percentage": (vietnamese_count / len(text)) * 100 if len(text) > 0 else 0,
            "diacritics_found": sorted(found_diacritics),
            "specific_words": specific_words,
            "specific_words_count": sum(specific_words.values())
        }

    def compare_before_after(self, enhanced_result: Dict) -> Dict[str, Any]:
        """So sánh trước và sau cải thiện"""
        
        before_analysis = self.analyze_vietnamese_diacritics(self.before_results["text"])
        after_analysis = self.analyze_vietnamese_diacritics(enhanced_result.get("text", ""))
        
        improvement = {
            "timestamp": datetime.now().isoformat(),
            "before": {
                **self.before_results,
                "analysis": before_analysis
            },
            "after": {
                **enhanced_result,
                "analysis": after_analysis
            },
            "improvements": {
                "vietnamese_chars_increase": after_analysis["vietnamese_chars"] - before_analysis["vietnamese_chars"],
                "percentage_increase": after_analysis["percentage"] - before_analysis["percentage"],
                "specific_words_improvement": after_analysis["specific_words_count"] - before_analysis["specific_words_count"],
                "new_diacritics": [d for d in after_analysis["diacritics_found"] if d not in before_analysis["diacritics_found"]]
            }
        }
        
        return improvement

    def run_full_comparison(self, image_path: str) -> Dict[str, Any]:
        """Chạy full comparison test"""
        print("🚀 VIETNAMESE OCR IMPROVEMENT ANALYSIS")
        print("=" * 60)
        
        if not os.path.exists(image_path):
            print(f"❌ Image file not found: {image_path}")
            return {}
        
        print(f"📸 Testing image: {os.path.basename(image_path)}")
        
        # Test enhanced PaddleOCR
        print(f"\n🔧 Testing Enhanced PaddleOCR v2.0...")
        enhanced_result = self.test_enhanced_paddleocr(image_path)
        
        if enhanced_result.get("success"):
            print(f"✅ Enhanced PaddleOCR completed in {enhanced_result['processing_time']:.2f}s")
            print(f"   Confidence: {enhanced_result.get('confidence', 0):.3f}")
        else:
            print(f"❌ Enhanced PaddleOCR failed: {enhanced_result.get('error', 'Unknown error')}")
            return {}
        
        # Compare before/after
        print(f"\n📊 BEFORE vs AFTER COMPARISON:")
        comparison = self.compare_before_after(enhanced_result)
        
        before = comparison["before"]["analysis"]
        after = comparison["after"]["analysis"]
        improvements = comparison["improvements"]
        
        print(f"┌─ ORIGINAL PaddleOCR:")
        print(f"├─   Vietnamese chars: {before['vietnamese_chars']}/{before['total_chars']} ({before['percentage']:.1f}%)")
        print(f"├─   Specific words: {before['specific_words_count']}/11")
        print(f"├─   Diacritics: {len(before['diacritics_found'])}")
        print(f"│")
        print(f"├─ ENHANCED PaddleOCR v2.0:")
        print(f"├─   Vietnamese chars: {after['vietnamese_chars']}/{after['total_chars']} ({after['percentage']:.1f}%)")
        print(f"├─   Specific words: {after['specific_words_count']}/11")
        print(f"├─   Diacritics: {len(after['diacritics_found'])}")
        print(f"│")
        print(f"└─ IMPROVEMENTS:")
        print(f"    • Vietnamese chars: +{improvements['vietnamese_chars_increase']}")
        print(f"    • Percentage: +{improvements['percentage_increase']:.1f}%")
        print(f"    • Specific words: +{improvements['specific_words_improvement']}")
        print(f"    • New diacritics: {improvements['new_diacritics']}")
        
        # Show specific word improvements
        print(f"\n🎯 SPECIFIC WORD RECOGNITION:")
        for word, recognized in after["specific_words"].items():
            status = "✅" if recognized else "❌"
            print(f"   {status} {word}")
        
        # Test Gemini for comparison
        print(f"\n🤖 Testing Google Gemini for comparison...")
        gemini_result = self.test_gemini_api(image_path)
        
        if gemini_result.get("success"):
            print(f"✅ Gemini completed in {gemini_result['processing_time']:.2f}s")
            gemini_analysis = self.analyze_vietnamese_diacritics(gemini_result.get("text", ""))
            
            print(f"\n🏆 FINAL COMPARISON:")
            print(f"┌─ Enhanced PaddleOCR v2.0: {after['vietnamese_chars']} Vietnamese chars ({after['percentage']:.1f}%)")
            print(f"├─ Google Gemini: {gemini_analysis['vietnamese_chars']} Vietnamese chars ({gemini_analysis['percentage']:.1f}%)")
            
            if after['vietnamese_chars'] >= gemini_analysis['vietnamese_chars']:
                print(f"└─ 🎉 PaddleOCR Enhanced WINS!")
            else:
                print(f"└─ 🥈 Gemini wins, but PaddleOCR much improved!")
                
            comparison["gemini"] = {
                **gemini_result,
                "analysis": gemini_analysis
            }
        else:
            print(f"❌ Gemini failed: {gemini_result.get('error', 'Unknown error')}")
        
        # Save results
        output_file = "/Users/lechaukha12/Desktop/ocr-service/VIETNAMESE_OCR_IMPROVEMENT_ANALYSIS.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(comparison, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Detailed results saved to: {output_file}")
        
        return comparison

def main():
    """Main function"""
    comparator = Vietnamese_OCR_Comparison()
    
    # Test image
    image_path = "/Users/lechaukha12/Desktop/ocr-service/IMG_4620.png"
    
    # Run full comparison
    results = comparator.run_full_comparison(image_path)
    
    if results:
        print(f"\n✨ SUMMARY:")
        improvements = results.get("improvements", {})
        print(f"   🚀 Vietnamese character recognition improved by {improvements.get('vietnamese_chars_increase', 0)} characters")
        print(f"   📈 Percentage improved by {improvements.get('percentage_increase', 0):.1f}%")
        print(f"   🎯 Specific Vietnamese words improved by {improvements.get('specific_words_improvement', 0)}")

if __name__ == "__main__":
    main()
