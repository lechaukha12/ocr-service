from fastapi import FastAPI, UploadFile, File
import numpy as np
import face_recognition
import io

app = FastAPI(title="Face Comparison Service")

@app.post("/compare_faces/")
def compare_faces(file1: UploadFile = File(...), file2: UploadFile = File(...)):
    img1 = face_recognition.load_image_file(io.BytesIO(file1.file.read()))
    img2 = face_recognition.load_image_file(io.BytesIO(file2.file.read()))
    encodings1 = face_recognition.face_encodings(img1)
    encodings2 = face_recognition.face_encodings(img2)
    if not encodings1 or not encodings2:
        return {"match": False, "score": 0.0, "threshold": 0.4, "message": "Không tìm thấy khuôn mặt trong một hoặc cả hai ảnh."}
    score = float(face_recognition.face_distance([encodings1[0]], encodings2[0])[0])
    threshold = 0.4
    match = score < threshold
    return {"match": match, "score": score, "threshold": threshold}
