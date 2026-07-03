"""真实 ETL 管线：文档解析 → 分块 → 向量化 → 存储

替代 mock_etl.py，实现完整的文档摄入流程：
  UPLOADED → 下载 → 解析 → 分块 → 向量嵌入 → pgvector + ES → READY
"""
import asyncio
import json
import logging
import traceback
import uuid
from datetime import datetime
from sqlalchemy import select, text
from src.database.session import async_session_factory
from src.models.document import Document
from src.engine import llm, minio
from src.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

CHUNK_SIZE = 512          # 每块字符数
CHUNK_OVERLAP = 100       # 块间重叠字符数
ES_INDEX = "dd_rag_document_chunks"


# ═══════════════════════════════════════
# 文本解析
# ═══════════════════════════════════════

def _parse_pdf(content: bytes) -> str:
    """PDF → 纯文本"""
    import fitz
    doc = fitz.open(stream=content, filetype="pdf")
    try:
        return "\n\n".join(page.get_text() for page in doc)
    finally:
        doc.close()


def _parse_docx(content: bytes) -> str:
    """DOCX → 纯文本"""
    from io import BytesIO
    from docx import Document as DocxDocument
    doc = DocxDocument(BytesIO(content))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def _parse_text(content: bytes) -> str:
    """纯文本文件"""
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        return content.decode("utf-8", errors="replace")


PARSERS = {
    "pdf":  _parse_pdf,
    "docx": _parse_docx,
    "doc":  _parse_docx,
    "txt":  _parse_text,
    "md":   _parse_text,
    "csv":  _parse_text,
    "json": _parse_text,
    "xml":  _parse_text,
    "html": _parse_text,
    "htm":  _parse_text,
}


def parse_document(content: bytes, file_ext: str) -> str:
    """根据扩展名解析文档"""
    ext = file_ext.lower().lstrip(".")
    parser = PARSERS.get(ext)
    if parser:
        return parser(content)
    # 兜底：尝试当纯文本解析
    return _parse_text(content)


# ═══════════════════════════════════════
# 文本分块
# ═══════════════════════════════════════

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[tuple[str, int, int]]:
    """将文本分块，返回 [(chunk_text, char_start, char_end), ...]

    优先按段落边界分割，段落太长的按句号/换行切分。
    """
    if not text or not text.strip():
        return []

    # 先按段落分
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[tuple[str, int, int]] = []
    pos = 0  # 当前在原文本中的字符位置

    for para in paragraphs:
        para_start = text.index(para, pos) if para in text[pos:] else pos
        para_pos = para_start

        if len(para) <= chunk_size:
            chunks.append((para, para_pos, para_pos + len(para)))
        else:
            # 段落太长，按句子切
            sentences = _split_sentences(para)
            current = ""
            current_start = para_pos
            for s in sentences:
                if len(current) + len(s) <= chunk_size:
                    current += s
                else:
                    if current.strip():
                        chunks.append((current.strip(), current_start, current_start + len(current)))
                    # 重叠
                    overlap_text = current[-overlap:] if len(current) > overlap else current
                    current = overlap_text + s
                    current_start = current_start + max(0, len(current) - len(s) - len(overlap_text))
            if current.strip():
                chunks.append((current.strip(), current_start, current_start + len(current)))

        pos = para_start + len(para)

    # 合并相邻小块
    return _merge_small_chunks(chunks, chunk_size)


def _split_sentences(text: str) -> list[str]:
    """按句号、问号、感叹号、换行切分句子"""
    import re
    parts = re.split(r'(?<=[。！？.!?\n])', text)
    return [p for p in parts if p.strip()]


def _merge_small_chunks(chunks: list[tuple[str, int, int]], min_size: int) -> list[tuple[str, int, int]]:
    """合并过小的相邻块"""
    if len(chunks) <= 1:
        return chunks
    merged = []
    i = 0
    while i < len(chunks):
        current, start, end = chunks[i]
        while i + 1 < len(chunks) and len(current) + len(chunks[i + 1][0]) <= min_size:
            i += 1
            next_text, _, next_end = chunks[i]
            current += " " + next_text
            end = next_end
        merged.append((current, start, end))
        i += 1
    return merged


# ═══════════════════════════════════════
# 向量化 + 存储
# ═══════════════════════════════════════

