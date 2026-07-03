"""RAG 问答服务 — 完整复刻 Java 实现

对照 Java:
    QaChatService.java         — RAG 编排、LLM 调用
    HybridChunkRetrievalService.java — RRF(k=0) 融合、聚类、证据评估
    QueryPlanningService.java  — LLM 查询规划 (DIRECT/REWRITE/DECOMPOSE)
    CitationAssembler.java     — 引用去重
    QaController.java          — SSE 流式格式
"""
import json
import re
import time
from sqlalchemy import text
from src.engine import llm
from src.engine.pgvector_search import vector_search
from src.database.session import async_session_factory
from src.prompts import QA_SYSTEM, QA_USER, QA_RAG_CONTEXT, QUERY_PLANNING_USER
from src.config import get_settings
from src.metrics.usage_recorder import record_llm_usage

# === 配置 ===
RRF_K = 0          # Java: RRF k=0 → 1/rank, 对 top 结果更激进
CHANNEL_TOP_K = 50
NEIGHBOR_WINDOW = 1
TOP_K = 5


# ============================================================
# 查询规划 (QueryPlanningService.java)
# ============================================================

QUERY_PLANNING_PROMPT = QUERY_PLANNING_USER


async def plan_query(question: str, user_id: int | None = None, group_id: int | None = None) -> list[str]:
    """LLM 查询规划 → 最多 3 条优化查询"""
    settings = get_settings()
    model_name = settings.ai_chat_model
    try:
        t0 = time.monotonic()
        resp = await llm.chat([
            {"role": "system", "content": "你是一个查询规划助手，只输出 JSON。"},
            {"role": "user", "content": QUERY_PLANNING_PROMPT.format(question=question)},
        ], max_tokens=300, temperature=0.0)
        latency_ms = int((time.monotonic() - t0) * 1000)
        usage = getattr(resp, "usage", None)
        # 记录查询规划 LLM 调用
        if user_id is not None:
            await record_llm_usage(
                user_id=user_id, group_id=group_id, module="QA",
                endpoint="qa/query-plan", model_name=model_name,
                prompt_tokens=usage.prompt_tokens if usage else 0,
                completion_tokens=usage.completion_tokens if usage else 0,
                total_tokens=usage.total_tokens if usage else 0,
                latency_ms=latency_ms, success=True,
            )
        raw = resp.choices[0].message.content or ""
        # 提取 JSON
        m = re.search(r'\{[\s\S]*\}', raw)
        if m:
            plan = json.loads(m.group(0))
            strategy = plan.get("strategy", "DIRECT")
            queries = plan.get("queries", [question])
            # normalize
            qs = list(dict.fromkeys([re.sub(r'\s+', ' ', q).strip() for q in queries if q.strip()]))[:3]
            if strategy == "DIRECT":
                return [question]
            elif strategy == "REWRITE":
                return ([question] + [q for q in qs if q != question])[:3]
            else:  # DECOMPOSE
                return qs if qs else [question]
    except Exception:
        pass
    return [question]  # fallback


# ============================================================
# ES 关键词检索 (ElasticsearchChunkIndexService.java)
# ============================================================

ES_INDEX = "dd_rag_document_chunks"


