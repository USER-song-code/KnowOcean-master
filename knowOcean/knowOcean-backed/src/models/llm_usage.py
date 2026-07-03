"""LLM 使用记录 ORM 模型

对应数据库表: llm_usage_records
索引:
  - idx_llm_usage_user_created    (user_id, created_at)
  - idx_llm_usage_group_created   (group_id, created_at)
  - idx_llm_usage_module_created  (module, created_at)
  - idx_llm_usage_created_at      (created_at)
"""
from datetime import datetime
from decimal import Decimal
from sqlalchemy import BigInteger, String, Integer, Boolean, DECIMAL, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from src.database.base import Base


class LlmUsageRecord(Base):
    __tablename__ = "llm_usage_records"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    group_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    module: Mapped[str] = mapped_column(String(32), nullable=False)          # QA | ASSISTANT
    endpoint: Mapped[str] = mapped_column(String(64), nullable=False)        # qa/ask, qa/stream-ask, qa/query-plan, qa/ask-retry
    session_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    prompt_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_estimated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    cost_amount: Mapped[Decimal | None] = mapped_column(DECIMAL(12, 6), nullable=True, default=0)
    cost_currency: Mapped[str | None] = mapped_column(String(8), nullable=True, default="CNY")
    latency_ms: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
