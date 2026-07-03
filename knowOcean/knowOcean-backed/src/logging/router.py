"""操作日志 API

管理员查看所有用户操作日志（含 LLM 调用）。
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.session import get_db
from src.auth.dependencies import require_admin
from src.logging.operation_log_service import get_operation_logs

router = APIRouter(prefix="/api/admin/operation-logs", tags=["Admin - Operation Logs"])


@router.get("")
async def list_operation_logs(
    user_id: int | None = Query(None, description="筛选用户 ID"),
    category: str | None = Query(None, description="类别: AUTH | ADMIN | DOCUMENT | QA | ASSISTANT"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await get_operation_logs(db, user_id=user_id, category=category, page=page, size=size)
