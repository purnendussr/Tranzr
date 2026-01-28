import os
import shutil
from datetime import datetime, timedelta

from backend.db import SessionLocal
from backend.models import File

CHUNKS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "storage",
    "chunks",
)


def cleanup_abandoned_uploads(hours: int = 6) -> int:
    """Remove incomplete uploads older than given hours."""
    cutoff = datetime.utcnow() - timedelta(hours=hours)

    with SessionLocal() as db:
        abandoned_files = (
            db.query(File)
            .filter(File.status != "completed", File.created_at < cutoff)
            .all()
        )

        for f in abandoned_files:
            shutil.rmtree(os.path.join(CHUNKS_DIR, f.file_id), ignore_errors=True)
            db.delete(f)

        db.commit()
        return len(abandoned_files)
