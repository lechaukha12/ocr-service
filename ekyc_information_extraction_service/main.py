from fastapi import FastAPI, HTTPException, status, Body
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List, Callable
import re
import json 

import google.generativeai as genai
from config import settings 

app = FastAPI(title="eKYC Information Extraction Service (Hybrid)")

IS_GEMINI_CONFIGURED = False
if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "YOUR_GEMINI_API_KEY_HERE":
    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        IS_GEMINI_CONFIGURED = True
    except Exception as e:
        IS_GEMINI_CONFIGURED = False
else:
    pass

VIETNAMESE_CHARS = "A-ZÀ-ỹÁ-ỹẠ-ỹĂ-ỹẰ-ỹẲ-ỹẴ-ỹẶ-ỹÂ-ỹẦ-ỹẨ-ỹẪ-ỹẬ-ỹĐđÈ-ỹÉ-ỹẸ-ỹÊ-ỹỀ-ỹỂ-ỹỄ-ỹỆ-ỹÌ-ỹÍ-ỹỈ-ỹỊ-ỹÒ-ỹÓ-ỹỌ-ỹÔ-ỹỒ-ỹỔ-ỹỖ-ỹỘ-ỹƠ-ỹỜ-ỹỞ-ỹỠ-ỹỢ-ỹÙ-ỹÚ-ỹỦ-ỹŨ-ỹỤ-ỹƯ-ỹỪ-ỹỨ-ỹỬ-ỹỮ-ỹỰ-ỹỲ-ỹÝ-ỹỶ-ỹỸ-ỹỴ-ỹ"
NAME_ALLOWED_CHARS = f"{VIETNAMESE_CHARS}A-Z\\s'.`-" 
ADDRESS_ALLOWED_CHARS = f"{VIETNAMESE_CHARS}A-Z0-9\\s.,/-()" 
ID_NUMBER_CHARS = r"\d\s" 

class OCRInput(BaseModel):
    ocr_text: str = Field(..., example="Số/NG: 060088002136\nHọ và tên/Full name: LÊ CHÂU KHẢ\nNgày sinh/Date of birth: 12/04/1998\nGiới tính/Sex: Nam Quốc tịch/Nationality: Việt Nam\nQuê quán/Place of origin: Châu Thành, Long An\nNơi thường trú/Place of residence: Tổ 5, Phú Điền, Hàm Hiệp, Hàm Thuận Bắc, Bình Thuận\nCó giá trị đến/Date of expiry: 12/04/2038\nĐặc điểm nhận dạng: Nốt ruồi C.Trán P 2cm\nngày 15 tháng 07 năm 2015\nNơi cấp: CỤC TRƯỞNG CỤC CẢNH SÁT QLHC VỀ TTXH")
    language: Optional[str] = Field("vie", example="vie")
    use_gemini_fallback: Optional[bool] = Field(True)


class ExtractedInfo(BaseModel):
    id_number: Optional[str] = None
    full_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    nationality: Optional[str] = None
    place_of_origin: Optional[str] = None
    place_of_residence: Optional[str] = None
    expiry_date: Optional[str] = None
    date_of_issue: Optional[str] = None
    place_of_issue: Optional[str] = None
    personal_identification_features: Optional[str] = None 
    ethnicity: Optional[str] = None 
    religion: Optional[str] = None 
    raw_input: str
    errors: Optional[List[Dict[str, str]]] = None
    extraction_method: Optional[str] = "regex" 

