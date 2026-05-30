"""LLM 调用引擎 — DashScope (OpenAI 兼容模式)

Chat: deepseek-v4-pro
Embedding: text-embedding-v3 (512 dims)
"""
from openai import AsyncOpenAI
from src.config import get_settings

settings = get_settings()

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        base = settings.dashscope_base_url.rstrip("/")
        if not base.endswith("/v1"):
            base += "/v1"
        _client = AsyncOpenAI(api_key=settings.dashscope_api_key, base_url=base)
    return _client


async def get_embedding(text: str) -> list[float]:
    """生成文本向量 (text-embedding-v3, 512 dims)"""
    client = _get_client()
    # DashScope compatible mode: dimension may not be supported
    try:
        resp = await client.embeddings.create(
            model=settings.ai_embedding_model,
            input=text,
            dimensions=512,
        )
    except Exception:
        resp = await client.embeddings.create(
            model=settings.ai_embedding_model,
            input=text,
        )
    return resp.data[0].embedding


async def chat(messages: list[dict], stream: bool = False, **kwargs):
    """调用 Chat 模型"""
    client = _get_client()
    return await client.chat.completions.create(
        model=settings.ai_chat_model,
        messages=messages,
        stream=stream,
        temperature=kwargs.get("temperature", 0.3),
        max_tokens=kwargs.get("max_tokens", 2048),
    )
