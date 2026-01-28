import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.db import get_db
from backend.models import File

router = APIRouter(prefix="/download", tags=["Download"])

FILES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "storage", "files")


@router.get("/{file_id}")
def download_file(file_id: str, db: Session = Depends(get_db)):
    file_obj = db.query(File).filter_by(file_id=file_id).first()
    if not file_obj:
        raise HTTPException(404, "Invalid file_id")

    if file_obj.status != "completed":
        raise HTTPException(400, "File not completed yet")

    file_path = os.path.join(FILES_DIR, f"{file_obj.file_id}_{file_obj.filename}")
    if not os.path.exists(file_path):
        raise HTTPException(404, "Merged file missing")

    return FileResponse(file_path, filename=file_obj.filename, media_type="application/octet-stream")
