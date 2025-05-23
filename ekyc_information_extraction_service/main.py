from fastapi import FastAPI, HTTPException, status, Body
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

app = FastAPI(title="eKYC Information Extraction Service")

class OCRInput(BaseModel):
    ocr_text: str = Field(..., example="Họ và tên: Nguyễn Văn A\nNgày sinh: 01/01/1990\nSố CCCD: 012345678910")
    language: Optional[str] = Field("vie", example="vie")

class ExtractedInfo(BaseModel):
    full_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    id_number: Optional[str] = None
    address: Optional[str] = None
    # Thêm các trường khác nếu cần
    raw_input: str

@app.post("/extract_info/", response_model=ExtractedInfo, tags=["Extraction"])
async def extract_information_from_ocr(ocr_input: OCRInput = Body(...)):
    # Đây là nơi bạn sẽ triển khai logic trích xuất thông tin
    # Ví dụ sử dụng regex, NLP, etc.
    # Hiện tại, nó chỉ trả về một phần input để minh họa
    
    # Ví dụ đơn giản (cần được thay thế bằng logic thực tế)
    extracted_full_name = None
    if "Họ và tên:" in ocr_input.ocr_text:
        try:
            extracted_full_name = ocr_input.ocr_text.split("Họ và tên:")[1].split("\n")[0].strip()
        except IndexError:
            pass # Bỏ qua nếu không tìm thấy hoặc định dạng không đúng

    return ExtractedInfo(
        full_name=extracted_full_name,
        # Thêm logic cho các trường khác ở đây
        raw_input=ocr_input.ocr_text
    )

@app.get("/health", status_code=status.HTTP_200_OK, tags=["Health"])
async def health_check():
    return {"status": "healthy", "message": "eKYC Information Extraction Service is running!"}

