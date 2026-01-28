from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.db import get_db
from backend.models import File

router = APIRouter(prefix="/files", tags=["Files"])


def dt_to_str(dt: Optional[datetime]):
    return dt.isoformat() if dt else None


@router.get("")
def list_files(db: Session = Depends(get_db)):
    """Return all files (newest first)"""

    files = db.query(File).order_by(File.id.desc()).all()

    return [
        {
            "file_id": f.file_id,
            "filename": f.filename,
            "file_size": f.file_size,
            "total_chunks": f.total_chunks,
            "status": f.status,
            "file_hash": f.file_hash,
            "created_at": dt_to_str(getattr(f, "created_at", None)),
            "updated_at": dt_to_str(getattr(f, "updated_at", None)),
        }
        for f in files
    ]