ID_KEYWORDS = [
    r"Số", r"SỐ", r"No\.", r"SỐ/NO\.", r"Số/N[Gg]", r"SỐ/NG", 
    r"SỐ CCCD", r"Số CCCD", r"CCCD", r"Số CMND", r"CMND",
    r"S[oôỔ0]\s*:", r"S[oôỔ0]\s*CCCD\s*:", r"S[oôỔ0]\s*CMND\s*:"
]
NAME_KEYWORDS = [
    r"Họ và tên", r"HỌ VÀ TÊN", r"Họ tên", r"HỌ TÊN", r"Full name", r"FULL NAME",
    r"H[oọỌ]\s*v[aàÀ]\s*t[eêÊ]n", r"H[oọỌ]\s*t[eêÊ]n",
    r"\[Zọ và tên ƒ Full name" 
]
DOB_KEYWORDS = [
    r"Ngày sinh", r"NGÀY SINH", r"Date of birth", r"DATE OF BIRTH",
    r"Ng[aàÀ]y\s*sinh", r"Ng[aàÀ]y\s*s[i1ÍÌ]nh",
    r"Mgày sinh\s*!\s*Dafe of bifh" 
]
SEX_KEYWORDS = [
    r"Giới tính", r"GIỚI TÍNH", r"Sex", r"SEX",
    r"Gi[oớƠỚ]i\s*t[iíÌ]nh", r"Giới tỉnh"
]
NATIONALITY_KEYWORDS = [
    r"Quốc tịch", r"QUỐC TỊCH", r"Nationality", r"NATIONALITY",
    r"Qu[oôỐỔ]c\s*t[iịỊ]ch", r"Quốc địch", r"Quốc tịch\s*Naionelt"
]
ORIGIN_KEYWORDS = [
    r"Quê quán", r"QUÊ QUÁN", r"Place of origin", r"PLACE OF ORIGIN",
    r"Qu[eêÊ]\s*qu[aáÀ]n", r"Quê quán\s*l\s*Place of origlr"
]
RESIDENCE_KEYWORDS = [
    r"Nơi thường trú", r"NƠI THƯỜNG TRÚ", r"Nơi ĐKHK thường trú", 
    r"Place of residence", r"PLACE OF RESIDENCE",
    r"N[oơƠ]i\s*th[uưƯờỜ]ng\s*tr[uúÚ]", r"Nơi thường trú\s*Í\s*Place OÏ f residerce"
]
EXPIRY_KEYWORDS = [
    r"Có giá trị đến", r"CÓ GIÁ TRỊ ĐẾN", r"Date of expiry", r"DATE OF EXPIRY",
    r"C[oóỎÕỌÓ]\s*gi[aáÀ]\s*tr[iịỊ]\s*đ[eếẾ]n", r"Dai6 d\[cplf:"
]
ISSUE_DATE_KEYWORDS = [r"ngày", r"Ngày"] 
ISSUE_PLACE_KEYWORDS = [r"Nơi cấp", r"NƠI CẤP", r"Place of issue", r"TẠI"]
ID_FEATURES_KEYWORDS = [
    r"Đặc điểm nhận dạng", r"ĐẶC ĐIỂM NHẬN DẠNG", r"Personal identification",
    r"Đ[aăĂ]c\s*đ[iểỂ]m\s*nh[aậẬ]n\s*d[aạẠ]ng"
]
ETHNICITY_KEYWORDS = [r"Dân tộc", r"DÂN TỘC", r"Ethnicity"]
RELIGION_KEYWORDS = [r"Tôn giáo", r"TÔN GIÁO", r"Religion"]

def create_keyword_regex_group(keywords: List[str]) -> str:
    return r"(?:" + "|".join(keywords) + r")"

ID_KWS_RGX = create_keyword_regex_group(ID_KEYWORDS)
NAME_KWS_RGX = create_keyword_regex_group(NAME_KEYWORDS)
DOB_KWS_RGX = create_keyword_regex_group(DOB_KEYWORDS)
SEX_KWS_RGX = create_keyword_regex_group(SEX_KEYWORDS)
NAT_KWS_RGX = create_keyword_regex_group(NATIONALITY_KEYWORDS)
ORIGIN_KWS_RGX = create_keyword_regex_group(ORIGIN_KEYWORDS)
RESIDENCE_KWS_RGX = create_keyword_regex_group(RESIDENCE_KEYWORDS)
EXPIRY_KWS_RGX = create_keyword_regex_group(EXPIRY_KEYWORDS)
ISSUE_DATE_KWS_RGX = create_keyword_regex_group(ISSUE_DATE_KEYWORDS)
ISSUE_PLACE_KWS_RGX = create_keyword_regex_group(ISSUE_PLACE_KEYWORDS)
ID_FEATURES_KWS_RGX = create_keyword_regex_group(ID_FEATURES_KEYWORDS)
ETHNICITY_KWS_RGX = create_keyword_regex_group(ETHNICITY_KEYWORDS)
RELIGION_KWS_RGX = create_keyword_regex_group(RELIGION_KEYWORDS)

def clean_text_before_extraction(text: str) -> str:
    text = re.sub(r'\s*\n\s*', '\n', text) 
    text = re.sub(r' +', ' ', text) 
    text = text.replace("Naionelt", "Nationality")
    text = text.replace("origlr", "origin")
    text = text.replace("residerce", "residence")
    text = text.replace("bifh", "birth")
    text = text.replace("Dafe", "Date")
    text = text.replace("ƒ", ":") 
    text = text.replace("Í", ":")
    text = text.replace("l ", ": ") 
    return text.strip()