def keyword_search_java(query: str, group_id: int, top_k: int = 50) -> list[dict]:
    """ES 关键词检索 — 两阶段评分 + IK 中文分词

    复刻 Java: ElasticsearchChunkIndexService.search()
    """
    from elasticsearch import Elasticsearch
    from src.config import get_settings
    s = get_settings()
    try:
        es_url = f"{s.es_scheme}://{s.es_host}:{s.es_port}"
        if s.es_username and s.es_password:
            es = Elasticsearch(es_url, basic_auth=(s.es_username, s.es_password))
        else:
            es = Elasticsearch(es_url)
        body = {
            "size": top_k,
            "_source": ["groupId", "documentId", "chunkId", "chunkIndex", "fileName", "chunkText"],
            "query": {
                "bool": {
                    "filter": [
                        {"term": {"groupId": group_id}},
                        {"term": {"status": "READY"}},
                        {"term": {"deleted": False}},
                    ],
                    "should": [
                        {"match_phrase": {"fileName": {"query": query, "boost": 8}}},
                        {"match": {"fileName": {"query": query, "boost": 4}}},
                        {"match_phrase": {"chunkText": {"query": query, "boost": 6}}},
                        {"match": {"chunkText": {"query": query, "boost": 3}}},
                    ],
                    "minimum_should_match": 1,
                }
            },
            "rescore": {
                "window_size": top_k,
                "query": {
                    "query_weight": 0.2,
                    "rescore_query_weight": 1.0,
                    "score_mode": "total",
                    "rescore_query": {
                        "bool": {
                            "should": [
                                {"match_phrase": {"fileName": {"query": query, "boost": 8}}},
                                {"match": {"fileName": {"query": query, "operator": "and", "boost": 5}}},
                                {"match_phrase": {"chunkText": {"query": query, "boost": 7}}},
                                {"match": {"chunkText": {"query": query, "operator": "and", "boost": 4}}},
                            ],
                            "minimum_should_match": 1,
                        }
                    }
                }
            },
        }
        resp = es.search(index=ES_INDEX, body=body)
    except Exception:
        return []

    import math
    hits = []
    for h in resp["hits"]["hits"]:
        src = h["_source"]
        raw = h["_score"] or 0
        # normalizedScore = min(1.0, log1p(rawScore) / log1p(100.0))
        norm = min(1.0, math.log1p(raw) / math.log1p(100.0))
        hits.append({
            "document_id": src.get("documentId"),
            "chunk_id": src.get("chunkId"),
            "chunk_index": src.get("chunkIndex"),
            "chunk_text": src.get("chunkText", ""),
            "file_name": src.get("fileName", ""),
            "score": norm,
            "source": "KEYWORD",
        })
    return hits


# ============================================================
# RRF 融合 (HybridChunkRetrievalService.java)
# ============================================================

async def hybrid_retrieve(group_id: int, question: str, user_id: int | None = None) -> list[dict]:
    """混合检索: 查询规划 → 多查询并行检索 → RRF(k=0) 融合 → 聚类

    Returns list of dicts with: document_id, chunk_id, chunk_index, chunk_text,
    file_name, score, source, cluster_score
    """
    # 1. 查询规划
    planned_queries = await plan_query(question, user_id=user_id, group_id=group_id)

    # 2. 多查询并行检索
    all_vec_hits: list[dict] = []
    all_kw_hits: list[dict] = []

    for q in planned_queries:
        # 向量检索
        emb = await llm.get_embedding(q)
        vec_hits = await vector_search(emb, group_id, limit=CHANNEL_TOP_K, threshold=0.0)
        all_vec_hits.extend(vec_hits)

        # 关键词检索
        kw_hits = keyword_search_java(q, group_id, top_k=CHANNEL_TOP_K)
        all_kw_hits.extend(kw_hits)

    # 3. RRF(k=0) 融合
    candidates: dict[int, dict] = {}  # chunk_id → candidate

    def _rrf_score(rank: int) -> float:
        return 1.0 / (RRF_K + max(rank, 1))

    for idx, hit in enumerate(all_vec_hits):
        cid = hit.get("chunk_id") or hit.get("id") or f"v-{idx}"
        c = candidates.get(cid)
        if c is None:
            candidates[cid] = {
                "document_id": hit.get("document_id"),
                "chunk_id": cid,
                "chunk_index": hit.get("chunk_index", 0),
                "chunk_text": hit.get("content") or hit.get("chunk_text", ""),
                "file_name": hit.get("file_name", ""),
                "vector_score": hit.get("score", 0),
                "keyword_score": 0,
                "rrf_score": _rrf_score(idx + 1),
                "vector_matched": True,
                "keyword_matched": False,
            }
        else:
            c["rrf_score"] += _rrf_score(idx + 1)
            c["vector_score"] = max(c["vector_score"], hit.get("score", 0))

    for idx, hit in enumerate(all_kw_hits):
        cid = hit.get("chunk_id") or hit.get("document_id") or f"k-{idx}"
        c = candidates.get(cid)
        if c is None:
            candidates[cid] = {
                "document_id": hit.get("document_id"),
                "chunk_id": cid,
                "chunk_index": hit.get("chunk_index", 0),
                "chunk_text": hit.get("chunk_text", ""),
                "file_name": hit.get("file_name", ""),
                "vector_score": 0,
                "keyword_score": hit.get("score", 0),
                "rrf_score": _rrf_score(idx + 1),
                "vector_matched": False,
                "keyword_matched": True,
            }
        else:
            c["rrf_score"] += _rrf_score(idx + 1)
            c["keyword_score"] = max(c["keyword_score"], hit.get("score", 0))

    # 4. 排序 + 归一化
    import math
    ranked = sorted(candidates.values(),
                    key=lambda x: (-x["rrf_score"], x.get("chunk_index", 0) or 0))

    for c in ranked:
        # normalizedScore = 1 - exp(-rawRrfScore)
        c["score"] = 1.0 - math.exp(-c["rrf_score"])
        c["source"] = ("BOTH" if (c["vector_matched"] and c["keyword_matched"])
                       else "VECTOR" if c["vector_matched"] else "KEYWORD")

    # 5. 聚类连续 chunk + 窗口扩展 → 构建 evidence documents
    evidence = await _build_evidence_documents(ranked[:TOP_K * 2], group_id, TOP_K)

    # 6. 回退: 无结果时用数据库文本搜索
    if not evidence:
        evidence = await _fallback_db_search(group_id, planned_queries[0], TOP_K)

    return evidence


