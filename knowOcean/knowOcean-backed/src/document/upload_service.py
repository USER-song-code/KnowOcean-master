"""分片上传业务逻辑

对照 Java: document/service/DocumentUploadService.java (chunked upload 部分)
"""
import hashlib
import uuid
from datetime import datetime, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from src.config import get_settings
from src.models.upload import UploadSession, UploadChunk
from src.models.document import Document
from src.engine import minio as minio_engine
from src.common.exceptions import BusinessException, NotFoundException

settings = get_settings()


async def init_upload(
    db: AsyncSession,
    user_id: int,
    group_id: int,
    file_name: str,
    file_size: int,
    content_type: str,
    file_hash: str,
    chunk_size: int,
    chunk_count: int,
) -> dict:
    """初始化分片上传会话

    Returns: { instantUpload, documentId, uploadId, uploadedChunks, chunkSize, chunkCount }
    """
    # 1. 秒传检测: 相同 hash 的已就绪文档
    stmt = select(Document).where(
        Document.group_id == group_id,
        Document.file_hash == file_hash,
        Document.status == "READY",
        Document.deleted == False,
    ).order_by(Document.id.desc()).limit(1)
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        return {
            "instantUpload": True,
            "documentId": existing.id,
            "uploadId": None,
            "uploadedChunks": [],
            "chunkSize": None,
            "chunkCount": None,
        }

    # 2. 断点续传: 查找进度中的会话
    expire_threshold = datetime.utcnow() - timedelta(hours=24)
    stmt = select(UploadSession).where(
        UploadSession.group_id == group_id,
        UploadSession.uploader_user_id == user_id,
        UploadSession.file_hash == file_hash,
        UploadSession.status.in_(["INIT", "UPLOADING"]),
        UploadSession.expires_at > expire_threshold,
    ).order_by(UploadSession.created_at.desc()).limit(1)
    reused = (await db.execute(stmt)).scalar_one_or_none()

    if reused:
        chunk_stmt = select(UploadChunk.chunk_index).where(UploadChunk.upload_id == reused.upload_id).order_by(UploadChunk.chunk_index)
        uploaded = [c for (c,) in (await db.execute(chunk_stmt)).all()]
        return {
            "instantUpload": False,
            "documentId": None,
            "uploadId": reused.upload_id,
            "uploadedChunks": uploaded,
            "chunkSize": reused.chunk_size,
            "chunkCount": reused.chunk_count,
        }

    # 3. 新建上传会话
    ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
    upload_id = uuid.uuid4().hex
    now = datetime.utcnow()
    session = UploadSession(
        upload_id=upload_id,
        group_id=group_id,
        uploader_user_id=user_id,
        file_name=file_name,
        file_ext=ext,
        content_type=content_type,
        file_size=file_size,
        file_hash=file_hash,
        chunk_size=chunk_size,
        chunk_count=chunk_count,
        status="UPLOADING",
        storage_bucket=settings.minio_bucket,
        expires_at=now + timedelta(hours=24),
    )
    db.add(session)
    await db.flush()

    return {
        "instantUpload": False,
        "documentId": None,
        "uploadId": upload_id,
        "uploadedChunks": [],
        "chunkSize": chunk_size,
        "chunkCount": chunk_count,
    }


async def upload_chunk(
    db: AsyncSession,
    upload_id: str,
    chunk_index: int,
    chunk_hash: str,
    chunk_data: bytes,
) -> dict:
    """上传单个分片到 MinIO

    Returns: { status, uploadedChunks, uploadedChunkCount, chunkCount }
    """
    session = await _get_session(db, upload_id)

    if session.status == "COMPLETED":
        raise BusinessException("上传会话已完成")
    if session.expires_at < datetime.utcnow():
        session.status = "EXPIRED"
        db.add(session)
        await db.flush()
        raise BusinessException("上传会话已过期")

    # 上传分片到 MinIO
    chunk_key = f"chunks/{upload_id}/{chunk_index:06d}"
    minio_engine.put_object(chunk_key, chunk_data, "application/octet-stream")

    # 记录分片 (upsert)
    stmt = select(UploadChunk).where(
        UploadChunk.upload_id == upload_id,
        UploadChunk.chunk_index == chunk_index,
    )
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        existing.chunk_hash = chunk_hash
        existing.chunk_size = len(chunk_data)
        existing.uploaded_at = datetime.utcnow()
        db.add(existing)
    else:
        chunk = UploadChunk(
            upload_id=upload_id,
            chunk_index=chunk_index,
            chunk_size=len(chunk_data),
            chunk_hash=chunk_hash,
            storage_bucket=settings.minio_bucket,
            storage_object_key=chunk_key,
            uploaded_at=datetime.utcnow(),
        )
        db.add(chunk)

    session.status = "UPLOADING"
    db.add(session)
    await db.flush()

    return await _status_response(db, upload_id)