def general_field_cleaner(value: Optional[str], field_name: Optional[str] = None) -> Optional[str]:
    if not value: return None
    value = value.replace('\n', ' ').strip()
    value = re.sub(r'\s*\-\s*¬?\s*$', '', value).strip() 
    value = re.sub(r'\s*"\d+\.\.\.\s*', '', value).strip() 
    value = re.sub(r' {2,}', ' ', value) 
    value = value.strip(' \t\n\r,:;/.!')
    return value if value else None

def post_process_id_number(id_num: Optional[str], field_name: str) -> Optional[str]:
    if not id_num: return None
    id_num = re.sub(r'[^0-9]', '', id_num) 
    if len(id_num) == 9 or len(id_num) == 12:
        return id_num
    return None

def post_process_name(name: Optional[str], field_name: str) -> Optional[str]:
    if not name: return None
    name = re.sub(rf"^[^{NAME_ALLOWED_CHARS}]+|[^{NAME_ALLOWED_CHARS}]+$", "", name).strip()
    name = re.sub(r'\s+', ' ', name).strip()
    name = re.sub(r'[.!`]+$', '', name).strip() 
    name = name.upper() 
    return name if len(name) > 1 else None

def normalize_date_string(date_str: Optional[str], field_name: str = "") -> Optional[str]:
    if not date_str: return None
    if field_name == "expiry_date" and re.search(r"Không\s*(?:thời)?\s*hạn|Vô\s*thời\s*hạn|KHH", date_str, re.IGNORECASE):
        return "Không thời hạn"
    cleaned_date = re.sub(r'\s*([/\.\-])\s*', r'\1', date_str) 
    cleaned_date = re.sub(r'[^0-9/]', '', cleaned_date) 
    match = re.match(r'(\d{1,2})/(\d{1,2})/(\d{4})', cleaned_date)
    if match:
        day, month, year = match.groups()
        try:
            d_int, m_int, y_int = int(day), int(month), int(year)
            if not (1 <= m_int <= 12 and 1 <= d_int <= 31 and 1900 <= y_int <= 2100):
                return None 
        except ValueError: return None 
        return f"{day.zfill(2)}/{month.zfill(2)}/{year}"
    return None

def post_process_address(address: Optional[str], field_name: str) -> Optional[str]:
    if not address: return None
    keywords_rgx_to_remove = KEYWORD_CONFIG.get(field_name, {}).get("keywords_rgx_for_cleaning", "")
    if keywords_rgx_to_remove:
        address = re.sub(rf"^\s*{keywords_rgx_to_remove}\s*[:\sƒlÍ.]*\s*", "", address, flags=re.IGNORECASE).strip()
    address = general_field_cleaner(address, field_name)
    address = re.sub(r'\s*-\s*¬\s*$', '', address).strip()
    address = re.sub(r'\s*\^s*$', '', address).strip()
    address = re.sub(r'\s*a_—ẴẮ`\s*_—\.\s*r3\s*l\s*mẽ\s*$', '', address, flags=re.IGNORECASE).strip()
    return address

def extract_single_field_from_patterns(
    patterns: List[Any], text: str, field_name: str, 
    default_group_index: int = 1, 
    flags=re.IGNORECASE | re.DOTALL, 
    post_process_func: Optional[Callable[[Optional[str], str], Optional[str]]] = None
) -> Optional[str]:
    for pattern_spec in patterns:
        current_pattern: str
        current_group_index: int = default_group_index
        
        if isinstance(pattern_spec, tuple) and len(pattern_spec) == 2:
            current_pattern, current_group_index = pattern_spec
        elif isinstance(pattern_spec, str):
            current_pattern = pattern_spec
        else:
            continue

        try:
            match = re.search(current_pattern, text, flags)
            if match:
                value = match.group(current_group_index)
                if value is not None:
                    value = value.strip() 
                    if post_process_func:
                        value = post_process_func(value, field_name)
                    else: 
                        value = general_field_cleaner(value, field_name)
                    return value if value else None 
        except IndexError:
            continue
        except re.error as e:
            continue
    return None