async def _fallback_db_search(group_id: int, query: str, top_k: int) -> list[dict]:
    """DB 全文回退: 向量/ES 都无结果时，直接搜索 document_chunks + documents"""
    async with async_session_factory() as db:
        result = await db.execute(text("""
            SELECT dc.document_id, dc.id as chunk_id, dc.chunk_index, dc.chunk_text,
                   d.file_name
            FROM document_chunks dc
            JOIN documents d ON d.id = dc.document_id
            WHERE dc.group_id = :gid AND d.deleted = false AND d.status = 'READY'
              AND (dc.chunk_text ILIKE :q OR d.file_name ILIKE :q)
            ORDER BY dc.id DESC
            LIMIT :limit
        """), {"gid": group_id, "q": f"%{query}%", "limit": top_k * 3})

        rows = result.fetchall()
        if not rows:
            # 更宽松的搜索
            result = await db.execute(text("""
                SELECT dc.document_id, dc.id as chunk_id, dc.chunk_index, dc.chunk_text,
                       d.file_name
                FROM document_chunks dc
                JOIN documents d ON d.id = dc.document_id
                WHERE dc.group_id = :gid AND d.deleted = false
                ORDER BY dc.id DESC
                LIMIT :limit
            """), {"gid": group_id, "limit": top_k * 3})
            rows = result.fetchall()

        if not rows:
            # 直接从 documents 表获取预览文本
            result = await db.execute(text("""
                SELECT id, file_name, file_ext, preview_text
                FROM documents
                WHERE group_id = :gid AND deleted = false AND status = 'READY'
                LIMIT :limit
            """), {"gid": group_id, "limit": top_k})
            docs = result.fetchall()
            return [{
                "document_id": d[0], "primary_chunk_id": None, "primary_chunk_index": 0,
                "file_name": d[1] or "unnamed", "chunk_text": d[3] or "",
                "start_chunk_index": 0, "end_chunk_index": 0,
                "score": 0.3, "source": "DB_FALLBACK",
            } for d in docs]

        return [{
            "document_id": r[0], "primary_chunk_id": r[1], "primary_chunk_index": r[2],
            "file_name": r[4] or "unnamed", "chunk_text": r[3] or "",
            "start_chunk_index": max(0, (r[2] or 0) - 1), "end_chunk_index": (r[2] or 0) + 1,
            "score": 0.3, "source": "DB_FALLBACK",
        } for r in rows]


