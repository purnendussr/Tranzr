import os, uuid, shutil, hashlib
from datetime import datetime
from fastapi import APIRouter, Depends, File as FastFile, Form, UploadFile, HTTPException
from sqlalchemy.orm import Session
from backend.db import get_db
from backend.models import File, Chunk

router = APIRouter(prefix="/upload", tags=["Upload"])

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHUNKS_DIR = os.path.join(BASE_DIR, "storage", "chunks")
FILES_DIR = os.path.join(BASE_DIR, "storage", "files")
os.makedirs(CHUNKS_DIR, exist_ok=True)
os.makedirs(FILES_DIR, exist_ok=True)


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1024 * 1024), b""):
            h.update(c)
    return h.hexdigest()


# ---------- START UPLOAD ----------
@router.post("/start")
def start_upload(payload: dict, db: Session = Depends(get_db)):
    try:
        filename = payload["filename"]
        file_size = int(float(payload["file_size"]) * 1024 * 1024)
        chunk_size = int(float(payload["chunk_size"]) * 1024 * 1024)
    except:
        raise HTTPException(400, "filename, file_size, chunk_size required (numbers)")

    if file_size <= 0 or chunk_size <= 0:
        raise HTTPException(400, "Sizes must be > 0")

    chunk_size = min(chunk_size, file_size)
    file_id = str(uuid.uuid4())
    total_chunks = (file_size + chunk_size - 1) // chunk_size

    db.add(File(
        file_id=file_id,
        filename=filename,
        file_size=file_size,
        total_chunks=total_chunks,
        chunk_size=chunk_size,
        status="uploading",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    ))
    db.commit()

    os.makedirs(os.path.join(CHUNKS_DIR, file_id), exist_ok=True)
    return {"file_id": file_id, "total_chunks": total_chunks}


# ---------- UPLOAD CHUNK ----------
@router.post("/chunk")
def upload_chunk(file_id: str = Form(...), chunk_index: int = Form(...),
                 chunk: UploadFile = FastFile(...), db: Session = Depends(get_db)):

    file_obj = db.query(File).filter(File.file_id == file_id).first()
    if not file_obj:
        raise HTTPException(404, "Invalid file_id")

    if not (0 <= chunk_index < file_obj.total_chunks):
        raise HTTPException(400, f"Invalid chunk_index {chunk_index}")

    if file_obj.status == "completed":
        return {"message": "File already completed ✅", "chunk_index": chunk_index}

    chunk_path = os.path.join(CHUNKS_DIR, file_id, f"{chunk_index}.part")
    os.makedirs(os.path.dirname(chunk_path), exist_ok=True)

    if os.path.exists(chunk_path):
        return {"message": "Chunk already uploaded ✅", "chunk_index": chunk_index}

    expected = (file_obj.file_size - file_obj.chunk_size * (file_obj.total_chunks - 1)
                if chunk_index == file_obj.total_chunks - 1 else file_obj.chunk_size)

    written = 0
    with open(chunk_path, "wb") as f:
        while data := chunk.file.read(1024 * 1024):
            remain = expected - written
            if remain <= 0:
                break
            f.write(data[:remain])
            written += min(len(data), remain)

    db.add(Chunk(file_id=file_id, chunk_index=chunk_index, uploaded=True))
    file_obj.updated_at = datetime.utcnow()
    db.commit()

    return {"message": "Chunk uploaded ✅", "chunk_index": chunk_index}


# ---------- STATUS ----------
@router.get("/status/{file_id}")
def upload_status(file_id: str, db: Session = Depends(get_db)):
    file_obj = db.query(File).filter(File.file_id == file_id).first()
    if not file_obj:
        raise HTTPException(404, "Invalid file_id")

    uploaded = {c[0] for c in db.query(Chunk.chunk_index)
                .filter(Chunk.file_id == file_id, Chunk.uploaded == True).all()}
    missing = [i for i in range(file_obj.total_chunks) if i not in uploaded]

    return {
        "file_id": file_id,
        "total_chunks": file_obj.total_chunks,
        "uploaded_chunks": sorted(uploaded),
        "missing_chunks": missing,
        "status": file_obj.status,
    }


# ---------- MERGE ----------
@router.post("/merge/{file_id}")
def merge_file(file_id: str, db: Session = Depends(get_db)):
    file_obj = db.query(File).filter(File.file_id == file_id).first()
    if not file_obj:
        raise HTTPException(404, "Invalid file_id")

    if file_obj.status == "completed":
        return {"message": "Already merged ✅", "file_id": file_id, "file_hash": file_obj.file_hash}

    status = upload_status(file_id, db)
    if status["missing_chunks"]:
        raise HTTPException(400, {"missing_chunks": status["missing_chunks"]})

    merged_path = os.path.join(FILES_DIR, f"{file_id}_{file_obj.filename}")
    with open(merged_path, "wb") as merged:
        for i in range(file_obj.total_chunks):
            with open(os.path.join(CHUNKS_DIR, file_id, f"{i}.part"), "rb") as p:
                shutil.copyfileobj(p, merged)

    file_obj.file_hash = sha256_file(merged_path)
    file_obj.status = "completed"
    file_obj.updated_at = datetime.utcnow()
    db.commit()
    shutil.rmtree(os.path.join(CHUNKS_DIR, file_id), ignore_errors=True)

    return {"message": "Merged ✅", "file_id": file_id, "file_hash": file_obj.file_hash}