KEYWORD_CONFIG: Dict[str, Dict[str, Any]] = {
    "id_number": {"keywords_rgx_for_cleaning": ID_KWS_RGX, "post_process": post_process_id_number},
    "full_name": {"keywords_rgx_for_cleaning": NAME_KWS_RGX, "post_process": post_process_name},
    "date_of_birth": {"keywords_rgx_for_cleaning": DOB_KWS_RGX, "post_process": normalize_date_string},
    "gender": {"keywords_rgx_for_cleaning": SEX_KWS_RGX, "post_process": general_field_cleaner},
    "nationality": {"keywords_rgx_for_cleaning": NAT_KWS_RGX, "post_process": general_field_cleaner},
    "place_of_origin": {"keywords_rgx_for_cleaning": ORIGIN_KWS_RGX, "post_process": post_process_address},
    "place_of_residence": {"keywords_rgx_for_cleaning": RESIDENCE_KWS_RGX, "post_process": post_process_address},
    "expiry_date": {"keywords_rgx_for_cleaning": EXPIRY_KWS_RGX, "post_process": normalize_date_string},
    "date_of_issue": {"keywords_rgx_for_cleaning": ISSUE_DATE_KWS_RGX, "post_process": normalize_date_string},
    "place_of_issue": {"keywords_rgx_for_cleaning": ISSUE_PLACE_KWS_RGX, "post_process": post_process_address},
    "personal_identification_features": {"keywords_rgx_for_cleaning": ID_FEATURES_KWS_RGX, "post_process": post_process_address},
    "ethnicity": {"keywords_rgx_for_cleaning": ETHNICITY_KWS_RGX, "post_process": general_field_cleaner},
    "religion": {"keywords_rgx_for_cleaning": RELIGION_KWS_RGX, "post_process": general_field_cleaner},
}

EXTRACTION_PATTERNS: Dict[str, List[Any]] = {
    "id_number": [
        rf"{ID_KWS_RGX}\s*[:\s.]*\s*((?:[{ID_NUMBER_CHARS}]{{10,18}}))", 
        (r"^(?:[^{{\n}}]*\n)?\s*((?:\d\s*){{11}}\d)\s*$", 1), 
        (r"^(?:[^{{\n}}]*\n)?\s*((?:\d\s*){{8}}\d)\s*$", 1)   
    ],
    "full_name": [
        rf"{NAME_KWS_RGX}\s*[:\sƒ]*\s*([{NAME_ALLOWED_CHARS}]+?)(?=\n\s*(?:{DOB_KWS_RGX}|{SEX_KWS_RGX}|{NAT_KWS_RGX})|\n\n|$)",
        rf"^(?!(?:{ID_KWS_RGX}|{DOB_KWS_RGX}|{SEX_KWS_RGX}|{NAT_KWS_RGX}|{ORIGIN_KWS_RGX}|{RESIDENCE_KWS_RGX}|{EXPIRY_KWS_RGX}))\s*([{NAME_ALLOWED_CHARS}]{{3,}}[\s{NAME_ALLOWED_CHARS}]*)$"
    ],
    "date_of_birth": [
        rf"{DOB_KWS_RGX}\s*[:\s!]*\s*([\d\s./-]+?)(?=\n\s*(?:{SEX_KWS_RGX}|{NAT_KWS_RGX})|$)"
    ],
    "gender": [
        rf"{SEX_KWS_RGX}\s*[:\s!]*\s*(Nam|Nữ|NAM|NỮ|Male|Female|N[aạA][mn])(?:\s|\.|$)"
    ],
    "nationality": [
        rf"{NAT_KWS_RGX}\s*[:\sV]*\s*([{VIETNAMESE_CHARS}\s.]+?)(?=\n\s*(?:{ORIGIN_KWS_RGX}|Dân tộc|{ETHNICITY_KWS_RGX})|$)"
    ],
    "place_of_origin": [
        rf"{ORIGIN_KWS_RGX}\s*[:\s]*\s*([\s\S]+?)(?=\n\s*(?:{RESIDENCE_KWS_RGX}|{ID_FEATURES_KWS_RGX}|{ETHNICITY_KWS_RGX})|\n\n|$)"
    ],
    "place_of_residence": [
        rf"{RESIDENCE_KWS_RGX}\s*[:\s]*\s*([\s\S]+?)(?=\n\s*(?:{ID_FEATURES_KWS_RGX}|{EXPIRY_KWS_RGX}|{ISSUE_DATE_KWS_RGX})|\n\n|$)"
    ],
    "expiry_date": [
        rf"{EXPIRY_KWS_RGX}\s*[:\s.]*\s*([\d\s./-]+|Không\s*thời\s*hạn|Vô\s*thời\s*hạn|KHH)(?:\s|\.|$)"
    ],
    "date_of_issue": [ 
        rf"(?:,\s*|,\n\s*|tại\s+)?{ISSUE_DATE_KWS_RGX}\s+(?P<day>\d{{1,2}})\s+(?:tháng|thang)\s+(?P<month>\d{{1,2}})\s+(?:năm|nam)\s+(?P<year>\d{{4}})"
    ],
    "place_of_issue": [
        (rf"{ISSUE_PLACE_KWS_RGX}\s*[:\s]*\s*([^{{\n}}]+?)(?=\n\s*(?:GIÁM ĐỐC|CỤC TRƯỞNG|TRUNG TÁ|CHỦ TỊCH)|$)", 1),
        (r"(?:GIÁM ĐỐC|CỤC TRƯỞNG)\s*(?:CÔNG AN|CA|C[SṢ]|CẢNH SÁT)\s*(?:TỈNH|THÀNH PHỐ|TP\.|T\.)\s*([{VIETNAMESE_CHARS}\s]+)", 1),
        (rf"(CỤC\s*(?:TRƯỞNG\s+CỤC\s+)?CẢNH SÁT\s*(?:QUẢN LÝ HÀNH CHÍNH VỀ TRẬT TỰ XÃ HỘI|QLHC VỀ TTXH|ĐKQL CƯ TRÚ VÀ DLQG VỀ DÂN CƯ|CS QLHC VỀ TTXH|ĐKQL CƯ TRÚ))", 1) 
    ],
    "personal_identification_features": [
        rf"{ID_FEATURES_KWS_RGX}\s*[:\s]*\s*([\s\S]+?)(?=\n\s*(?:{ISSUE_DATE_KWS_RGX}|{EXPIRY_KWS_RGX}|{ISSUE_PLACE_KWS_RGX}|GIÁM ĐỐC|CỤC TRƯỞNG|CHỦ TỊCH)|$)"
    ],
    "ethnicity": [
        rf"{ETHNICITY_KWS_RGX}\s*[:\s]*\s*([{VIETNAMESE_CHARS}\s]+?)(?=\n\s*(?:{RELIGION_KWS_RGX}|{ORIGIN_KWS_RGX})|$)"
    ],
    "religion": [
        rf"{RELIGION_KWS_RGX}\s*[:\s]*\s*([{VIETNAMESE_CHARS}\s]+?)(?=\n|$)" 
    ]
}