async def _fallback_db_search_loose(group_id: int, top_k: int) -> list[dict]:
    """宽松回退: 取群组最新文档"""
    async with async_session_factory() as db:
        result = await db.execute(text("""
            SELECT id, file_name, file_ext, preview_text
            FROM documents
            WHERE group_id = :gid AND deleted = false AND status = 'READY'
              AND preview_text IS NOT NULL AND preview_text != ''
            ORDER BY id DESC LIMIT :limit
        """), {"gid": group_id, "limit": top_k})
        docs = result.fetchall()
        return [{
            "document_id": d[0], "primary_chunk_id": None, "primary_chunk_index": 0,
            "file_name": d[1] or "unnamed",
            "start_chunk_index": 0, "end_chunk_index": 0,
            "score": 0.25, "source": "DB_FALLBACK",
            "chunk_text": d[3] or "",
        } for d in docs]


async def _build_evidence_documents(candidates: list[dict], group_id: int, top_k: int) -> list[dict]:
    """聚类 + 邻居窗口扩展 → 证据文档列表

    复刻: HybridChunkRetrievalService.buildClusters() + 窗口扩展
    """
    if not candidates:
        return []

    # 按 document_id 分组
    doc_groups: dict[int, list[dict]] = {}
    for c in candidates:
        did = c.get("document_id")
        if did is not None:
            doc_groups.setdefault(did, []).append(c)

    # 每个 document 内按 chunk_index 排序并聚类
    clusters: list[dict] = []
    for did, items in doc_groups.items():
        items.sort(key=lambda x: (x.get("chunk_index", 0) or 0))
        doc_clusters: list[list[dict]] = []
        for item in items:
            ci = item.get("chunk_index", 0) or 0
            if not doc_clusters or ci != (doc_clusters[-1][-1].get("chunk_index", 0) or 0) + 1:
                doc_clusters.append([item])
            else:
                doc_clusters[-1].append(item)

        # 计算每个 cluster 的元数据
        for cl in doc_clusters:
            max_rrf = max(c["rrf_score"] for c in cl)
            max_vec = max(c.get("vector_score", 0) for c in cl)
            max_kw = max(c.get("keyword_score", 0) for c in cl)
            sources = {c.get("source", "") for c in cl}
            src_str = "BOTH" if sources >= {"VECTOR", "KEYWORD"} else ("VECTOR" if "VECTOR" in sources else "KEYWORD")

            primary = cl[0]
            start_ci = max(0, (primary.get("chunk_index", 0) or 0) - NEIGHBOR_WINDOW)
            end_ci = (cl[-1].get("chunk_index", 0) or 0) + NEIGHBOR_WINDOW

            # 查询数据库获取扩展窗口的实际 chunk 文本
            clusters.append({
                "document_id": did,
                "primary_chunk_id": primary.get("chunk_id"),
                "primary_chunk_index": primary.get("chunk_index", 0),
                "start_chunk_index": start_ci,
                "end_chunk_index": end_ci,
                "file_name": primary.get("file_name", ""),
                "rrf_score": max_rrf,
                "score": 1.0 - __import__("math").exp(-max_rrf),
                "vector_score": max_vec,
                "keyword_score": max_kw,
                "source": src_str,
            })

    # 排序: score DESC → chunk_id ASC
    clusters.sort(key=lambda x: (-x["score"], x.get("primary_chunk_id", 0) or 0))
    return clusters[:top_k]


