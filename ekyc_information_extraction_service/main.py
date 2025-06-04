from fastapi import FastAPI, HTTPException, status, Body
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List, Callable
import re
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="eKYC Information Extraction Service (Regex-Only)")

VIETNAMESE_UPPER_CHARS = "A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ"
VIETNAMESE_LOWER_CHARS = "a-zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ"
DIGITS = "0-9"
SPACE_CHAR = " " 

NAME_CHARS_FOR_REGEX_SET = VIETNAMESE_UPPER_CHARS + VIETNAMESE_LOWER_CHARS + "'.`" + SPACE_CHAR + "-"

ADDRESS_CHARS_FOR_REGEX_SET = VIETNAMESE_UPPER_CHARS + VIETNAMESE_LOWER_CHARS + DIGITS + ".,/:()" + SPACE_CHAR + "\\-"
ID_NUMBER_CHARS_FOR_REGEX_SET = DIGITS + SPACE_CHAR 

class OCRInput(BaseModel):
    ocr_text: str = Field(..., example="Số/NG: 060098002136\nHọ và tên/Full name: LÊ CHÂU KHẢ\n...")
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
    extraction_method: str = "regex" 
    message: Optional[str] = None

ID_KEYWORDS = [
    r"Số", r"SỐ", r"No\.", r"SỐ/NO\.", r"Số/N[Gg]", r"SỐ/NG", r"Số / No\.?" 
    r"SỐ CCCD", r"Số CCCD", r"CCCD", r"Số CMND", r"CMND",
    r"S[oôỔ0]\s*:", r"S[oôỔ0]\s*CCCD\s*:", r"S[oôỔ0]\s*CMND\s*:"
]
NAME_KEYWORDS = [
    r"Họ và tên / Full name", 
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
    r"Nơi thường trú", r"NƠI THƯỜNG TRÚ", r"Nơi ĐKHK thường trú", r"Nơi thường trú\s*I\s*Place of residence\.?", 
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
    logger.warning(f"ID number '{id_num}' after cleaning is not 9 or 12 digits for field '{field_name}'.")
    return None

def post_process_name(name: Optional[str], field_name: str) -> Optional[str]:
    if not name: return None
    name = name.replace('\n', ' ').strip() 
    name = re.sub(rf"^[^{NAME_CHARS_FOR_REGEX_SET}]+|[^{NAME_CHARS_FOR_REGEX_SET}]+$", "", name, flags=re.IGNORECASE | re.UNICODE).strip()
    name = re.sub(r'\s+', ' ', name).strip() 
    name = re.sub(r'[.!`]+$', '', name).strip() 
    name = name.upper() 
    return name if len(name) > 1 else None

def normalize_date_string(date_str: Optional[str], field_name: str = "") -> Optional[str]:
    if not date_str: return None
    date_str = date_str.strip()
    if field_name == "expiry_date" and re.search(r"Không\s*(?:thời)?\s*hạn|Vô\s*thời\s*hạn|KHH", date_str, re.IGNORECASE):
        return "Không thời hạn"
    cleaned_date = re.sub(r'[.\s-]+', '/', date_str) 
    cleaned_date = re.sub(r'[^0-9/]', '', cleaned_date) 
    match = re.match(r'(\d{1,2})/(\d{1,2})/(\d{4})', cleaned_date)
    if match:
        day, month, year = match.groups()
        try:
            d_int, m_int, y_int = int(day), int(month), int(year)
            if not (1 <= m_int <= 12 and 1 <= d_int <= 31 and 1900 <= y_int <= 2100): 
                logger.warning(f"Date '{date_str}' for field '{field_name}' is out of valid range after normalization to {day}/{month}/{year}.")
                return None
        except ValueError: 
            logger.warning(f"Date '{date_str}' for field '{field_name}' contains non-integer parts after normalization to {day}/{month}/{year}.")
            return None
        return f"{day.zfill(2)}/{month.zfill(2)}/{year}" 
    logger.warning(f"Date '{date_str}' for field '{field_name}' could not be normalized to dd/mm/yyyy format.")
    return None

def post_process_address(address: Optional[str], field_name: str) -> Optional[str]:
    if not address: return None
    address = re.sub(r"^\s*[Il]\s+", "", address).strip() 
    keywords_to_remove_rgx_str = KEYWORD_CONFIG.get(field_name, {}).get("keywords_rgx_for_cleaning", "")
    if keywords_to_remove_rgx_str:
        pattern_to_remove = rf"^\s*(?:{keywords_to_remove_rgx_str})\s*(?:[:.\sƒlÍ]+|\n)?\s*"
        address = re.sub(pattern_to_remove, "", address, count=1, flags=re.IGNORECASE | re.UNICODE).strip()
    address = general_field_cleaner(address, field_name) 
    address = re.sub(r'\s*-\s*¬\s*$', '', address).strip() 
    address = re.sub(r'\s*\^s*$', '', address).strip()
    address = re.sub(r'\s*a_—ẴẮ`\s*_—\.\s*r3\s*l\s*mẽ\s*$', '', address, flags=re.IGNORECASE).strip()
    return address

def extract_single_field_from_patterns(
    patterns: List[Any], text: str, field_name: str,
    default_group_index: int = 1,
    flags=re.IGNORECASE | re.DOTALL | re.UNICODE, 
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
            logger.warning(f"Invalid pattern spec for field {field_name}: {pattern_spec}")
            continue

        try:
            # Biên dịch regex một lần để kiểm tra cú pháp trước khi search
            compiled_regex = re.compile(current_pattern, flags)
            match = compiled_regex.search(text)
            # match = re.search(current_pattern, text, flags) # Dòng cũ
            if match:
                value = match.group(current_group_index)
                if value is not None:
                    value = value.replace('\n', ' ').strip() 
                    if post_process_func:
                        value = post_process_func(value, field_name) 
                    else: 
                        value = general_field_cleaner(value, field_name) 
                    
                    if value: 
                        logger.debug(f"Field '{field_name}' extracted with pattern '{str(current_pattern)[:50]}...': '{value[:50]}...'")
                        return value
        except IndexError:
            logger.warning(f"IndexError for field {field_name} with pattern '{str(current_pattern)[:50]}...' and group index {current_group_index}.")
            continue
        except re.error as e: 
            logger.error(f"Regex compilation/matching error for field '{field_name}' with pattern '{str(current_pattern)[:100]}...': {e}")
            continue # Bỏ qua pattern này và thử pattern tiếp theo nếu có
    return None

KEYWORD_CONFIG: Dict[str, Dict[str, Any]] = {
    "id_number": {"keywords_rgx_for_cleaning": ID_KWS_RGX, "post_process": post_process_id_number},
    "full_name": {"keywords_rgx_for_cleaning": NAME_KWS_RGX, "post_process": post_process_name},
    "date_of_birth": {"keywords_rgx_for_cleaning": DOB_KWS_RGX, "post_process": normalize_date_string},
    "gender": {"keywords_rgx_for_cleaning": SEX_KWS_RGX, "post_process": general_field_cleaner}, 
    "nationality": {"keywords_rgx_for_cleaning": NAT_KWS_RGX, "post_process": post_process_address}, 
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
        rf"{ID_KWS_RGX}\s*[:.]?\s*([{ID_NUMBER_CHARS_FOR_REGEX_SET}]{{10,18}})", 
        (r"(?:\n|^)\s*([0-9\s]{11}[0-9])\s*(?:\n|$)", 1),
        (r"(?:\n|^)\s*([0-9\s]{8}[0-9])\s*(?:\n|$)", 1)
    ],
    "full_name": [
        # Pattern 1: Chuẩn nhất, có cả tiếng Việt và tiếng Anh, có thể có dấu : hoặc không, có thể xuống dòng hoặc không
        rf"(?:{NAME_KWS_RGX})\s*[:：]?\s*(?:\n)?\s*([A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐa-zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ'`.\- ]{{3,}})",
        # Pattern 2: fallback, lấy dòng sau dòng chứa từ khóa tên
        rf"(?:{NAME_KWS_RGX})[^\n]*\n([A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐa-zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ'`.\- ]{{3,}})",
        # Pattern 3: fallback, lấy tên ở đầu dòng nếu không có từ khóa
        r"^(?:[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ][a-zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ'`.\- ]{3,})$"
    ],
    "date_of_birth": [
        rf"{DOB_KWS_RGX}\s*[:!\s]?\s*([\d\s./-]+?)(?=\n\s*(?:{SEX_KWS_RGX}|{NAT_KWS_RGX})|$)"
    ],
    "gender": [
        rf"{SEX_KWS_RGX}\s*[:!\s]?\s*(Nam|Nữ|NAM|NỮ|Male|Female|N[aạA][mn])(?:\s|\.|$|\n)"
    ],
    "nationality": [
        rf"{NAT_KWS_RGX}(?:\s*[:./\sV])?\s*([\s\S]+?)(?=\n\s*(?:{ORIGIN_KWS_RGX}|Dân tộc|{ETHNICITY_KWS_RGX})|$)"
    ],
    "place_of_origin": [
        rf"{ORIGIN_KWS_RGX}(?:\s*[:./\s])?\s*([\s\S]+?)(?=\n\s*(?:{RESIDENCE_KWS_RGX}|{ID_FEATURES_KWS_RGX}|{ETHNICITY_KWS_RGX})|\n\n|$)"
    ],
    "place_of_residence": [
        rf"{RESIDENCE_KWS_RGX}(?:\s*[:./\s])?\s*([\s\S]+?)(?=\n\s*(?:{ID_FEATURES_KWS_RGX}|{EXPIRY_KWS_RGX}|{ISSUE_DATE_KWS_RGX})|\n\n|$)"
    ],
    "expiry_date": [
        rf"{EXPIRY_KWS_RGX}\s*[:.\s]?\s*([\d\s./-]+|Không\s*thời\s*hạn|Vô\s*thời\s*hạn|KHH)(?:\s|\.|$|\n)"
    ],
    "date_of_issue": [ 
        rf"(?:,\s*|,\n\s*|tại\s+)?{ISSUE_DATE_KWS_RGX}\s+(?P<day>\d{{1,2}})\s+(?:tháng|thang)\s+(?P<month>\d{{1,2}})\s+(?:năm|nam)\s+(?P<year>\d{{4}})"
    ],
    "place_of_issue": [
        (rf"{ISSUE_PLACE_KWS_RGX}\s*[:\s]?\s*([^{{\n}}]+?)(?=\n\s*(?:GIÁM ĐỐC|CỤC TRƯỞNG|TRUNG TÁ|CHỦ TỊCH)|$)", 1),
    ],
    "personal_identification_features": [
        rf"{ID_FEATURES_KWS_RGX}\s*[:\s]?\s*([\s\S]+?)(?=\n\s*(?:{ISSUE_DATE_KWS_RGX}|{EXPIRY_KWS_RGX}|{ISSUE_PLACE_KWS_RGX}|GIÁM ĐỐC|CỤC TRƯỞNG|CHỦ TỊCH)|$)"
    ],
    "ethnicity": [ 
        rf"{ETHNICITY_KWS_RGX}\s*[:\s]?\s*([{VIETNAMESE_UPPER_CHARS}{VIETNAMESE_LOWER_CHARS}\s]+?)(?=\n\s*(?:{RELIGION_KWS_RGX}|{ORIGIN_KWS_RGX})|$)"
    ],
    "religion": [ 
        rf"{RELIGION_KWS_RGX}\s*[:\s]?\s*([{VIETNAMESE_UPPER_CHARS}{VIETNAMESE_LOWER_CHARS}\s]+?)(?=\n|$)"
    ]
}

@app.post("/extract_info/", response_model=ExtractedInfo, tags=["Extraction"])
async def extract_information_from_ocr(ocr_input: OCRInput = Body(...)):
    original_text = ocr_input.ocr_text
    logger.info(f"Received OCR text for extraction (length: {len(original_text)} chars).")
    logger.debug(f"Raw OCR text: {original_text[:500]}...") 

    text_to_process = clean_text_before_extraction(original_text)
    logger.debug(f"Cleaned OCR text: {text_to_process[:500]}...")
    
    general_message = None
    alphanumeric_chars_count = len(re.sub(r'[^a-zA-Z0-9]', '', original_text))
    if alphanumeric_chars_count < 20: 
        general_message = "Văn bản OCR đầu vào có vẻ quá ngắn hoặc chất lượng quá thấp để trích xuất thông tin đáng tin cậy."
        logger.warning(general_message)

    extracted_data: Dict[str, Any] = {"raw_input": original_text, "extraction_method": "regex"}
    
    for field_key, config in KEYWORD_CONFIG.items():
        patterns_for_field = EXTRACTION_PATTERNS.get(field_key, [])
        post_processor = config.get("post_process")
        value = None
        
        if field_key == "date_of_issue": 
            if EXTRACTION_PATTERNS["date_of_issue"]:
                issue_date_match = re.search(EXTRACTION_PATTERNS["date_of_issue"][0], text_to_process, re.IGNORECASE | re.UNICODE)
                if issue_date_match:
                    try:
                        day = issue_date_match.group("day")
                        month = issue_date_match.group("month")
                        year = issue_date_match.group("year")
                        temp_date_str = f"{day}/{month}/{year}"
                        if post_processor: value = post_processor(temp_date_str, field_key)
                    except (IndexError, AttributeError): 
                        logger.warning(f"Could not parse groups for date_of_issue with pattern: {EXTRACTION_PATTERNS['date_of_issue'][0]}")
                        pass 
        elif patterns_for_field:
            value = extract_single_field_from_patterns(patterns_for_field, text_to_process, field_key, post_process_func=post_processor)
        
        extracted_data[field_key] = value
        if value:
            logger.info(f"Extracted '{field_key}': '{str(value)[:100]}'")
        else:
            expected_fields_on_cccd_front = ["id_number", "full_name", "date_of_birth", "gender", "nationality", "place_of_origin", "place_of_residence", "expiry_date"]
            if field_key in expected_fields_on_cccd_front:
                logger.warning(f"Could not extract expected field '{field_key}' using regex.")
            else:
                logger.info(f"Field '{field_key}' not typically on CCCD front or not extracted by regex.")


    current_errors: List[Dict[str, str]] = []
    if not extracted_data.get("id_number"):
        current_errors.append({"field": "id_number", "message": "Không thể trích xuất Số CCCD/CMND bằng Regex."})
    if not extracted_data.get("full_name"):
        current_errors.append({"field": "full_name", "message": "Không thể trích xuất Họ và tên bằng Regex."})
    if not extracted_data.get("date_of_birth"):
        current_errors.append({"field": "date_of_birth", "message": "Không thể trích xuất Ngày sinh bằng Regex."})

    if current_errors:
        extracted_data["errors"] = current_errors
    
    if general_message: 
        extracted_data["message"] = general_message
    
    logger.info(f"Final extracted data (Regex-only): { {k:v for k,v in extracted_data.items() if k != 'raw_input'} }")
    return ExtractedInfo(**extracted_data)

@app.get("/health", status_code=status.HTTP_200_OK, tags=["Health"])
async def health_check():
    return {"status": "healthy", "message": "eKYC Information Extraction Service (Regex-Only) is running!"}
