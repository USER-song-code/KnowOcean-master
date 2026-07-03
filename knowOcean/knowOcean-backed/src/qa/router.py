"""QA 问答 API"""
import json
import time
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.session import get_db
from src.auth.dependencies import require_auth
from src.common.security import UserIdentity
from src.config import get_settings
from src.group.service import check_membership
from src.metrics.usage_recorder import record_llm_usage
from src.qa.service import ask_question, stream_ask


class AskQuestionBody(BaseModel):
    groupId: int
    question: str

router = APIRouter(prefix="/api/qa", tags=["QA"])


def _estimate_tokens(text: str) -> int:
    """粗略估算 token 数量。

    中文约 2 字符/token，英文约 4 字符/token。
    用于流式调用无法获取精确 token 数时的估算。
    """
    chinese_chars = sum(1 for c in text if '一' <= c <= '鿿')
    remaining = max(0, len(text) - chinese_chars)
    return max(1, chinese_chars // 2 + max(1, int(remaining * 0.25)))


@router.post("/ask")
async def qa_ask(body: AskQuestionBody, user: UserIdentity = Depends(require_auth), db: AsyncSession = Depends(get_db)):
    if not body.question.strip():
        return {"answered": False, "answer": None, "reasonCode": "INVALID_INPUT", "reasonMessage": "请输入问题", "citations": []}
    if not await check_membership(db, body.groupId, user.user_id):
        return {"answered": False, "answer": None, "reasonCode": "FORBIDDEN", "reasonMessage": "你不是该群组的成员", "citations": []}
    return await ask_question(body.groupId, body.question.strip(), user_id=user.user_id)


@router.post("/stream-ask")
async def qa_stream_ask(body: AskQuestionBody, user: UserIdentity = Depends(require_auth), db: AsyncSession = Depends(get_db)):
    if not body.question.strip():
        async def e(): yield "event: error\ndata: {\"message\":\"请输入问题\"}\n\n"
        return StreamingResponse(e(), media_type="text/event-stream")
    if not await check_membership(db, body.groupId, user.user_id):
        async def e(): yield "event: error\ndata: {\"message\":\"你不是该群组的成员\"}\n\n"
        return StreamingResponse(e(), media_type="text/event-stream")

    settings = get_settings()
    model_name = settings.ai_chat_model
    user_id = user.user_id
    group_id = body.groupId
    question = body.question.strip()

    async def event_stream():
        total_content = ""
        t0 = time.monotonic()
        stream_success = True
        error_msg = None

        try:
            async for event in stream_ask(group_id, question, user_id=user_id):
                # 提取流式 token 内容用于估算 completion tokens
                if "data:" in event:
                    data_start = event.index("data:") + len("data:")
                    data_line = event[data_start:].strip()
                    # 跳过 JSON 结构化数据（如 citations），只累加纯文本 token
                    if event.startswith("event: token"):
                        total_content += data_line
                yield event
        except Exception as e:
            stream_success = False
            error_msg = str(e)[:500]
            yield f"event: error\ndata: {json.dumps({'message': str(e)[:200]}, ensure_ascii=False)}\n\n"
        finally:
            latency_ms = int((time.monotonic() - t0) * 1000)
            # 流式调用估算 token（is_estimated=True）
            est_prompt = _estimate_tokens(question)
            est_completion = _estimate_tokens(total_content)
            await record_llm_usage(
                user_id=user_id, group_id=group_id, module="QA",
                endpoint="qa/stream-ask", model_name=model_name,
                prompt_tokens=est_prompt,
                completion_tokens=est_completion,
                total_tokens=est_prompt + est_completion,
                is_estimated=True,
                latency_ms=latency_ms, success=stream_success,
                error_message=error_msg,
            )

    return StreamingResponse(event_stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