async def _load_window_text(doc: dict, group_id: int) -> str:
    """加载证据文本"""
    if doc.get("source") == "DB_FALLBACK":
        chunk_txt = doc.get("chunk_text", "") or ""
        if chunk_txt.strip():
            return chunk_txt
        # chunk_text 为空时，尝试读取原文 (支持 PDF 提取)
        did = doc.get("document_id")
        if did:
            async with async_session_factory() as db:
                row = (await db.execute(text(
                    "SELECT storage_bucket, storage_object_key, file_ext FROM documents WHERE id=:id"
                ), {"id": did})).fetchone()
                if row:
                    bucket, key, ext = row[0], row[1], row[2]
                    content = None
                    # 1. MinIO
                    try:
                        from src.engine import minio; content = minio.get_object(key)
                    except Exception: pass
                    # 2. 本地
                    if not content:
                        from pathlib import Path
                        p = Path("uploads") / key
                        if p.exists(): content = p.read_bytes()
                    if content:
                        if ext in ("txt", "md", "csv", "json"):
                            try: return content.decode("utf-8")[:8000]
                            except UnicodeDecodeError: return content.decode("utf-8", errors="replace")[:5000]
                        if ext == "pdf":
                            try:
                                import fitz
                                pdf = fitz.open(stream=content, filetype="pdf")
                                pdf_txt = "".join(page.get_text() for page in pdf)
                                pdf.close()
                                if pdf_txt.strip():
                                    await db.execute(text("UPDATE documents SET preview_text=:pt WHERE id=:id"), {"pt": pdf_txt[:5000], "id": did})
                                    await db.commit()
                                    return pdf_txt[:8000]
                            except Exception: pass
        return f"[文件: {doc.get('file_name', '未知')}, 该文件暂未提取文本内容，请等待 ETL 处理完成]"
    async with async_session_factory() as db:
        result = await db.execute(text("""
            SELECT chunk_text FROM document_chunks
            WHERE document_id = :did AND group_id = :gid
              AND chunk_index BETWEEN :start AND :end
            ORDER BY chunk_index
        """), {
            "did": doc["document_id"],
            "gid": group_id,
            "start": doc["start_chunk_index"],
            "end": doc["end_chunk_index"],
        })
        parts = [row[0] for row in result.fetchall()]
        return "\n".join(parts)


# ============================================================
# 证据评估 (HybridChunkRetrievalService.evaluateEvidenceLevel)
# ============================================================

def _evaluate_evidence(documents: list[dict]) -> tuple[str, str]:
    """四级证据评估

    Returns: (evidenceLevel, evidenceGuidance)
    """
    if not documents:
        return "NONE", "当前没有可用证据，必须直接拒答。"

    sources = {d.get("source", "") for d in documents}
    has_both = "BOTH" in sources
    has_vector = "VECTOR" in sources or "BOTH" in sources
    top_score = max((d.get("score", 0) for d in documents), default=0)

    if len(documents) >= 2 and (has_both or (has_vector and top_score >= 0.85)):
        return "SUFFICIENT", "当前证据较充分，可以正常回答，但仍然不得超出证据进行臆测。"
    if has_both or len(documents) >= 2:
        return "PARTIAL", "当前证据只覆盖部分问题，只能回答证据明确支持的部分，未覆盖部分必须明确说明不足。"
    return "WEAK", "当前证据相关性有限，只能谨慎回答，必须明确说明依据有限，不能给出确定性结论。"


# ============================================================
# 引用组装 (CitationAssembler.java)
# ============================================================

def _build_citations(documents: list[dict]) -> list[dict]:
    """引用去重 — 按 fileName 保留首次出现"""
    seen = {}
    for d in documents:
        fn = d.get("file_name", "")
        if fn and fn not in seen:
            seen[fn] = {
                "documentId": d.get("document_id"),
                "chunkId": d.get("primary_chunk_id"),
                "chunkIndex": d.get("primary_chunk_index"),
                "fileName": fn,
                "score": round(d.get("score", 0), 4),
                "snippet": None,
            }
    return list(seen.values())


# ============================================================
# 回答生成 (QaChatService.java)
# ============================================================

SYSTEM_PROMPT_STRUCTURED = QA_SYSTEM
SYSTEM_PROMPT_STREAMING = """你是群组知识问答助手，只能依据给定证据回答，不得补充外部知识或猜测。请直接输出纯文本回答正文，使用简体中文。不要输出 JSON、Markdown 等任何格式标记。"""
USER_PROMPT_TEMPLATE = QA_USER
RAG_CONTEXT_TEMPLATE = QA_RAG_CONTEXT



# ============================================================
# API 入口 (QaChatService.askWithUsage + askStream)
# ============================================================

