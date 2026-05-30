"""文档管理 API"""
import hashlib
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Query, Depends, UploadFile, File, Form
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from src.database.session import get_db
from src.auth.dependencies import require_auth
from src.common.exceptions import NotFoundException
from src.common.response import ApiResponse
from src.common.security import UserIdentity
from src.group.service import check_membership
from src.models.document import Document
from src.document.schemas import DocumentListItem
from src.document.upload_service import init_upload, upload_chunk, get_upload_status, complete_upload
from src.engine import minio as minio_engine
from src.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/api/documents", tags=["Documents"])

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"
ALLOWED_EXTENSIONS = {"txt", "md", "pdf", "docx", "doc", "xlsx", "xls", "pptx", "ppt", "csv", "json", "xml", "html", "htm"}


# ── 直接上传 ──

@router.post("/upload")
async def upload_document(
    groupId: int = Form(...),
    file: UploadFile = File(...),
    user: UserIdentity = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """直接上传文档"""
    if not await check_membership(db, groupId, user.user_id):
        from src.common.exceptions import ForbiddenException
        raise ForbiddenException("你不是该群组的成员")

    ext = (file.filename or "").rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        from src.common.exceptions import BusinessException
        raise BusinessException(f"不支持的文件类型: .{ext}")

    # 读取文件内容并计算哈希
    content = await file.read()
    file_hash = hashlib.sha256(content).hexdigest()

    # 写入本地存储
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid.uuid4().hex}.{ext}"
    stored_path = UPLOAD_DIR / stored_name
    stored_path.write_bytes(content)

    # 提取预览文本 (仅纯文本文件，前 5000 字符)
    preview = None
    if ext in ("txt", "md", "csv", "json", "xml", "html", "htm") and len(content) < 10 * 1024 * 1024:
        try:
            text = content.decode("utf-8")
            # 检查是否真的是文本文件（无过多控制字符）
            if "\x00" not in text:
                preview = text[:5000]
        except UnicodeDecodeError:
            pass  # 二进制内容, 不提取预览

    now = datetime.utcnow()
    doc = Document(
        group_id=groupId,
        uploader_user_id=user.user_id,
        file_name=file.filename or "unnamed",
        file_ext=ext,
        content_type=file.content_type or "application/octet-stream",
        file_size=len(content),
        file_hash=file_hash,
        storage_bucket="local",
        storage_object_key=stored_name,
        status="UPLOADED",
        preview_text=preview,
        uploaded_at=now,
    )
    db.add(doc)
    await db.flush()
    await db.refresh(doc)

    return ApiResponse.ok(data=doc.id, message="上传成功，文档正在处理中...")


# ── 分片上传 ──