async def get_upload_status(db: AsyncSession, upload_id: str) -> dict:
    await _get_session(db, upload_id)
    return await _status_response(db, upload_id)


async def complete_upload(db: AsyncSession, upload_id: str) -> int:
    """完成上传: MinIO compose 合并分片 → 创建文档记录 → 清理分片

    Returns: 新文档 ID
    """
    session = await _get_session(db, upload_id)
    if session.status == "COMPLETED":
        # 已经完成, 直接返回文档
        doc_stmt = select(Document).where(
            Document.storage_object_key.like(f"merged_{upload_id}_%")
        ).order_by(Document.id.desc()).limit(1)
        doc = (await db.execute(doc_stmt)).scalar_one_or_none()
        if doc:
            return doc.id

    session.status = "COMPLETING"
    db.add(session)
    await db.flush()

    # 收集所有分片 key
    chunk_stmt = (
        select(UploadChunk)
        .where(UploadChunk.upload_id == upload_id)
        .order_by(UploadChunk.chunk_index)
    )
    chunks = (await db.execute(chunk_stmt)).scalars().all()

    if len(chunks) != session.chunk_count:
        raise BusinessException(f"分片不完整: 已上传 {len(chunks)}/{session.chunk_count}")

    chunk_keys = [c.storage_object_key for c in chunks]
    merged_key = f"documents/{session.group_id}/{upload_id}_{session.file_name}"

    # MinIO compose 合并
    minio_engine.compose_objects(chunk_keys, merged_key)

    # 清理分片
    for ck in chunk_keys:
        minio_engine.delete_object(ck)

    # 提取预览文本 (小文本文件)
    preview = None
    if session.file_ext in ("txt", "md", "csv", "json", "xml", "html", "htm"):
        content = minio_engine.get_object(merged_key)
        if content:
            try:
                preview = content.decode("utf-8")[:5000]
            except UnicodeDecodeError:
                preview = content.decode("utf-8", errors="replace")[:5000]

    # 创建文档记录
    now = datetime.utcnow()
    doc = Document(
        group_id=session.group_id,
        uploader_user_id=session.uploader_user_id,
        file_name=session.file_name,
        file_ext=session.file_ext,
        content_type=session.content_type,
        file_size=session.file_size,
        file_hash=session.file_hash,
        storage_bucket=settings.minio_bucket,
        storage_object_key=merged_key,
        status="UPLOADED",
        preview_text=preview,
        uploaded_at=now,
    )
    db.add(doc)
    await db.flush()
    await db.refresh(doc)

    session.status = "COMPLETED"
    session.merged_object_key = merged_key
    db.add(session)
    await db.flush()

    return doc.id


async def _get_session(db: AsyncSession, upload_id: str) -> UploadSession:
    stmt = select(UploadSession).where(UploadSession.upload_id == upload_id)
    session = (await db.execute(stmt)).scalar_one_or_none()
    if session is None:
        raise NotFoundException("上传会话不存在")
    return session


async def _status_response(db: AsyncSession, upload_id: str) -> dict:
    session = await _get_session(db, upload_id)
    chunk_stmt = select(UploadChunk.chunk_index).where(
        UploadChunk.upload_id == upload_id
    ).order_by(UploadChunk.chunk_index)
    uploaded_chunks = [c for (c,) in (await db.execute(chunk_stmt)).all()]
    return {
        "status": session.status,
        "uploadedChunks": uploaded_chunks,
        "uploadedChunkCount": len(uploaded_chunks),
        "chunkCount": session.chunk_count,
    }