async def ask_question(group_id: int, question: str, user_id: int | None = None) -> dict:
    """同步问答 — 全文检索 → 证据评估 → LLM 生成 → 引用组装

    对照: QaChatService.askWithUsage()
    """
    t0 = time.monotonic()
    settings = get_settings()
    model_name = settings.ai_chat_model

    # 1. 混合检索 + 聚类 + 证据评估
    evidence_docs = await hybrid_retrieve(group_id, question, user_id=user_id)
    evidence_level, evidence_guidance = _evaluate_evidence(evidence_docs)

    # NONE → 检查群组是否有文档，有则强制用 DB 回退再试
    if evidence_level == "NONE":
        async with async_session_factory() as db:
            cnt = (await db.execute(text("SELECT count(*) FROM documents WHERE group_id=:gid AND deleted=false"),
                                     {"gid": group_id})).scalar()
        if not cnt:
            return {
                "answered": False, "answer": None,
                "reasonCode": "NO_DOCUMENTS",
                "reasonMessage": "该群组还没有文档，请先上传文档后再提问。",
                "citations": [],
            }
        # 有文档但没匹配到，用宽松匹配再试
        evidence_docs = await _fallback_db_search_loose(group_id, TOP_K)
        if not evidence_docs:
            return {
                "answered": False, "answer": None,
                "reasonCode": "NO_EVIDENCE",
                "reasonMessage": "未检索到相关文档内容，尝试换一种问法或上传更多相关资料。",
                "citations": [],
            }
        evidence_level = "WEAK"
        evidence_guidance = "当前证据相关性有限，只能谨慎回答，必须明确说明依据有限，不能给出确定性结论。"

    # 2. 构建证据上下文 (Java: buildEvidenceWindow + rag-context.st)
    # Java 格式: "E{N} 文件名：{fileName}\n{chunk texts}"
    evidence_parts = []
    for i, doc in enumerate(evidence_docs):
        window_text = await _load_window_text(doc, group_id)
        fname = doc.get("file_name", "未知")
        evidence_parts.append(f"E{i+1} 文件名：{fname}\n{window_text}")
    evidence_context = "\n".join(evidence_parts)

    # Java: ContextualQueryAugmenter 将 rag-context.st + user.st 合并为同一条 USER 消息
    full_user = RAG_CONTEXT_TEMPLATE.format(query=question, context=evidence_context)

    full_user += "\n\n" + USER_PROMPT_TEMPLATE.format(
        question=question,
        evidenceLevel=evidence_level,
        evidenceGuidance=evidence_guidance,
    )

    # 3. LLM 生成 (结构化 JSON 输出)
    try:
        t_ask = time.monotonic()
        resp = await llm.chat([
            {"role": "system", "content": SYSTEM_PROMPT_STRUCTURED},
            {"role": "user", "content": full_user},
        ], temperature=0.0, max_tokens=2048)
        latency_ms = int((time.monotonic() - t_ask) * 1000)
        raw_answer = resp.choices[0].message.content or ""
        # 记录主生成 LLM 调用
        if user_id is not None:
            usage = getattr(resp, "usage", None)
            await record_llm_usage(
                user_id=user_id, group_id=group_id, module="QA",
                endpoint="qa/ask", model_name=model_name,
                prompt_tokens=usage.prompt_tokens if usage else 0,
                completion_tokens=usage.completion_tokens if usage else 0,
                total_tokens=usage.total_tokens if usage else 0,
                latency_ms=latency_ms, success=True,
            )
    except Exception as e:
        if user_id is not None:
            latency_ms = int((time.monotonic() - t_ask) * 1000)
            await record_llm_usage(
                user_id=user_id, group_id=group_id, module="QA",
                endpoint="qa/ask", model_name=model_name,
                latency_ms=latency_ms, success=False,
                error_message=str(e)[:500],
            )
        return {
            "answered": False, "answer": None,
            "reasonCode": "LLM_ERROR",
            "reasonMessage": f"模型调用失败: {str(e)[:200]}",
            "citations": _build_citations(evidence_docs),
        }

    # 4. 解析 JSON 输出
    output = _parse_structured_output(raw_answer)

    # 5. 回退: 再调一次 LLM 用纯文本解析
    if output is None:
        try:
            t_retry = time.monotonic()
            resp2 = await llm.chat([
                {"role": "system", "content": SYSTEM_PROMPT_STRUCTURED},
                {"role": "user", "content": full_user},
            ], temperature=0.0, max_tokens=1024)
            latency_ms2 = int((time.monotonic() - t_retry) * 1000)
            output = _parse_structured_output(resp2.choices[0].message.content or "")
            # 记录重试 LLM 调用
            if user_id is not None:
                usage2 = getattr(resp2, "usage", None)
                await record_llm_usage(
                    user_id=user_id, group_id=group_id, module="QA",
                    endpoint="qa/ask-retry", model_name=model_name,
                    prompt_tokens=usage2.prompt_tokens if usage2 else 0,
                    completion_tokens=usage2.completion_tokens if usage2 else 0,
                    total_tokens=usage2.total_tokens if usage2 else 0,
                    latency_ms=latency_ms2, success=True,
                )
        except Exception:
            pass

    if output is None:
        return {
            "answered": False, "answer": None,
            "reasonCode": "ANSWER_FORMAT_ERROR",
            "reasonMessage": "模型输出格式异常，无法解析回答。",
            "citations": _build_citations(evidence_docs),
        }

    if not output.get("answered", False) or not (output.get("answer") or "").strip():
        return {
            "answered": False, "answer": None,
            "reasonCode": output.get("reasonCode", "INSUFFICIENT_EVIDENCE"),
            "reasonMessage": output.get("reasonMessage", "证据不足以给出可靠回答。"),
            "citations": _build_citations(evidence_docs),
        }

    return {
        "answered": True,
        "answer": output["answer"].strip(),
        "reasonCode": None, "reasonMessage": None,
        "citations": _build_citations(evidence_docs),
    }