async def _store_chunk(
    document_id: int,
    group_id: int,
    chunk_index: int,
    chunk_text: str,
    char_start: int,
    char_end: int,
    file_name: str,
) -> str | None:
    """存储单个 chunk → document_chunks + vector_store + ES。返回 chunk_id"""
    import uuid as uuid_mod

    chunk_id = uuid_mod.uuid4().hex[:32]
    now = datetime.utcnow()

    async with async_session_factory() as db:
        try:
            # 1. 插入 document_chunks 表
            await db.execute(
                text("""INSERT INTO document_chunks (document_id, group_id, chunk_index, chunk_text, char_start, char_end, created_at, updated_at)
                        VALUES (:did, :gid, :cidx, :txt, :cs, :ce, :now, :now)"""),
                {"did": document_id, "gid": group_id, "cidx": chunk_index, "txt": chunk_text, "cs": char_start, "ce": char_end, "now": now},
            )

            # 2. 生成向量嵌入
            embedding = await llm.get_embedding(chunk_text)
            vector_str = f"[{','.join(str(x) for x in embedding)}]"

            # 3. 插入 vector_store
            metadata = json.dumps({
                "documentId": document_id,
                "chunkIndex": chunk_index,
                "fileName": file_name,
                "groupId": group_id,
            }, ensure_ascii=False)

            await db.execute(
                text("""INSERT INTO vector_store (id, content, metadata, embedding)
                        VALUES (:id, :content, CAST(:meta AS jsonb), :embedding)"""),
                {"id": chunk_id, "content": chunk_text, "meta": metadata, "embedding": vector_str},
            )

            await db.commit()

            # 4. 索引 Elasticsearch（独立操作，失败不影响 DB）
            try:
                from elasticsearch import Elasticsearch
                es_url = f"{settings.es_scheme}://{settings.es_host}:{settings.es_port}"
                if settings.es_username and settings.es_password:
                    es = Elasticsearch(es_url, basic_auth=(settings.es_username, settings.es_password))
                else:
                    es = Elasticsearch(es_url)
                es.index(index=ES_INDEX, body={
                    "groupId": group_id,
                    "documentId": document_id,
                    "chunkId": chunk_id,
                    "chunkIndex": chunk_index,
                    "fileName": file_name,
                    "chunkText": chunk_text,
                })
            except Exception as e:
                logger.warning(f"[ETL] ES index failed for chunk {chunk_id}: {e}")

            return chunk_id

        except Exception as e:
            logger.error(f"[ETL] Store chunk {chunk_index} failed: {e}")
            await db.rollback()
            return None


# ═══════════════════════════════════════
# 主处理流程
# ═══════════════════════════════════════

async def process_document(doc: Document) -> None:
    """处理单个文档"""
    doc_id = doc.id
    logger.info(f"[ETL] Processing doc {doc_id}: {doc.file_name}")

    async with async_session_factory() as db:
        # 更新状态为 PROCESSING
        await db.execute(
            text("UPDATE documents SET status = 'PROCESSING', updated_at = :now WHERE id = :did"),
            {"did": doc_id, "now": datetime.utcnow()},
        )
        await db.commit()

    try:
        # 1. 下载文件
        content = None
        if doc.storage_bucket and doc.storage_bucket != "local":
            content = minio.get_object(doc.storage_object_key)
        if content is None:
            from pathlib import Path
            upload_dir = Path(__file__).resolve().parent.parent.parent / "uploads"
            stored_path = upload_dir / doc.storage_object_key
            if stored_path.exists():
                content = stored_path.read_bytes()

        if content is None:
            raise Exception(f"无法获取文件内容: {doc.storage_object_key}")

        # 2. 解析文本
        full_text = parse_document(content, doc.file_ext)
        if not full_text or not full_text.strip():
            raise Exception("文档解析后无文本内容")

        # 3. 分块
        chunks = chunk_text(full_text)
        logger.info(f"[ETL] Doc {doc_id}: {len(chunks)} chunks")

        # 4. 逐块处理
        success_count = 0
        for i, (chunk_text_val, char_start, char_end) in enumerate(chunks):
            if not chunk_text_val.strip():
                continue
            chunk_id = await _store_chunk(
                document_id=doc_id,
                group_id=doc.group_id,
                chunk_index=i,
                chunk_text=chunk_text_val,
                char_start=char_start,
                char_end=char_end,
                file_name=doc.file_name or "unnamed",
            )
            if chunk_id:
                success_count += 1
            # 每个 chunk 间短暂休眠，避免 API 限流
            await asyncio.sleep(0.3)

        # 5. 更新文档状态为 READY
        async with async_session_factory() as db:
            preview = full_text[:5000]
            await db.execute(
                text("""UPDATE documents
                        SET status = 'READY', preview_text = :preview,
                            processed_at = :now, updated_at = :now
                        WHERE id = :did"""),
                {"did": doc_id, "preview": preview, "now": datetime.utcnow()},
            )
            await db.commit()

        logger.info(f"[ETL] Doc {doc_id}: READY ({success_count}/{len(chunks)} chunks)")

    except Exception as e:
        logger.error(f"[ETL] Doc {doc_id} FAILED: {e}\n{traceback.format_exc()}")
        async with async_session_factory() as db:
            await db.execute(
                text("""UPDATE documents
                        SET status = 'FAILED', failure_reason = :reason,
                            updated_at = :now
                        WHERE id = :did"""),
                {"did": doc_id, "reason": str(e)[:500], "now": datetime.utcnow()},
            )
            await db.commit()


async def process_pending_documents():
    """轮询并处理所有 UPLOADED 状态的文档"""
    async with async_session_factory() as db:
        stmt = select(Document).where(
            Document.status == "UPLOADED",
            Document.deleted == False,
        ).order_by(Document.id.asc()).limit(5)  # 一次最多处理 5 个

        result = await db.execute(stmt)
        docs = result.scalars().all()

    for doc in docs:
        await process_document(doc)


async def start_etl_loop():
    """后台 ETL 主循环"""
    logger.info("[ETL] ETL loop started")
    while True:
        try:
            await process_pending_documents()
        except Exception as e:
            logger.error(f"[ETL] Loop error: {e}")
        await asyncio.sleep(5)
