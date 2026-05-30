"""AI 助手模块 (stub)"""
from fastapi import APIRouter, Depends
from src.auth.dependencies import require_auth
from src.common.response import ApiResponse

router = APIRouter(prefix="/api/assistant", tags=["Assistant"])


@router.post("/chat")
async def assistant_chat(user=Depends(require_auth)):
    return ApiResponse.ok(data={"content": "AI 助手模块开发中"})


@router.post("/chat/stream")
async def assistant_chat_stream(user=Depends(require_auth)):
    return ApiResponse.ok(data={"content": "AI 助手模块开发中"})


@router.post("/sessions")
async def create_session(user=Depends(require_auth)):
    return ApiResponse.ok(data={"sessionId": 0, "title": "新会话", "status": "ACTIVE"})


@router.get("/sessions")
async def list_sessions(user=Depends(require_auth)):
    return ApiResponse.ok(data=[])


@router.get("/sessions/{session_id}")
async def get_session(session_id: int, user=Depends(require_auth)):
    return ApiResponse.ok(data={"sessionId": session_id, "title": "新会话", "status": "ACTIVE"})


@router.patch("/sessions/{session_id}")
async def rename_session(session_id: int, user=Depends(require_auth)):
    return ApiResponse.ok(message="OK")


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: int, user=Depends(require_auth)):
    return ApiResponse.ok(message="OK")


@router.get("/sessions/{session_id}/context")
async def get_session_context(session_id: int, user=Depends(require_auth)):
    return ApiResponse.ok(data={"summary": "", "messages": []})
