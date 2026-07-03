"""操作日志记录器

提供 record_operation() 函数，以独立 DB 会话写入 operation_logs 表。
失败仅打日志，不影响调用方业务流程。
"""
import logging
import traceback
from datetime import datetime
from sqlalchemy import text
from src.database.session import async_session_factory

logger = logging.getLogger(__name__)


async def record_operation(
    *,
    user_id: int,
    username: str | None = None,
    category: str,
    action: str,
    target_type: str | None = None,
    target_id: int | None = None,
    detail: dict | None = None,
    ip_address: str | None = None,
) -> None:
    """记录一条系统操作日志。

    使用独立数据库会话，失败不影响调用方事务。
    """
    try:
        import json
        async with async_session_factory() as db:
            await db.execute(
                text(
                    """INSERT INTO operation_logs
                       (user_id, username, category, action, target_type, target_id, detail, ip_address, created_at)
                       VALUES
                       (:user_id, :username, :category, :action, :target_type, :target_id,
                        CAST(:detail AS jsonb), :ip_address, :created_at)"""
                ),
                {
                    "user_id": user_id,
                    "username": username,
                    "category": category,
                    "action": action,
                    "target_type": target_type,
                    "target_id": target_id,
                    "detail": json.dumps(detail) if detail else None,
                    "ip_address": ip_address,
                    "created_at": datetime.utcnow(),
                },
            )
            await db.commit()
    except Exception:
        logger.error(f"记录操作日志失败: {traceback.format_exc()}")
