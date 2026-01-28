from datetime import datetime
from sqlalchemy import Column, Integer, String, BigInteger, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from backend.db import Base


class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(String(100), unique=True, index=True, nullable=False)
    filename = Column(String(255), nullable=False)

    total_chunks = Column(Integer, nullable=False)
    chunk_size = Column(Integer, nullable=False)
    file_size = Column(BigInteger, nullable=False)

    status = Column(String(50), default="uploading")  # uploading | completed | failed
    file_hash = Column(String(64))

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    chunks = relationship("Chunk", back_populates="file", cascade="all, delete-orphan")
    share_links = relationship("ShareLink", back_populates="file", cascade="all, delete-orphan")


class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(String(100), ForeignKey("files.file_id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)

    uploaded = Column(Boolean, default=False)
    chunk_hash = Column(String(64))
    size = Column(BigInteger)
    created_at = Column(DateTime, default=datetime.utcnow)

    file = relationship("File", back_populates="chunks")


class ShareLink(Base):
    __tablename__ = "share_links"

    id = Column(Integer, primary_key=True, index=True)
    share_token = Column(String(255), unique=True, index=True, nullable=False)
    file_id = Column(String(100), ForeignKey("files.file_id", ondelete="CASCADE"), nullable=False)

    password = Column(String(128), nullable=False)
    expires_at = Column(DateTime)
    download_count = Column(Integer, default=0)
    max_downloads = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    file = relationship("File", back_populates="share_links")
