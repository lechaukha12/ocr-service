"""
Các tiện ích xử lý văn bản
"""
import re
from typing import Dict, Any, Optional

def postprocess_vietnamese_text(text: str) -> str:
    """
    Hậu xử lý văn bản tiếng Việt để cải thiện chất lượng
    
    Args:
        text: Văn bản cần xử lý
    
    Returns:
        str: Văn bản đã được xử lý
    """
    if not text:
        return text
    
    # Sửa các lỗi dấu tiếng Việt phổ biến
    vietnamese_fixes = {
        'a`': 'à', 'a\'': 'á', 'a?': 'ả', 'a~': 'ã', 'a.': 'ạ',
        'ă`': 'ằ', 'ă\'': 'ắ', 'ă?': 'ẳ', 'ă~': 'ẵ', 'ă.': 'ặ',
        'â`': 'ầ', 'â\'': 'ấ', 'â?': 'ẩ', 'â~': 'ẫ', 'â.': 'ậ',
        'e`': 'è', 'e\'': 'é', 'e?': 'ẻ', 'e~': 'ẽ', 'e.': 'ẹ',
        'ê`': 'ề', 'ê\'': 'ế', 'ê?': 'ể', 'ê~': 'ễ', 'ê.': 'ệ',
        'i`': 'ì', 'i\'': 'í', 'i?': 'ỉ', 'i~': 'ĩ', 'i.': 'ị',
        'o`': 'ò', 'o\'': 'ó', 'o?': 'ỏ', 'o~': 'õ', 'o.': 'ọ',
        'ô`': 'ồ', 'ô\'': 'ố', 'ô?': 'ổ', 'ô~': 'ỗ', 'ô.': 'ộ',
        'ơ`': 'ờ', 'ơ\'': 'ớ', 'ơ?': 'ở', 'ơ~': 'ỡ', 'ơ.': 'ợ',
        'u`': 'ù', 'u\'': 'ú', 'u?': 'ủ', 'u~': 'ũ', 'u.': 'ụ',
        'ư`': 'ừ', 'ư\'': 'ứ', 'ư?': 'ử', 'ư~': 'ữ', 'ư.': 'ự',
        'y`': 'ỳ', 'y\'': 'ý', 'y?': 'ỷ', 'y~': 'ỹ', 'y.': 'ỵ',
    }
    
    # Thay thế các dạng lỗi phổ biến
    processed_text = text
    for error, correction in vietnamese_fixes.items():
        processed_text = processed_text.replace(error, correction)
    
    # Sửa các lỗi cụm từ phổ biến trong CCCD/CMND
    common_phrases = [
        (r'CONG HOA XA HOI', 'CỘNG HÒA XÃ HỘI'),
        (r'CHU NGHIA VIET NAM', 'CHỦ NGHĨA VIỆT NAM'),
        (r'Doc lap - Tu do - Hanh phuc', 'Độc lập - Tự do - Hạnh phúc'),
        (r'CAN CUOC CONG DAN', 'CĂN CƯỚC CÔNG DÂN'),
        (r'CHUNG MINH NHAN DAN', 'CHỨNG MINH NHÂN DÂN'),
        (r'Ho va ten', 'Họ và tên'),
        (r'Ngay, thang, nam sinh', 'Ngày, tháng, năm sinh'),
        (r'Ngay sinh', 'Ngày sinh'),
        (r'Gioi tinh', 'Giới tính'),
        (r'Quoc tich', 'Quốc tịch'),
        (r'Que quan', 'Quê quán'),
        (r'Noi thuong tru', 'Nơi thường trú'),
        (r'Co gia tri den', 'Có giá trị đến'),
    ]
    
    for pattern, replacement in common_phrases:
        processed_text = re.sub(pattern, replacement, processed_text, flags=re.IGNORECASE)
    
    return processed_text

def extract_info_from_text(text: str) -> Dict[str, Any]:
    """
    Trích xuất thông tin từ văn bản CCCD/CMND
    
    Args:
        text: Văn bản cần trích xuất thông tin
    
    Returns:
        Dict[str, Any]: Thông tin đã trích xuất
    """
    info = {
        "id_number": None,
        "full_name": None,
        "date_of_birth": None,
        "gender": None,
        "nationality": None,
        "place_of_origin": None,
        "place_of_residence": None,
        "expiry_date": None,
        "document_type": None,
    }
    
    # Xác định loại giấy tờ
    if "CĂN CƯỚC CÔNG DÂN" in text.upper():
        info["document_type"] = "CCCD"
    elif "CHỨNG MINH NHÂN DÂN" in text.upper() or "CMND" in text.upper():
        info["document_type"] = "CMND"
    
    # Trích xuất số CMND/CCCD
    id_pattern = r'(?:Số|So):\s*(\d{9}|\d{12})'
    id_match = re.search(id_pattern, text)
    if id_match:
        info["id_number"] = id_match.group(1)
    
    # Trích xuất họ tên
    name_pattern = r'(?:Họ và tên|Ho va ten):\s*([^\n]+)'
    name_match = re.search(name_pattern, text)
    if name_match:
        info["full_name"] = name_match.group(1).strip()
    
    # Trích xuất ngày sinh
    dob_pattern = r'(?:Ngày sinh|Ngay sinh):\s*(\d{1,2}[/-]\d{1,2}[/-]\d{4}|\d{1,2}[/-]\d{1,2}[/-]\d{2})'
    dob_match = re.search(dob_pattern, text)
    if dob_match:
        info["date_of_birth"] = dob_match.group(1)
    
    # Trích xuất giới tính
    gender_pattern = r'(?:Giới tính|Gioi tinh):\s*(Nam|Nữ|Nu)'
    gender_match = re.search(gender_pattern, text, re.IGNORECASE)
    if gender_match:
        info["gender"] = gender_match.group(1)
    
    # Trích xuất quốc tịch
    nationality_pattern = r'(?:Quốc tịch|Quoc tich):\s*([^\n]+)'
    nationality_match = re.search(nationality_pattern, text)
    if nationality_match:
        info["nationality"] = nationality_match.group(1).strip()
    
    # Trích xuất quê quán
    origin_pattern = r'(?:Quê quán|Que quan):\s*([^\n]+)'
    origin_match = re.search(origin_pattern, text)
    if origin_match:
        info["place_of_origin"] = origin_match.group(1).strip()
    
    # Trích xuất nơi thường trú
    residence_pattern = r'(?:Nơi thường trú|Noi thuong tru):\s*([^\n]+)'
    residence_match = re.search(residence_pattern, text)
    if residence_match:
        info["place_of_residence"] = residence_match.group(1).strip()
    
    # Trích xuất ngày hết hạn
    expiry_pattern = r'(?:Có giá trị đến|Co gia tri den|Ngày hết hạn|Ngay het han):\s*(\d{1,2}[/-]\d{1,2}[/-]\d{4}|\d{1,2}[/-]\d{1,2}[/-]\d{2})'
    expiry_match = re.search(expiry_pattern, text)
    if expiry_match:
        info["expiry_date"] = expiry_match.group(1)
    
    return info
