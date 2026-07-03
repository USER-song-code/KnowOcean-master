"""LLM 用量记录器

提供 record_llm_usage() 函数，以独立 DB 会话写入 llm_usage_records 表。
记录失败仅打日志，不影响调用方业务流程。
"""
import logging
import traceback
from datetime import datetime
from decimal import Decimal
from sqlalchemy import text
from src.database.session import async_session_factory
from src.metrics.pricing import calculate_cost

logger = logging.getLogger(__name__)


async def record_llm_usage(
    *,
    user_id: int,
    group_id: int | None = None,
    module: str = "QA",
    endpoint: str,
    session_id: str | None = None,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    total_tokens: int = 0,
    is_estimated: bool = False,
    model_name: str | None = None,
    latency_ms: int = 0,
    success: bool = True,
    error_message: str | None = None,
) -> None:
    """记录一次 LLM 调用用量。

    使用独立的数据库会话写入，确保记录失败不影响调用方的事务。
    所有参数均为关键字参数，调用时显式指定。
    """
    # 如果 total_tokens 未设置，从 prompt+completion 推算
    if total_tokens == 0:
        total_tokens = prompt_tokens + completion_tokens

    # 计算费用
    cost_amount = calculate_cost(model_name, prompt_tokens, completion_tokens) if success else Decimal("0")

    try:
        async with async_session_factory() as db:
            await db.execute(
                text(
                    """INSERT INTO llm_usage_records
                       (user_id, group_id, module, endpoint, session_id,
                        prompt_tokens, completion_tokens, total_tokens,
                        is_estimated, cost_amount, cost_currency,
                        latency_ms, success, error_message, model_name, created_at)
                       VALUES
                       (:user_id, :group_id, :module, :endpoint, :session_id,
                        :prompt_tokens, :completion_tokens, :total_tokens,
                        :is_estimated, :cost_amount, 'CNY',
                        :latency_ms, :success, :error_message, :model_name, :created_at)"""
                ),
                {
                    "user_id": user_id,
                    "group_id": group_id,
                    "module": module,
                    "endpoint": endpoint,
                    "session_id": session_id,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                    "is_estimated": is_estimated,
                    "cost_amount": cost_amount,
                    "latency_ms": latency_ms,
                    "success": success,
                    "error_message": error_message[:500] if error_message else None,
                    "model_name": model_name,
                    "created_at": datetime.utcnow(),
                },
            )
            await db.commit()
    except Exception:
        logger.error(f"记录 LLM 用量失败: {traceback.format_exc()}")
