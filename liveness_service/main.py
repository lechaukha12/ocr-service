from fastapi import FastAPI, UploadFile, File
import random

app = FastAPI(title="Liveness Service")

@app.post("/check_liveness/")
def check_liveness(file: UploadFile = File(...)):
    # Demo: random kết quả, thực tế cần tích hợp model liveness
    is_live = random.choice([True, False])
    score = random.uniform(0.7, 0.99) if is_live else random.uniform(0.0, 0.3)
    return {"is_live": is_live, "score": score}
