import os
import secrets
import hashlib
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.db import get_db
from backend.models import File, ShareLink

router = APIRouter(prefix="/share", tags=["Share"])

FILES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "storage", "files")


def hash_password(p: str) -> str:
    return hashlib.sha256(p.encode()).hexdigest()


@router.post("/create/{file_id}")
def create_share_link(file_id: str, expire_minutes: int = 60, max_downloads: int = 5, db: Session = Depends(get_db)):
    file_obj = db.query(File).filter_by(file_id=file_id).first()
    if not file_obj:
        raise HTTPException(404, "Invalid file_id")
    if file_obj.status != "completed":
        raise HTTPException(400, "File not completed yet")

    token = secrets.token_urlsafe(32)
    raw_password = secrets.token_urlsafe(8)

    db.add(ShareLink(
        share_token=token,
        file_id=file_id,
        password=hash_password(raw_password),
        expires_at=datetime.utcnow() + timedelta(minutes=expire_minutes),
        max_downloads=max_downloads
    ))
    db.commit()

    return {
        "message": "Share link created ✅",
        "file_id": file_id,
        "share_url": f"http://127.0.0.1:8000/share/download/{token}",
        "password": raw_password,
        "expires_at": datetime.utcnow() + timedelta(minutes=expire_minutes),
        "max_downloads": max_downloads
    }


@router.get("/download/{token}")
def download_shared_file(token: str, password: str, db: Session = Depends(get_db)):
    share = db.query(ShareLink).filter_by(share_token=token).first()
    if not share:
        raise HTTPException(404, "Invalid share link")
    if share.expires_at and datetime.utcnow() > share.expires_at:
        raise HTTPException(403, "Share link expired")
    if share.max_downloads is not None and share.download_count >= share.max_downloads:
        raise HTTPException(403, "Max downloads reached")
    if share.password != hash_password(password):
        raise HTTPException(401, "Wrong password")

    file_obj = db.query(File).filter_by(file_id=share.file_id).first()
    if not file_obj:
        raise HTTPException(404, "File not found")

    path = os.path.join(FILES_DIR, f"{file_obj.file_id}_{file_obj.filename}")
    if not os.path.exists(path):
        raise HTTPException(404, "Merged file missing")

    share.download_count += 1
    db.commit()

    return FileResponse(path, filename=file_obj.filename, media_type="application/octet-stream")