@router.post("/upload/init")
async def upload_init(
    payload: dict,
    user: UserIdentity = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """初始化分片上传 — 支持秒传和断点续传"""
    group_id = payload.get("groupId", 0)
    if not await check_membership(db, group_id, user.user_id):
        from src.common.exceptions import ForbiddenException
        raise ForbiddenException("你不是该群组的成员")

    result = await init_upload(
        db, user.user_id, group_id,
        file_name=str(payload.get("fileName", "")),
        file_size=int(payload.get("fileSize", 0)),
        content_type=str(payload.get("contentType", "")),
        file_hash=str(payload.get("fileHash", "")),
        chunk_size=int(payload.get("chunkSize", 0)),
        chunk_count=int(payload.get("chunkCount", 0)),
    )
    return ApiResponse.ok(data=result)


@router.post("/upload/chunks")
async def handle_upload_chunk(
    uploadId: str = Form(...),
    chunkIndex: int = Form(...),
    chunkHash: str = Form(...),
    chunk: UploadFile = File(...),
    user: UserIdentity = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """上传单个分片到 MinIO"""
    data = await chunk.read()
    result = await upload_chunk(db, uploadId, chunkIndex, chunkHash, data)
    return ApiResponse.ok(data=result)


@router.get("/upload/{upload_id}")
async def handle_upload_status(
    upload_id: str,
    user: UserIdentity = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """查询分片上传状态"""
    result = await get_upload_status(db, upload_id)
    return ApiResponse.ok(data=result)


@router.post("/upload/{upload_id}/complete")
async def handle_upload_complete(
    upload_id: str,
    user: UserIdentity = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """完成分片上传合并"""
    doc_id = await complete_upload(db, upload_id)
    return ApiResponse.ok(data=doc_id, message="上传完成")


# ── 文档 CRUD ──

@router.get("")
async def list_documents(
    groupId: int | None = Query(None),
    fileName: str | None = Query(None),
    status: str | None = Query(None),
    uploaderUserId: int | None = Query(None),
    user: UserIdentity = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """文档列表 — 支持按群组、文件名、状态筛选"""
    stmt = select(Document).where(Document.deleted == False)
    if groupId:
        stmt = stmt.where(Document.group_id == groupId)
    if fileName:
        stmt = stmt.where(Document.file_name.ilike(f"%{fileName}%"))
    if status:
        stmt = stmt.where(Document.status == status)
    if uploaderUserId:
        stmt = stmt.where(Document.uploader_user_id == uploaderUserId)
    stmt = stmt.order_by(Document.created_at.desc()).limit(50)

    result = await db.execute(stmt)
    docs = result.scalars().all()

    items = [
        DocumentListItem(
            documentId=d.id,
            fileName=d.file_name,
            fileExt=d.file_ext,
            fileSize=d.file_size,
            status=d.status,
            uploaderUserId=d.uploader_user_id,
            groupId=d.group_id,
            uploadedAt=d.uploaded_at.isoformat() if d.uploaded_at else None,
        )
        for d in docs
    ]
    return ApiResponse.ok(data=items)


@router.get("/{document_id}/preview")
async def preview_document(document_id: int, user: UserIdentity = Depends(require_auth), db: AsyncSession = Depends(get_db)):
    doc = (await db.execute(select(Document).where(Document.id == document_id, Document.deleted == False))).scalar_one_or_none()
    if doc is None:
        raise NotFoundException("文档不存在")
    return ApiResponse.ok(data={
        "documentId": doc.id,
        "groupId": doc.group_id,
        "fileName": doc.file_name,
        "fileExt": doc.file_ext,
        "fileSize": doc.file_size,
        "status": doc.status,
        "previewText": doc.preview_text or "",
    })


@router.delete("/{document_id}")
async def delete_document(document_id: int, user: UserIdentity = Depends(require_auth), db: AsyncSession = Depends(get_db)):
    doc = (await db.execute(select(Document).where(Document.id == document_id))).scalar_one_or_none()
    if doc is None:
        raise NotFoundException("文档不存在")
    doc.deleted = True
    db.add(doc)
    await db.flush()
    return ApiResponse.ok(message="文档已删除")


@router.post("/{document_id}/retry-ingestion")
async def retry_ingestion(document_id: int, user: UserIdentity = Depends(require_auth), db: AsyncSession = Depends(get_db)):
    doc = (await db.execute(select(Document).where(Document.id == document_id))).scalar_one_or_none()
    if doc is None:
        raise NotFoundException("文档不存在")
    doc.status = "PROCESSING"
    db.add(doc)
    await db.flush()
    return ApiResponse.ok(message="重新处理已提交，文档状态已重置为 PROCESSING")


@router.get("/{document_id}/download")
async def download_document(document_id: int, user: UserIdentity = Depends(require_auth), db: AsyncSession = Depends(get_db)):
    doc = (await db.execute(select(Document).where(Document.id == document_id, Document.deleted == False))).scalar_one_or_none()
    if doc is None:
        raise NotFoundException("文档不存在")

    content = None
    # 1. 尝试 MinIO
    if doc.storage_bucket and doc.storage_bucket != "local":
        content = minio_engine.get_object(doc.storage_object_key)
    # 2. 回退本地
    if content is None:
        stored_path = UPLOAD_DIR / doc.storage_object_key
        if stored_path.exists():
            content = stored_path.read_bytes()

    if content:
        from fastapi.responses import Response as FileResponse
        return FileResponse(content=content, media_type=doc.content_type,
                          headers={"Content-Disposition": f'attachment; filename="{doc.file_name}"'})

    return PlainTextResponse(doc.preview_text or "(空文档)")
