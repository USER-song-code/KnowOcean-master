"""QA 问答 API"""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.session import get_db
from src.auth.dependencies import require_auth
from src.common.security import UserIdentity
from src.group.service import check_membership
from src.qa.service import ask_question, stream_ask


class AskQuestionBody(BaseModel):
    groupId: int
    question: str

router = APIRouter(prefix="/api/qa", tags=["QA"])


@router.post("/ask")
async def qa_ask(body: AskQuestionBody, user: UserIdentity = Depends(require_auth), db: AsyncSession = Depends(get_db)):
    if not body.question.strip():
        return {"answered": False, "answer": None, "reasonCode": "INVALID_INPUT", "reasonMessage": "请输入问题", "citations": []}
    if not await check_membership(db, body.groupId, user.user_id):
        return {"answered": False, "answer": None, "reasonCode": "FORBIDDEN", "reasonMessage": "你不是该群组的成员", "citations": []}
    return await ask_question(body.groupId, body.question.strip())


@router.post("/stream-ask")
async def qa_stream_ask(body: AskQuestionBody, user: UserIdentity = Depends(require_auth), db: AsyncSession = Depends(get_db)):
    if not body.question.strip():
        async def e(): yield "event: error\ndata: {\"message\":\"请输入问题\"}\n\n"
        return StreamingResponse(e(), media_type="text/event-stream")
    if not await check_membership(db, body.groupId, user.user_id):
        async def e(): yield "event: error\ndata: {\"message\":\"你不是该群组的成员\"}\n\n"
        return StreamingResponse(e(), media_type="text/event-stream")

    async def event_stream():
        async for event in stream_ask(body.groupId, body.question.strip()):
            yield event

    return StreamingResponse(event_stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
