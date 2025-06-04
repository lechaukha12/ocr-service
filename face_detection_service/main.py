from fastapi import FastAPI, UploadFile, File
from typing import List
import numpy as np
from PIL import Image
import io
import face_recognition

app = FastAPI(title="Face Detection Service")

@app.post("/detect_faces/")
def detect_faces(file: UploadFile = File(...)):
    image_bytes = file.file.read()
    image = face_recognition.load_image_file(io.BytesIO(image_bytes))
    face_locations = face_recognition.face_locations(image)
    results = []
    for top, right, bottom, left in face_locations:
        results.append({"top": top, "right": right, "bottom": bottom, "left": left})
    return {"num_faces": len(face_locations), "faces": results}
