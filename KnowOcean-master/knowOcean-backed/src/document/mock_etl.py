"""模拟 ETL 处理：文档上传后自动经历 UPLOADED → PROCESSING → READY"""
import asyncio
from sqlalchemy import select
from src.database.session import engine, async_session_factory
from src.models.document import Document


async def process_pending_documents():
    """处理所有 UPLOADED 状态的文档"""
    async with async_session_factory() as db:
        stmt = select(Document).where(
            Document.status == "UPLOADED",
            Document.deleted == False,
        ).order_by(Document.id.asc())

        result = await db.execute(stmt)
        docs = result.scalars().all()

        for doc in docs:
            # Step 1: UPLOADED → PROCESSING
            doc.status = "PROCESSING"
            db.add(doc)
            await db.commit()
            print(f"[MockETL] Doc {doc.id}: UPLOADED → PROCESSING")

            # Step 2: Simulate ETL work — 大文件处理更久
            size_mb = doc.file_size / (1024 * 1024)
            delay = min(max(size_mb, 2), 15)  # 最少 2 秒, 最多 15 秒
            await asyncio.sleep(delay)

            # Step 3: PROCESSING → READY + preview extraction
            doc.status = "READY"
            if doc.preview_text is None and doc.file_ext in ("txt", "md", "csv", "json"):
                from src.engine import minio
                content = minio.get_object(doc.storage_object_key)
                if content:
                    try:
                        doc.preview_text = content.decode("utf-8")[:5000]
                    except UnicodeDecodeError:
                        doc.preview_text = content.decode("utf-8", errors="replace")[:5000]
            db.add(doc)
            await db.commit()
            await db.refresh(doc)
            print(f"[MockETL] Doc {doc.id}: PROCESSING → READY")


async def start_mock_etl_loop():
    """后台循环"""
    while True:
        try:
            await process_pending_documents()
        except Exception as e:
            print(f"[MockETL] Error: {e}")
            import traceback
            traceback.print_exc()
        await asyncio.sleep(5)
