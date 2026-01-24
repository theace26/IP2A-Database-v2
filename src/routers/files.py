from fastapi import APIRouter, UploadFile, File
import os
from datetime import datetime

router = APIRouter(prefix="/files", tags=["files"])

UPLOAD_DIR = "uploads_data"

os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    file_name = f"{timestamp}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, file_name)

    with open(file_path, "wb") as f:
        f.write(await file.read())

    return {
        "file_name": file_name,
        "file_path": file_path,
        "content_type": file.content_type,
    }
