"""AI 助手服务 — 会话管理 + 流式聊天

使用 assistant_sessions、assistant_messages 表持久化。
"""
import json
import logging
import time
from datetime import datetime, timezone
from sqlalchemy import text
from src.database.session import async_session_factory
from src.engine import llm
from src.config import get_settings
from src.metrics.usage_recorder import record_llm_usage

logger = logging.getLogger(__name__)
settings = get_settings()

SYSTEM_PROMPT = """你是一个智能 AI 助手，名叫 KnowOcean。你可以帮助用户解答各种问题。
请用简洁、准确的中文回答。如果用户要求搜索知识库，请在回答中说明当前暂不支持联网搜索，
但可以基于你的训练数据提供帮助。"""


async def create_session(user_id: int) -> dict:
    """创建新会话"""
    now = datetime.now(timezone.utc)
    async with async_session_factory() as db:
        result = await db.execute(
            text("""INSERT INTO assistant_sessions (user_id, title, status, last_message_at, created_at, updated_at)
                    VALUES (:uid, '新会话', 'ACTIVE', :now, :now, :now) RETURNING id"""),
            {"uid": user_id, "now": now},
        )
        sid = result.scalar_one()
        await db.commit()
        return {"sessionId": sid, "title": "新会话", "status": "ACTIVE", "lastMessageAt": None, "createdAt": now.isoformat()}


