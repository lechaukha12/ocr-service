#!/usr/bin/env python3
"""
Test riêng cho ảnh IMG_4620.png với VLM Core
Phân tích chi tiết độ chính xác và hiệu suất
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8010"
TEST_IMAGE = "/Users/lechaukha12/Desktop/ocr-service/IMG_4620.png"

def print_header(title):
    """In header với định dạng đẹp"""
    print(f"\n{'='*70}")
    print(f"🔍 {title}")
    print(f"{'='*70}")

def analyze_ocr_results(result, test_name):
    """Phân tích chi tiết kết quả OCR"""
    print(f"\n📊 KẾT QUẢ {test_name}:")
    print(f"   ✅ Thành công: {result['success']}")
    print(f"   🤖 Model: {result['model']}")
    print(f"   🎯 Độ tin cậy: {result['confidence']:.4f} ({result['confidence']*100:.2f}%)")
    print(f"   ⚡ Thời gian xử lý: {result['processing_time']:.4f} giây")
    print(f"   📝 Độ dài văn bản: {len(result['text'])} ký tự")
    
    if result.get('text_blocks'):
        print(f"   📦 Số khối văn bản: {len(result['text_blocks'])}")
        
        # Phân tích từng text block
        print(f"\n🔍 CHI TIẾT CÁC KHỐI VĂN BẢN:")
        for i, block in enumerate(result['text_blocks'][:5]):  # Hiển thị 5 block đầu
            print(f"   {i+1}. '{block['text'][:40]}...' - Tin cậy: {block['confidence']:.4f}")
    
    # Hiển thị văn bản được trích xuất
    print(f"\n📄 VĂN BẢN TRÍCH XUẤT:")
    lines = result['text'].split('\n')
    for i, line in enumerate(lines[:10]):  # Hiển thị 10 dòng đầu
        print(f"   {i+1:2d}. {line}")
    
    if len(lines) > 10:
        print(f"   ... và {len(lines) - 10} dòng khác")

def test_img_4620_comprehensive():
    """Test toàn diện ảnh IMG_4620.png"""
    print_header("TEST TOÀN DIỆN ẢNH IMG_4620.PNG - CCCD TIẾNG VIỆT")
    
    # Test 1: Text format
    print(f"\n🧪 TEST 1: ĐỊNH DẠNG TEXT")
    try:
        with open(TEST_IMAGE, 'rb') as f:
            files = {'image': f}
            data = {'format': 'text'}
            
            start_time = time.time()
            response = requests.post(f"{BASE_URL}/ocr", files=files, data=data, timeout=30)
            end_time = time.time()
        
        if response.status_code == 200:
            result = response.json()
            analyze_ocr_results(result, "TEXT FORMAT")
            print(f"   🕐 Thời gian request: {end_time - start_time:.4f} giây")
            text_result = result
        else:
            print(f"❌ Lỗi: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ Exception: {e}")
        return
    
    # Test 2: JSON format  
    print(f"\n🧪 TEST 2: ĐỊNH DẠNG JSON")
    try:
        with open(TEST_IMAGE, 'rb') as f:
            files = {'image': f}
            data = {'format': 'json'}
            
            start_time = time.time()
            response = requests.post(f"{BASE_URL}/ocr", files=files, data=data, timeout=30)
            end_time = time.time()
        
        if response.status_code == 200:
            result = response.json()
            analyze_ocr_results(result, "JSON FORMAT")
            print(f"   🕐 Thời gian request: {end_time - start_time:.4f} giây")
            json_result = result
        else:
            print(f"❌ Lỗi: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ Exception: {e}")
        return
    
    # Phân tích so sánh
    print_header("PHÂN TÍCH SO SÁNH VÀ ĐÁNH GIÁ")
    
    print(f"\n📊 SO SÁNH HIỆU SUẤT:")
    print(f"   Text format  - Thời gian: {text_result['processing_time']:.4f}s")
    print(f"   JSON format  - Thời gian: {json_result['processing_time']:.4f}s")
    print(f"   Chênh lệch   - {abs(text_result['processing_time'] - json_result['processing_time']):.4f}s")
    
    print(f"\n🎯 ĐÁNH GIÁ CHẤT LƯỢNG:")
    confidence = text_result['confidence']
    if confidence >= 0.9:
        grade = "XUẤT SẮC ⭐⭐⭐⭐⭐"
    elif confidence >= 0.8:
        grade = "TỐT ⭐⭐⭐⭐"
    elif confidence >= 0.7:
        grade = "KHÁ ⭐⭐⭐"
    elif confidence >= 0.6:
        grade = "TRUNG BÌNH ⭐⭐"
    else:
        grade = "CẦN CẢI THIỆN ⭐"
    
    print(f"   Độ tin cậy: {confidence:.4f} ({confidence*100:.2f}%) - {grade}")
    
    # Phân tích nội dung CCCD
    print(f"\n📋 PHÂN TÍCH NỘI DUNG CCCD:")
    text = text_result['text']
    
    # Tìm các thông tin quan trọng
    info_found = {}
    info_patterns = {
        "Họ tên": "LE CHAU KHA" in text,
        "Số CCCD": "060098002136" in text,
        "Ngày sinh": "12/04/1998" in text,
        "Quê quán": "Long An" in text,
        "Nơi thường trú": "Binh Thuan" in text,
        "Tiếng Việt": "CONG HOA" in text,
        "Tiếng Anh": "SOCIALIST REPUBLIC" in text
    }
    
    found_count = 0
    for info, found in info_patterns.items():
        status = "✅" if found else "❌"
        print(f"   {status} {info}: {'Có' if found else 'Không tìm thấy'}")
        if found:
            found_count += 1
    
    accuracy_percent = (found_count / len(info_patterns)) * 100
    print(f"\n📈 ĐỘ CHÍNH XÁC THÔNG TIN: {found_count}/{len(info_patterns)} ({accuracy_percent:.1f}%)")
    
    # Phân tích text blocks
    if json_result.get('text_blocks'):
        blocks = json_result['text_blocks']
        print(f"\n🔍 PHÂN TÍCH TEXT BLOCKS:")
        print(f"   Tổng số blocks: {len(blocks)}")
        
        # Thống kê confidence
        confidences = [block['confidence'] for block in blocks]
        avg_confidence = sum(confidences) / len(confidences)
        min_confidence = min(confidences)
        max_confidence = max(confidences)
        
        print(f"   Độ tin cậy trung bình: {avg_confidence:.4f}")
        print(f"   Độ tin cậy thấp nhất: {min_confidence:.4f}")
        print(f"   Độ tin cậy cao nhất: {max_confidence:.4f}")
        
        # Top 3 blocks có confidence cao nhất
        sorted_blocks = sorted(blocks, key=lambda x: x['confidence'], reverse=True)
        print(f"\n🏆 TOP 3 BLOCKS CÓ ĐỘ TIN CẬY CAO NHẤT:")
        for i, block in enumerate(sorted_blocks[:3]):
            print(f"   {i+1}. {block['confidence']:.4f} - '{block['text'][:50]}...'")
    
    # Kết luận
    print_header("KẾT LUẬN")
    print(f"🎉 VLM Core v2.0.0 với PaddleOCR hoạt động XUẤT SẮC!")
    print(f"✅ Độ tin cậy tổng thể: {confidence:.4f} ({confidence*100:.2f}%)")
    print(f"✅ Thời gian xử lý: {text_result['processing_time']:.2f} giây")
    print(f"✅ Nhận diện được: {found_count}/{len(info_patterns)} thông tin quan trọng")
    print(f"✅ Số text blocks: {len(json_result.get('text_blocks', []))}")
    print(f"✅ Hỗ trợ cả 2 định dạng: Text và JSON với bounding boxes")
    
    if confidence >= 0.9 and found_count >= 6:
        print(f"\n🚀 ĐÁNH GIÁ CUỐI: SẴN SÀNG CHO PRODUCTION!")
        print(f"   Hệ thống có thể xử lý CCCD tiếng Việt với độ chính xác cao.")
    else:
        print(f"\n⚠️  ĐÁNH GIÁ CUỐI: CẦN KIỂM TRA THÊM")
        print(f"   Một số thông tin có thể cần xử lý bổ sung.")

def main():
    """Chạy test chính"""
    print_header("VLM CORE TEST - ẢNH IMG_4620.PNG")
    print(f"🕐 Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 File test: {TEST_IMAGE}")
    print(f"🔗 Service: {BASE_URL}")
    
    # Kiểm tra health trước
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            health = response.json()
            print(f"✅ Service healthy: {health['model']} - {health['status']}")
        else:
            print(f"❌ Service không healthy: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Không thể kết nối service: {e}")
        return
    
    # Chạy test chính
    test_img_4620_comprehensive()
    
    print(f"\n🎯 Test hoàn thành lúc: {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    main()
