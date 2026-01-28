import os
import shutil

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.db import get_db
from backend.models import File, Chunk, ShareLink

router = APIRouter(prefix="/files", tags=["Delete"])

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STORAGE_DIR = os.path.join(os.path.dirname(BASE_DIR), "storage")


@router.delete("/{file_id}")
def delete_file(file_id: str, db: Session = Depends(get_db)):
    """Delete file, chunks, share links, and storage artifacts."""

    file_obj = db.query(File).filter(File.file_id == file_id).first()
    if not file_obj:
        raise HTTPException(status_code=404, detail="File not found")

    # Remove storage artifacts
    shutil.rmtree(os.path.join(STORAGE_DIR, "chunks", file_id), ignore_errors=True)
    try:
        os.remove(os.path.join(STORAGE_DIR, "files", f"{file_id}_{file_obj.filename}"))
    except FileNotFoundError:
        pass

    # Remove DB records
    db.query(ShareLink).filter(ShareLink.file_id == file_id).delete()
    db.query(Chunk).filter(Chunk.file_id == file_id).delete()
    db.delete(file_obj)
    db.commit()

    return {"message": "File deleted successfully ✅", "file_id": file_id}