async def extract_with_gemini(ocr_text: str, fields_to_extract: List[str]) -> Optional[Dict[str, Any]]:
    global IS_GEMINI_CONFIGURED
    if not IS_GEMINI_CONFIGURED:
        return {"error_gemini_not_configured": "Gemini API Key not configured or invalid."}

    try:
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        prompt = f"""
        Nhiệm vụ: Trích xuất thông tin từ văn bản OCR của một giấy tờ tùy thân Việt Nam (CCCD/CMND).
        Văn bản OCR:
        ---
        {ocr_text}
        ---
        Yêu cầu:
        1. Trích xuất các trường thông tin sau: {', '.join(fields_to_extract)}.
        2. Trả về kết quả dưới dạng một đối tượng JSON duy nhất.
        3. Nếu không tìm thấy thông tin cho một trường, giá trị của trường đó phải là `null` (không phải chuỗi "null").
        4. Định dạng ngày tháng (dd/mm/yyyy).
        5. Viết HOA toàn bộ tên người.
        6. Loại bỏ mọi khoảng trắng khỏi Số CCCD/CMND.
        7. Đối với quê quán và nơi thường trú, cố gắng lấy địa chỉ đầy đủ nhất có thể.
        8. Chỉ trả về đối tượng JSON, không có bất kỳ giải thích hay ký tự ```json ``` nào bao quanh.

        Ví dụ JSON (chỉ là cấu trúc, giá trị sẽ phụ thuộc vào văn bản OCR):
        {{
          "id_number": "012345678912",
          "full_name": "NGUYỄN VĂN A",
          "date_of_birth": "01/01/1990",
          "gender": "Nam",
          "nationality": "Việt Nam",
          "place_of_origin": "Xã X, Huyện Y, Tỉnh Z",
          "place_of_residence": "Số nhà A, Đường B, Phường C, Quận D, Thành phố E",
          "expiry_date": "01/01/2030",
          "date_of_issue": "15/07/2015",
          "place_of_issue": "CỤC CẢNH SÁT QLHC VỀ TTXH",
          "personal_identification_features": "Nốt ruồi cách đuôi mắt trái 1cm",
          "ethnicity": "Kinh"
        }}
        """
        
        response = await model.generate_content_async(prompt)
        json_text = response.text
        try:
            gemini_result = json.loads(json_text)
            return gemini_result
        except json.JSONDecodeError:
            match = re.search(r"```json\s*([\s\S]+?)\s*```", json_text)
            if match:
                json_text_from_markdown = match.group(1)
                try:
                    gemini_result = json.loads(json_text_from_markdown)
                    return gemini_result
                except json.JSONDecodeError as e_markdown:
                    return {"error_gemini_json_decode": str(e_markdown), "gemini_raw_text": json_text}
            else:
                return {"error_gemini_no_json_found": "No JSON block found or direct parse failed", "gemini_raw_text": json_text}
    except Exception as e:
        return {"error_gemini_api_call": f"{type(e).__name__}: {str(e)}"}