def _parse_structured_output(raw: str) -> dict | None:
    """解析 LLM 输出的 JSON"""
    if not raw:
        return None
    m = re.search(r'\{[\s\S]*\}', raw)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


async def stream_ask(group_id: int, question: str, user_id: int | None = None):
    """流式问答 — 检索 → 纯文本 LLM 流 → 引用

    对照: QaChatService.askStream() + QaController event format
    """
    # 1. 检索
    evidence_docs = await hybrid_retrieve(group_id, question, user_id=user_id)
    evidence_level, evidence_guidance = _evaluate_evidence(evidence_docs)

    if evidence_level == "NONE":
        yield _sse("error", json.dumps({"message": "未检索到相关文档"}, ensure_ascii=False))
        return

    # 2. 证据上下文 (Java: buildEvidenceWindow + rag-context.st)
    evidence_parts = []
    for i, doc in enumerate(evidence_docs):
        window_text = await _load_window_text(doc, group_id)
        fname = doc.get("file_name", "未知")
        evidence_parts.append(f"E{i+1} 文件名：{fname}\n{window_text}")
    evidence_context = "\n".join(evidence_parts)

    # Java: ContextualQueryAugmenter 将 rag-context.st + user.st 合并为同一条 USER 消息
    full_user = RAG_CONTEXT_TEMPLATE.format(query=question, context=evidence_context)
    full_user += "\n\n" + USER_PROMPT_TEMPLATE.format(
        question=question,
        evidenceLevel=evidence_level,
        evidenceGuidance=evidence_guidance,
    )

    # 3. 流式 LLM
    try:
        stream = await llm.chat([
            {"role": "system", "content": SYSTEM_PROMPT_STREAMING},
            {"role": "user", "content": full_user},
        ], stream=True, temperature=0.0, max_tokens=2048)

        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield _sse("token", delta.content)

    except Exception as e:
        yield _sse("error", json.dumps({"message": str(e)[:200]}, ensure_ascii=False))
        return

    # 4. 引用
    citations = _build_citations(evidence_docs)
    if citations:
        yield _sse("citations", json.dumps(citations, ensure_ascii=False))


def _sse(event: str, data: str) -> str:
    return f"event: {event}\ndata: {data}\n\n"
