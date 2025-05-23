import shutil
import uuid
from pathlib import Path
from typing import List

import aiofiles
from fastapi import FastAPI, File, UploadFile, HTTPException, status, Form
from fastapi.responses import JSONResponse, FileResponse
from .config import settings

app = FastAPI(title="Storage Service")

UPLOAD_DIR = Path(settings.UPLOAD_DIR)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@app.post("/upload/file/", response_model=dict, tags=["File Upload"])
async def upload_single_file(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file name provided.")

    original_filename = file.filename
    file_extension = Path(original_filename).suffix
    
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_location = UPLOAD_DIR / unique_filename

    try:
        async with aiofiles.open(file_location, "wb") as out_file:
            while content := await file.read(1024 * 1024):
                await out_file.write(content)
    except Exception as e:
        if file_location.exists():
            file_location.unlink(missing_ok=True) # missing_ok=True nếu file có thể đã bị xóa bởi tác nhân khác
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"There was an error uploading the file: {str(e)}",
        )
    finally:
        await file.close()

    return {
        "message": "File uploaded successfully",
        "filename": unique_filename,
        "original_filename": original_filename,
        "content_type": file.content_type,
        "file_path": str(file_location) # Đã sửa: dùng str(file_location) trực tiếp
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
            continue

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
                "file_path": str(file_location) # Đã sửa: dùng str(file_location) trực tiếp
            })
        except Exception as e:
            if file_location.exists():
                file_location.unlink(missing_ok=True)
            results.append({
                "error": f"Error uploading {original_filename}: {str(e)}",
                "original_filename": original_filename
            })
        finally:
            await file.close()
            
    return results


@app.get("/files/{filename}", tags=["File Access"])
async def get_file(filename: str):
    file_location = UPLOAD_DIR / filename
    if not file_location.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    
    return FileResponse(path=file_location, filename=filename)

