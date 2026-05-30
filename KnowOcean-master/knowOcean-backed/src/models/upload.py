"""DocumentUploadSession / DocumentUploadChunk ORM

匹配现有 DB 表: document_upload_sessions, document_upload_chunks
"""
from datetime import datetime
from sqlalchemy import String, BigInteger, ForeignKey, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from src.database.base import Base, TimestampMixin


class UploadSession(Base, TimestampMixin):
    __tablename__ = "document_upload_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    upload_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    group_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("groups.id"), nullable=False)
    uploader_user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    file_name: Mapped[str] = mapped_column(String(512), nullable=False)
    file_ext: Mapped[str] = mapped_column(String(32), default="")
    content_type: Mapped[str] = mapped_column(String(128), default="")
    file_size: Mapped[int] = mapped_column(BigInteger, default=0)
    file_hash: Mapped[str] = mapped_column(String(128), default="")
    chunk_size: Mapped[int] = mapped_column(BigInteger, default=0)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(16), default="INIT")  # INIT|UPLOADING|COMPLETING|COMPLETED|EXPIRED
    storage_bucket: Mapped[str] = mapped_column(String(128), default="")
    merged_object_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class UploadChunk(Base, TimestampMixin):
    __tablename__ = "document_upload_chunks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    upload_id: Mapped[str] = mapped_column(String(64), ForeignKey("document_upload_sessions.upload_id"), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_size: Mapped[int] = mapped_column(BigInteger, default=0)
    chunk_hash: Mapped[str] = mapped_column(String(128), default="")
    storage_bucket: Mapped[str] = mapped_column(String(128), default="")
    storage_object_key: Mapped[str] = mapped_column(String(512), default="")
    uploaded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