@app.post("/extract_info/", response_model=ExtractedInfo, tags=["Extraction"])
async def extract_information_from_ocr(ocr_input: OCRInput = Body(...)):
    original_text = ocr_input.ocr_text
    text_to_process = clean_text_before_extraction(original_text)
    
    extracted_data_regex: Dict[str, Any] = {"raw_input": original_text, "extraction_method": "regex"}
    current_errors_regex: List[Dict[str, str]] = []

    for field_key, config in KEYWORD_CONFIG.items():
        patterns_for_field = EXTRACTION_PATTERNS.get(field_key, [])
        post_processor = config.get("post_process")
        value = None
        if field_key == "date_of_issue": 
            if EXTRACTION_PATTERNS["date_of_issue"]: 
                issue_date_match = re.search(EXTRACTION_PATTERNS["date_of_issue"][0], text_to_process, re.IGNORECASE)
                if issue_date_match:
                    try:
                        day = issue_date_match.group("day")
                        month = issue_date_match.group("month")
                        year = issue_date_match.group("year")
                        temp_date_str = f"{day}/{month}/{year}"
                        if post_processor: value = post_processor(temp_date_str, field_key)
                    except (IndexError, AttributeError): pass
        elif patterns_for_field:
            value = extract_single_field_from_patterns(patterns_for_field, text_to_process, field_key, post_process_func=post_processor)
        extracted_data_regex[field_key] = value

    key_fields_present_regex = all([
        extracted_data_regex.get("id_number"),
        extracted_data_regex.get("full_name"),
        extracted_data_regex.get("date_of_birth")
    ])

    if ocr_input.use_gemini_fallback and not key_fields_present_regex and IS_GEMINI_CONFIGURED:
        fields_to_request_from_gemini = list(KEYWORD_CONFIG.keys()) 
        gemini_result = await extract_with_gemini(original_text, fields_to_request_from_gemini) 
        
        if gemini_result and not any(k.startswith("error_gemini") for k in gemini_result):
            extracted_data_regex["extraction_method"] = "hybrid_gemini_fallback"
            for field_key in fields_to_request_from_gemini:
                gemini_value = gemini_result.get(field_key)
                post_processor_for_gemini = KEYWORD_CONFIG.get(field_key, {}).get("post_process")
                if post_processor_for_gemini and gemini_value is not None:
                    processed_gemini_value = post_processor_for_gemini(str(gemini_value), field_key) 
                    extracted_data_regex[field_key] = processed_gemini_value
                elif gemini_value is not None: 
                    extracted_data_regex[field_key] = general_field_cleaner(str(gemini_value), field_key)
                elif extracted_data_regex.get(field_key) is None and gemini_value is None:
                     extracted_data_regex[field_key] = None
    
    if not extracted_data_regex.get("id_number"):
        current_errors_regex.append({"field": "id_number", "message": "Không thể trích xuất Số CCCD/CMND."})
    if not extracted_data_regex.get("full_name"):
        current_errors_regex.append({"field": "full_name", "message": "Không thể trích xuất Họ và tên."})
    if not extracted_data_regex.get("date_of_birth"):
        current_errors_regex.append({"field": "date_of_birth", "message": "Không thể trích xuất Ngày sinh."})
    
    if current_errors_regex:
        extracted_data_regex["errors"] = current_errors_regex
    elif "errors" in extracted_data_regex and not current_errors_regex :
         del extracted_data_regex["errors"]

    return ExtractedInfo(**extracted_data_regex)

@app.get("/health", status_code=status.HTTP_200_OK, tags=["Health"])
async def health_check():
    return {"status": "healthy", "message": "eKYC Information Extraction Service (Hybrid) is running!"}