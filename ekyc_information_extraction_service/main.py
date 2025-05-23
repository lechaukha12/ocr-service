from fastapi import FastAPI, HTTPException, status, Body
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List, Callable
import re

app = FastAPI(title="eKYC Information Extraction Service")

# Define common Vietnamese characters for regex patterns
VIETNAMESE_CHARS = "A-ZÀ-ỹÁ-ỹẠ-ỹĂ-ỹẰ-ỹẲ-ỹẴ-ỹẶ-ỹÂ-ỹẦ-ỹẨ-ỹẪ-ỹẬ-ỹĐđÈ-ỹÉ-ỹẸ-ỹÊ-ỹỀ-ỹỂ-ỹỄ-ỹỆ-ỹÌ-ỹÍ-ỹỈ-ỹỊ-ỹÒ-ỹÓ-ỹỌ-ỹÔ-ỹỒ-ỹỔ-ỹỖ-ỹỘ-ỹƠ-ỹỜ-ỹỞ-ỹỠ-ỹỢ-ỹÙ-ỹÚ-ỹỦ-ỹŨ-ỹỤ-ỹƯ-ỹỪ-ỹỨ-ỹỬ-ỹỮ-ỹỰ-ỹỲ-ỹÝ-ỹỶ-ỹỸ-ỹỴ-ỹ"
NAME_ALLOWED_CHARS = f"{VIETNAMESE_CHARS}A-Z\\s'.`-" 
ADDRESS_ALLOWED_CHARS = f"{VIETNAMESE_CHARS}A-Z0-9\\s.,/-()" 
ID_NUMBER_CHARS = r"\d\s" 

class OCRInput(BaseModel):
    ocr_text: str = Field(..., example="Số/NG: 060088002136\nHọ và tên/Full name: LÊ CHÂU KHẢ\nNgày sinh/Date of birth: 12/04/1998\nGiới tính/Sex: Nam Quốc tịch/Nationality: Việt Nam\nQuê quán/Place of origin: Châu Thành, Long An\nNơi thường trú/Place of residence: Tổ 5, Phú Điền, Hàm Hiệp, Hàm Thuận Bắc, Bình Thuận\nCó giá trị đến/Date of expiry: 12/04/2038\nĐặc điểm nhận dạng: Nốt ruồi C.Trán P 2cm\nngày 15 tháng 07 năm 2015\nNơi cấp: CỤC TRƯỞNG CỤC CẢNH SÁT QLHC VỀ TTXH")
    language: Optional[str] = Field("vie", example="vie")

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
    text = re.sub(r'\s*\n\s*', '\n', text) # Normalize newlines
    text = re.sub(r' +', ' ', text) 
    # More targeted replacements based on observed OCR errors
    text = text.replace("Naionelt", "Nationality")
    text = text.replace("origlr", "origin")
    text = text.replace("residerce", "residence")
    text = text.replace("bifh", "birth")
    text = text.replace("Dafe", "Date")
    text = text.replace("ƒ", ":") # Common OCR error for colon
    text = text.replace("Í", ":")
    text = text.replace("l ", ": ") # "l " often means ": "
    return text.strip()

