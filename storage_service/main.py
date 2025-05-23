import shutil
import uuid
from pathlib import Path
from typing import List

import aiofiles
from fastapi import FastAPI, File, UploadFile, HTTPException, status, Form
from fastapi.responses import JSONResponse, FileResponse

# Sửa import tương đối thành tuyệt đối
from config import settings # Thay vì from .config import settings

app = FastAPI(title="Storage Service")

UPLOAD_DIR = Path(settings.UPLOAD_DIR)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True) # Đảm bảo thư mục upload tồn tại

@app.post("/upload/file/", response_model=dict, tags=["File Upload"])
async def upload_single_file(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file name provided.")

    original_filename = file.filename
    file_extension = Path(original_filename).suffix
    
    # Tạo tên file duy nhất để tránh ghi đè
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_location = UPLOAD_DIR / unique_filename

    try:
        async with aiofiles.open(file_location, "wb") as out_file:
            while content := await file.read(1024 * 1024): # Đọc từng chunk 1MB
                await out_file.write(content)
    except Exception as e:
        # Nếu có lỗi, cố gắng xóa file đã tạo (nếu có) để tránh file rác
        if file_location.exists():
            try:
                file_location.unlink()
            except Exception as unlink_e:
                # Ghi log lỗi xóa file nếu cần
                # print(f"Error unlinking file {file_location} after upload error: {unlink_e}")
                pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"There was an error uploading the file: {str(e)}",
        )
    finally:
        await file.close() # Luôn đóng file sau khi xử lý

    return {
        "message": "File uploaded successfully",
        "filename": unique_filename, # Trả về tên file đã lưu trên server
        "original_filename": original_filename,
        "content_type": file.content_type,
        "file_path": str(file_location) # Đường dẫn tuyệt đối trên server (chủ yếu để debug)
    }

@app.post("/upload/files/", response_model=List[dict], tags=["File Upload"])
async def upload_multiple_files(files: List[UploadFile] = File(...)):
    results = []
    for file in files:
        if not file.filename:
            results.append({
                "error": "No file name provided for one of the files.",
                "original_filename": "unknown"
            })
            continue # Bỏ qua file này và xử lý file tiếp theo

        original_filename = file.filename
        file_extension = Path(original_filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_location = UPLOAD_DIR / unique_filename

        try:
            async with aiofiles.open(file_location, "wb") as out_file:
                while content := await file.read(1024 * 1024):
                    await out_file.write(content)
            
            results.append({
                "message": "File uploaded successfully",
                "filename": unique_filename,
                "original_filename": original_filename,
                "content_type": file.content_type,
                "file_path": str(file_location)
            })
        except Exception as e:
            if file_location.exists():
                try:
                    file_location.unlink()
                except Exception:
                    pass
            results.append({
                "error": f"Error uploading {original_filename}: {str(e)}",
                "original_filename": original_filename
            })
        finally:
            await file.close()
            
    return results


@app.get("/files/{filename}", tags=["File Access"])
async def get_file(filename: str):
    # Validate filename để tránh traversal attack (mặc dù Path() cũng có một số bảo vệ)
    if ".." in filename or filename.startswith("/"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid filename.")

    file_location = UPLOAD_DIR / filename
    if not file_location.is_file(): # Kiểm tra file có tồn tại và là file không
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    
    # Trả về file, trình duyệt sẽ tự xử lý việc hiển thị hoặc tải xuống dựa trên content type
    return FileResponse(path=file_location, filename=filename) # filename giúp gợi ý tên khi tải xuống
