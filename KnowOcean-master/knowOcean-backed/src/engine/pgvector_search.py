"""pgvector 向量检索引擎

对照 Java: engine/pgvector/PgVectorRetrievalAdapter.java
"""
from sqlalchemy import text
from src.database.session import async_session_factory


async def vector_search(
    embedding: list[float],
    group_id: int | None = None,
    limit: int = 10,
    threshold: float = 0.3,
) -> list[dict]:
    """向量相似度检索 — COSINE_DISTANCE + HNSW 索引

    对照 Java: PgVectorRetrievalAdapter.search(embedding, groupId)
    """
    async with async_session_factory() as db:
        vector_str = f"[{','.join(str(x) for x in embedding)}]"

        if group_id:
            query = text("""
                SELECT
                    vs.id, vs.content, vs.metadata,
                    1 - (vs.embedding <=> :embedding) AS score
                FROM vector_store vs
                WHERE 1 - (vs.embedding <=> :embedding) >= :threshold
                  AND vs.metadata->>'groupId' = :group_id
                ORDER BY vs.embedding <=> :embedding
                LIMIT :limit
            """)
            result = await db.execute(query, {
                "embedding": vector_str,
                "group_id": str(group_id),
                "threshold": threshold,
                "limit": limit,
            })
        else:
            query = text("""
                SELECT
                    vs.id, vs.content, vs.metadata,
                    1 - (vs.embedding <=> :embedding) AS score
                FROM vector_store vs
                WHERE 1 - (vs.embedding <=> :embedding) >= :threshold
                ORDER BY vs.embedding <=> :embedding
                LIMIT :limit
            """)
            result = await db.execute(query, {
                "embedding": vector_str,
                "threshold": threshold,
                "limit": limit,
            })

        results = []
        for row in result.all():
            meta = row[2] or {}
            results.append({
                "id": row[0],
                "content": row[1],
                "metadata": meta,
                "score": float(row[3]),
                "source": "pgvector",
                "document_id": (meta.get("documentId") or meta.get("document_id")) if isinstance(meta, dict) else None,
                "chunk_index": (meta.get("chunkIndex") or meta.get("chunk_index")) if isinstance(meta, dict) else None,
                "file_name": meta.get("fileName") if isinstance(meta, dict) else None,
            })
        return results