def general_field_cleaner(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
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
    name = re.sub(r'[.!`]+$', '', name).strip() # Remove trailing punctuation
    name = name.upper() 
    return name if len(name) > 1 else None # Allow single-letter names if that's the case

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
        except ValueError:
            return None 
        return f"{day.zfill(2)}/{month.zfill(2)}/{year}"
    return None

def post_process_address(address: Optional[str], field_name: str) -> Optional[str]:
    if not address: return None
    
    # Remove keyword labels if captured at the beginning more robustly
    keywords_rgx_to_remove = KEYWORD_CONFIG.get(field_name, {}).get("keywords_rgx_for_cleaning", "")
    if keywords_rgx_to_remove: # keywords_rgx_for_cleaning should be the same as keywords_rgx
        address = re.sub(rf"^\s*{keywords_rgx_to_remove}\s*[:\sƒlÍ.]*\s*", "", address, flags=re.IGNORECASE).strip()

    address = general_field_cleaner(address)
    # Remove common OCR artifacts at the end of addresses
    address = re.sub(r'\s*-\s*¬\s*$', '', address).strip()
    address = re.sub(r'\s*\^s*$', '', address).strip()
    address = re.sub(r'\s*a_—ẴẮ`\s*_—\.\s*r3\s*l\s*mẽ\s*$', '', address, flags=re.IGNORECASE).strip()
    return address

def extract_single_field_from_patterns(
    patterns: List[str], 
    text: str, 
    field_name: str, 
    group_index: int = 1, # Default group index
    flags=re.IGNORECASE | re.DOTALL, 
    post_process_func: Optional[Callable[[Optional[str], str], Optional[str]]] = None
) -> Optional[str]:
    for i, pattern_or_spec in enumerate(patterns):
        current_pattern = pattern_or_spec
        current_group_index = group_index # Use default unless specified
        
        if isinstance(pattern_or_spec, tuple): # Allow (pattern, group_index)
            current_pattern, current_group_index = pattern_or_spec

        match = re.search(current_pattern, text, flags)
        if match:
            try:
                value = match.group(current_group_index)
                if value is not None:
                    value = value.strip() 
                    if post_process_func:
                        value = post_process_func(value, field_name)
                    else: 
                        value = general_field_cleaner(value)
                    
                    return value if value else None 
            except IndexError:
                # This can happen if the group_index is out of bounds for the specific pattern that matched
                # print(f"IndexError for field {field_name}, pattern {i}, group {current_group_index}")
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
        rf"{ID_KWS_RGX}\s*[:\s.]*\s*((?:[{ID_NUMBER_CHARS}]{{10,18}}))", # More flexible length
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
        rf"{SEX_KWS_RGX}\s*[:\s!]*\s*(Nam|Nữ|NAM|NỮ|Male|Female|N[aạA][mn])(?:\s|\.|$)" # Added Narn/Naam
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

@app.post("/extract_info/", response_model=ExtractedInfo, tags=["Extraction"])
async def extract_information_from_ocr(ocr_input: OCRInput = Body(...)):
    original_text = ocr_input.ocr_text
    text_to_process = clean_text_before_extraction(original_text)
    
    extracted_data: Dict[str, Any] = {"raw_input": original_text}
    current_errors: List[Dict[str, str]] = []

    for field_key, config in KEYWORD_CONFIG.items():
        patterns_for_field = EXTRACTION_PATTERNS.get(field_key, [])
        post_processor = config.get("post_process")
        
        value = None
        if field_key == "date_of_issue": 
            issue_date_match = re.search(EXTRACTION_PATTERNS["date_of_issue"][0], text_to_process, re.IGNORECASE)
            if issue_date_match:
                try:
                    day = issue_date_match.group("day")
                    month = issue_date_match.group("month")
                    year = issue_date_match.group("year")
                    temp_date_str = f"{day}/{month}/{year}"
                    if post_processor:
                         value = post_processor(temp_date_str, field_key)
                except (IndexError, AttributeError):
                    pass
        elif patterns_for_field:
            value = extract_single_field_from_patterns(
                patterns_for_field, 
                text_to_process, 
                field_key,
                post_process_func=post_processor
            )
        
        extracted_data[field_key] = value

    # Post-extraction validation and cross-field checks (examples)
    if extracted_data.get("id_number") and extracted_data.get("full_name") and extracted_data.get("date_of_birth"):
        # All key fields found, potentially clear generic errors or add specific ones if values are still suspicious
        pass
    else:
        if not extracted_data.get("id_number"):
            current_errors.append({"field": "id_number", "message": "Không thể trích xuất Số CCCD/CMND."})
        if not extracted_data.get("full_name"):
            current_errors.append({"field": "full_name", "message": "Không thể trích xuất Họ và tên."})
        if not extracted_data.get("date_of_birth"):
            current_errors.append({"field": "date_of_birth", "message": "Không thể trích xuất Ngày sinh."})
    
    # Consolidate nationality if still messy
    if extracted_data.get("nationality") and not extracted_data["nationality"] == "Việt Nam":
        if re.search(r"Việt\s*Nam|Mật\s*Nam|VIET NAM", extracted_data["nationality"], re.IGNORECASE):
            extracted_data["nationality"] = "Việt Nam"
        # else keep it as is, or add error if it looks very wrong

    if current_errors:
        extracted_data["errors"] = current_errors

    return ExtractedInfo(**extracted_data)

@app.get("/health", status_code=status.HTTP_200_OK, tags=["Health"])
async def health_check():
    return {"status": "healthy", "message": "eKYC Information Extraction Service is running!"}

