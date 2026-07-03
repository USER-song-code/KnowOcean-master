"""AI 助手模块 — 会话管理 + 流式对话"""
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.session import get_db
from src.auth.dependencies import require_auth
from src.common.response import ApiResponse
from src.common.security import UserIdentity
from src.assistant import service as assistant_service

router = APIRouter(prefix="/api/assistant", tags=["Assistant"])


class ChatPayload(BaseModel):
    sessionId: int
    message: str
    toolMode: str = "CHAT"
    groupId: int | None = None


# ── 会话管理 ──

@router.post("/sessions")
async def create_session(
    user: UserIdentity = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    data = await assistant_service.create_session(user.user_id)
    return ApiResponse.ok(data=data)


@router.get("/sessions")
async def list_sessions(
    user: UserIdentity = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    data = await assistant_service.list_sessions(user.user_id)
    return ApiResponse.ok(data=data)


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: int,
    user: UserIdentity = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    data = await assistant_service.get_session(session_id)
    if data is None:
        return ApiResponse.fail(code=404, message="会话不存在")
    return ApiResponse.ok(data=data)


@router.patch("/sessions/{session_id}")
async def rename_session(
    session_id: int,
    body: dict,
    user: UserIdentity = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    title = body.get("title", "").strip()
    if not title or len(title) > 255:
        return ApiResponse.fail(code=400, message="标题无效")
    ok = await assistant_service.rename_session(session_id, title)
    if not ok:
        return ApiResponse.fail(code=404, message="会话不存在")
    return ApiResponse.ok(message="OK")


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: int,
    user: UserIdentity = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    ok = await assistant_service.delete_session(session_id)
    if not ok:
        return ApiResponse.fail(code=404, message="会话不存在")
    return ApiResponse.ok(message="OK")


@router.get("/sessions/{session_id}/context")
async def get_session_context(
    session_id: int,
    recentLimit: int = Query(12, alias="recentLimit"),
    user: UserIdentity = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    data = await assistant_service.get_session_context(session_id, recentLimit)
    return ApiResponse.ok(data=data)


# ── 聊天 ──

@router.post("/chat")
async def assistant_chat(
    body: ChatPayload,
    user: UserIdentity = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """非流式聊天 — 收集完整回复后返回"""
    full_reply = ""
    msg_id = None
    async for event_str in assistant_service.stream_chat(
        session_id=body.sessionId, message=body.message,
        tool_mode=body.toolMode, group_id=body.groupId,
        user_id=user.user_id,
    ):
        # 解析 SSE 收集结果
        if "data:" in event_str:
            try:
                idx = event_str.index("data:") + 5
                obj = __import__("json").loads(event_str[idx:].strip())
                if obj.get("event") == "done":
                    full_reply = obj.get("reply", "")
                    msg_id = obj.get("messageId")
                elif obj.get("event") == "delta":
                    full_reply += obj.get("delta", "")
                elif obj.get("event") == "error":
                    return ApiResponse.fail(code=500, message=obj.get("error", "AI 调用失败"))
            except Exception:
                pass

    return ApiResponse.ok(data={
        "sessionId": body.sessionId, "messageId": msg_id, "reply": full_reply,
        "toolMode": body.toolMode, "groupId": body.groupId, "citations": [],
    })


@router.post("/chat/stream")
async def assistant_chat_stream(
    body: ChatPayload,
    user: UserIdentity = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """流式聊天 — SSE 实时推送"""

    async def event_stream():
        async for event in assistant_service.stream_chat(
            session_id=body.sessionId, message=body.message,
            tool_mode=body.toolMode, group_id=body.groupId,
            user_id=user.user_id,
        ):
            yield event

    return StreamingResponse(event_stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