async def list_sessions(user_id: int) -> list[dict]:
    """列出用户的所有会话"""
    async with async_session_factory() as db:
        result = await db.execute(
            text("""SELECT id, title, status, last_message_at, created_at
                    FROM assistant_sessions
                    WHERE user_id = :uid AND status != 'DELETED'
                    ORDER BY last_message_at DESC NULLS LAST, created_at DESC"""),
            {"uid": user_id},
        )
        rows = result.fetchall()
        return [
            {
                "sessionId": r.id, "title": r.title, "status": r.status,
                "lastMessageAt": r.last_message_at.isoformat() if r.last_message_at else None,
                "createdAt": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]


async def get_session(session_id: int) -> dict | None:
    """获取单个会话详情"""
    async with async_session_factory() as db:
        row = (await db.execute(
            text("SELECT id, title, status, last_message_at, created_at FROM assistant_sessions WHERE id = :sid"),
            {"sid": session_id},
        )).fetchone()
        if not row:
            return None
        return {
            "sessionId": row.id, "title": row.title, "status": row.status,
            "lastMessageAt": row.last_message_at.isoformat() if row.last_message_at else None,
            "createdAt": row.created_at.isoformat() if row.created_at else None,
        }


async def rename_session(session_id: int, title: str) -> bool:
    """重命名会话"""
    async with async_session_factory() as db:
        result = await db.execute(
            text("UPDATE assistant_sessions SET title = :t, updated_at = :now WHERE id = :sid"),
            {"t": title, "sid": session_id, "now": datetime.utcnow()},
        )
        await db.commit()
        return result.rowcount > 0


async def delete_session(session_id: int) -> bool:
    """软删除会话"""
    async with async_session_factory() as db:
        result = await db.execute(
            text("UPDATE assistant_sessions SET status = 'DELETED', updated_at = :now WHERE id = :sid"),
            {"sid": session_id, "now": datetime.utcnow()},
        )
        await db.commit()
        return result.rowcount > 0


async def get_session_context(session_id: int, recent_limit: int = 12) -> dict:
    """获取会话上下文（最近消息）"""
    async with async_session_factory() as db:
        result = await db.execute(
            text("""SELECT role, tool_mode, group_id, content, structured_payload, created_at
                    FROM assistant_messages
                    WHERE session_id = :sid
                    ORDER BY created_at ASC
                    LIMIT :lim"""),
            {"sid": session_id, "lim": recent_limit},
        )
        rows = result.fetchall()
        messages = []
        msg_id = 0
        for r in rows:
            msg_id += 1
            messages.append({
                "messageId": msg_id, "sessionId": session_id, "role": r.role,
                "toolMode": r.tool_mode, "groupId": r.group_id,
                "content": r.content or "", "structuredPayload": r.structured_payload,
                "createdAt": r.created_at.isoformat() if r.created_at else None,
            })
        return {"summaryText": None, "recentMessages": messages}


async def _save_message(session_id: int, role: str, content: str, tool_mode: str = "CHAT", group_id: int | None = None) -> int:
    """保存一条消息，返回 message_id"""
    now = datetime.now(timezone.utc)
    async with async_session_factory() as db:
        result = await db.execute(
            text("""INSERT INTO assistant_messages (session_id, role, tool_mode, group_id, content, created_at)
                    VALUES (:sid, :role, :mode, :gid, :content, :now) RETURNING id"""),
            {"sid": session_id, "role": role, "mode": tool_mode, "gid": group_id, "content": content, "now": now},
        )
        mid = result.scalar_one()
        await db.execute(
            text("UPDATE assistant_sessions SET last_message_at = :now, updated_at = :now WHERE id = :sid"),
            {"now": now, "sid": session_id},
        )
        await db.commit()
        return mid


async def _rename_by_content(session_id: int, message: str):
    """用用户第一条消息自动命名会话"""
    title = message[:30].replace("\n", " ").strip()
    if len(message) > 30:
        title += "…"
    async with async_session_factory() as db:
        await db.execute(
            text("UPDATE assistant_sessions SET title = :t WHERE id = :sid AND title = '新会话'"),
            {"t": title, "sid": session_id},
        )
        await db.commit()


async def stream_chat(session_id: int, message: str, tool_mode: str = "CHAT", group_id: int | None = None, user_id: int | None = None):
    """流式聊天生成器 — SSE 格式"""
    model_name = settings.ai_chat_model
    t0 = time.monotonic()

    # 保存用户消息
    await _save_message(session_id, "USER", message, tool_mode, group_id)
    # 自动命名
    await _rename_by_content(session_id, message)

    # 加载历史
    history = []
    async with async_session_factory() as db:
        result = await db.execute(
            text("SELECT role, content FROM assistant_messages WHERE session_id = :sid ORDER BY created_at ASC LIMIT 50"),
            {"sid": session_id},
        )
        for r in result.fetchall():
            history.append({"role": r.role.lower(), "content": r.content})

    # 构建消息列表
    messages_list = [{"role": "system", "content": SYSTEM_PROMPT}]
    for h in history[-20:]:  # 最近 20 条
        role = "assistant" if h["role"] == "ASSISTANT" else "user"
        messages_list.append({"role": role, "content": h["content"]})

    logger.info(f"[Assistant] stream_chat start: session={session_id}, msg={message[:50]}...")

    # 发送 start 事件
    yield _sse("start", json.dumps({
        "event": "start", "sessionId": session_id,
        "toolMode": tool_mode, "groupId": group_id,
        "delta": None, "messageId": None, "reply": None, "citations": [],
        "error": None,
    }, ensure_ascii=False))

    full_reply = ""
    success = True
    error_msg = None

    try:
        stream = await llm.chat(messages_list, stream=True, temperature=0.3, max_tokens=2048)
        logger.info(f"[Assistant] LLM stream started, model={model_name}")
        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                full_reply += delta.content
                yield _sse("delta", json.dumps({
                    "event": "delta", "sessionId": session_id,
                    "toolMode": tool_mode, "groupId": group_id,
                    "delta": delta.content, "messageId": None, "reply": None,
                    "citations": [], "error": None,
                }, ensure_ascii=False))

    except Exception as e:
        success = False
        error_msg = str(e)[:500]
        yield _sse("error", json.dumps({
            "event": "error", "sessionId": session_id,
            "toolMode": tool_mode, "groupId": group_id,
            "delta": None, "messageId": None, "reply": None, "citations": [],
            "error": error_msg,
        }, ensure_ascii=False))
        return

    finally:
        latency_ms = int((time.monotonic() - t0) * 1000)
        if user_id:
            est_tokens = max(1, len(full_reply) // 2)
            await record_llm_usage(
                user_id=user_id, group_id=group_id, module="ASSISTANT",
                endpoint="assistant/chat/stream", model_name=model_name,
                prompt_tokens=len(message) // 2, completion_tokens=est_tokens,
                total_tokens=len(message) // 2 + est_tokens,
                is_estimated=True, latency_ms=latency_ms, success=success,
                error_message=error_msg, session_id=str(session_id),
            )

    if success and full_reply:
        msg_id = await _save_message(session_id, "ASSISTANT", full_reply, tool_mode, group_id)
        yield _sse("done", json.dumps({
            "event": "done", "sessionId": session_id,
            "toolMode": tool_mode, "groupId": group_id,
            "delta": None, "messageId": msg_id, "reply": full_reply,
            "citations": [], "error": None,
        }, ensure_ascii=False))


def _sse(event: str, data: str) -> str:
    return f"event: {event}\ndata: {data}\n\n"
