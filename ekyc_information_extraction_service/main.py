from fastapi import FastAPI, HTTPException, status, Body
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import re

app = FastAPI(title="eKYC Information Extraction Service")

class OCRInput(BaseModel):
    ocr_text: str = Field(..., example="Số: 012345678910\nHọ và tên: NGUYỄN VĂN A\nNgày sinh: 01/01/1990\nGiới tính: Nam Quốc tịch: Việt Nam\nQuê quán: Xã B, Huyện C, Tỉnh D\nNơi thường trú: Số nhà X, đường Y, Phường Z, Quận W, TP V\nCó giá trị đến: 01/01/2030\nĐặc điểm nhận dạng:...\nngày 15 tháng 07 năm 2015\nGIÁM ĐỐC CÔNG AN TỈNH K")
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
    raw_input: str
    errors: Optional[list[str]] = None


def extract_single_field(pattern: str, text: str, field_name: str, group_index: int = 1, flags=re.IGNORECASE | re.DOTALL) -> Optional[str]:
    match = re.search(pattern, text, flags)
    if match:
        try:
            # Loại bỏ khoảng trắng thừa và các ký tự không mong muốn ở đầu/cuối
            value = match.group(group_index).strip(' \t\n\r,:;')
            return value if value else None
        except IndexError:
            return None
    return None

@app.post("/extract_info/", response_model=ExtractedInfo, tags=["Extraction"])
async def extract_information_from_ocr(ocr_input: OCRInput = Body(...)):
    text = ocr_input.ocr_text
    errors = []

    # Số CCCD/CMND
    id_number = extract_single_field(r"(?:Số/No\.|Số)\s*[:\s]*(\d{12}(?!\d))", text, "id_number") # Ưu tiên 12 số
    if not id_number:
        id_number = extract_single_field(r"(?:Số/No\.|Số)\s*[:\s]*(\d{9}(?!\d))", text, "id_number") # Thử 9 số
    if not id_number: # Thử tìm số đứng một mình nếu các mẫu trên thất bại (ít chính xác hơn)
         id_number = extract_single_field(r"^(?:\D*\n)?\s*(\d{12}(?!\d))\s*$", text, "id_number", flags=re.IGNORECASE | re.MULTILINE)
         if not id_number:
             id_number = extract_single_field(r"^(?:\D*\n)?\s*(\d{9}(?!\d))\s*$", text, "id_number", flags=re.IGNORECASE | re.MULTILINE)

    # Họ và tên
    full_name = extract_single_field(r"(?:Họ và tên|Họ tên|Full name)\s*[:\s]*(.+?)(?=\n(?:Ngày sinh|Date of birth|Giới tính|Sex)|$)", text, "full_name")
    if full_name: # Chuyển thành chữ hoa nếu cần chuẩn hóa
        full_name = full_name.upper()
    
    # Ngày sinh
    date_of_birth = extract_single_field(r"(?:Ngày sinh|Date of birth)\s*[:\s]*(\d{1,2}[/\.\s\-]\d{1,2}[/\.\s\-]\d{4})", text, "date_of_birth")
    
    # Giới tính
    gender = extract_single_field(r"(?:Giới tính|Sex)\s*[:\s]*(Nam|Nữ|Male|Female)", text, "gender")
    
    # Quốc tịch
    nationality = extract_single_field(r"(?:Quốc tịch|Nationality)\s*[:\s]*(.+?)(?=\n(?:Quê quán|Place of origin|Dân tộc)|$)", text, "nationality")
    
    # Quê quán
    place_of_origin = extract_single_field(r"(?:Quê quán|Place of origin)\s*[:\s]*(.+?)(?=\n(?:Nơi thường trú|Place of residence|Đặc điểm nhận dạng)|$)", text, "place_of_origin")
    
    # Nơi thường trú
    place_of_residence = extract_single_field(r"(?:Nơi thường trú|Place of residence)\s*[:\s]*(.+?)(?=\n(?:Đặc điểm nhận dạng|Có giá trị đến|Date of expiry)|$)", text, "place_of_residence")

    # Ngày hết hạn
    expiry_date = extract_single_field(r"(?:Có giá trị đến|Date of expiry)\s*[:\s]*(\d{1,2}[/\.\s\-]\d{1,2}[/\.\s\-]\d{4}|Không thời hạn|Vô thời hạn)", text, "expiry_date")

    # Ngày cấp (thường ở mặt sau hoặc cuối mặt trước)
    # Cố gắng tìm "ngày dd tháng mm năm yyyy"
    date_of_issue_match = re.search(r"ngày\s*(\d{1,2})\s*tháng\s*(\d{1,2})\s*năm\s*(\d{4})", text, re.IGNORECASE)
    date_of_issue = None
    if date_of_issue_match:
        try:
            day = date_of_issue_match.group(1).zfill(2)
            month = date_of_issue_match.group(2).zfill(2)
            year = date_of_issue_match.group(3)
            date_of_issue = f"{day}/{month}/{year}"
        except IndexError:
            pass
    
    # Nơi cấp (thường ở mặt sau, liên quan đến cơ quan cấp)
    place_of_issue = extract_single_field(r"(?:Nơi cấp|Place of issue|TẠI)\s*[:\s]*(.+?)(?:\n|GIÁM ĐỐC|CỤC TRƯỞNG|TRUNG TÁ|$)", text, "place_of_issue")
    if not place_of_issue: # Thử một mẫu khác nếu không tìm thấy
        place_of_issue = extract_single_field(r"(?:GIÁM ĐỐC|CỤC TRƯỞNG)\s*(?:CÔNG AN|CA)\s*(?:TỈNH|THÀNH PHỐ|TP\.)\s*([A-ZÀ-Ỹ\s]+)", text, "place_of_issue", group_index=1)
        if not place_of_issue:
             place_of_issue = extract_single_field(r"CỤC CẢNH SÁT\s*(?:QUẢN LÝ HÀNH CHÍNH VỀ TRẬT TỰ XÃ HỘI|QLHC VỀ TTXH|ĐKQL CƯ TRÚ VÀ DLQG VỀ DÂN CƯ)", text, "place_of_issue", group_index=0)


    # Thu thập lỗi nếu một trường quan trọng không trích xuất được
    if not id_number:
        errors.append("Không thể trích xuất Số CCCD/CMND.")
    if not full_name:
        errors.append("Không thể trích xuất Họ và tên.")
    if not date_of_birth:
        errors.append("Không thể trích xuất Ngày sinh.")

    # Chuẩn hóa output, loại bỏ None để response gọn hơn nếu muốn, hoặc giữ None
    return ExtractedInfo(
        id_number=id_number,
        full_name=full_name,
        date_of_birth=date_of_birth,
        gender=gender,
        nationality=nationality,
        place_of_origin=place_of_origin.replace('\n', ' ').strip() if place_of_origin else None,
        place_of_residence=place_of_residence.replace('\n', ' ').strip() if place_of_residence else None,
        expiry_date=expiry_date,
        date_of_issue=date_of_issue,
        place_of_issue=place_of_issue.strip() if place_of_issue else None,
        raw_input=ocr_input.ocr_text,
        errors=errors if errors else None
    )

@app.get("/health", status_code=status.HTTP_200_OK, tags=["Health"])
async def health_check():
    return {"status": "healthy", "message": "eKYC Information Extraction Service is running!"}

