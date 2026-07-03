"""Elasticsearch 检索引擎

对照 Java: engine/elasticsearch/ElasticsearchChunkIndexService.java
"""
from elasticsearch import Elasticsearch
from src.config import get_settings

settings = get_settings()


def get_es_client() -> Elasticsearch:
    return Elasticsearch(f"http://{settings.es_host}:{settings.es_port}")


def keyword_search(query: str, group_id: int, size: int = 10) -> list[dict]:
    """ES 关键词检索 — BM25 + IK 中文分词

    对照 Java: ElasticsearchChunkIndexService.search(query, groupId)
    """
    client = get_es_client()
    try:
        resp = client.search(
            index="document_chunks",
            body={
                "query": {
                    "bool": {
                        "must": [
                            {"match": {"chunk_text": {"query": query, "operator": "and"}}},
                        ],
                        "filter": [
                            {"term": {"group_id": group_id}},
                        ],
                    }
                },
                "size": size,
                "_source": ["document_id", "chunk_index", "chunk_text", "group_id", "file_name"],
            },
        )
    except Exception:
        # Index may not exist
        return []

    results = []
    for hit in resp["hits"]["hits"]:
        src = hit["_source"]
        results.append({
            "document_id": src.get("document_id"),
            "chunk_index": src.get("chunk_index"),
            "chunk_text": src.get("chunk_text", ""),
            "group_id": src.get("group_id"),
            "file_name": src.get("file_name", ""),
            "score": hit["_score"],
            "source": "es",
        })
    return results
