"""管理员用量统计 API

所有端点需要管理员权限 (require_admin)。
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.session import get_db
from src.auth.dependencies import require_admin
from src.common.response import ApiResponse
from src.metrics import service as metrics_service

router = APIRouter(prefix="/api/admin/metrics", tags=["Admin - Metrics"])


@router.get("/overview")
async def metrics_overview(
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await metrics_service.get_overview(db)


@router.get("/platform")
async def metrics_platform(
    period: str = Query("LAST_7_DAYS", description="时间段: TODAY | LAST_7_DAYS | LAST_14_DAYS | LAST_30_DAYS"),
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await metrics_service.get_platform_stats(db, period)


@router.get("/user/{user_id}")
async def metrics_user(
    user_id: int,
    period: str = Query("LAST_7_DAYS"),
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await metrics_service.get_user_stats(db, user_id, period)


@router.get("/user/{user_id}/detail")
async def metrics_user_detail(
    user_id: int,
    period: str = Query("LAST_7_DAYS"),
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """用户使用详情：模型拆分、模块拆分、每日趋势、文档数、提问数"""
    data = await metrics_service.get_user_detail(db, user_id, period)
    if data is None:
        return ApiResponse.fail(code=404, message="用户不存在")
    return data


@router.get("/group/{group_id}")
async def metrics_group(
    group_id: int,
    period: str = Query("LAST_7_DAYS"),
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await metrics_service.get_group_stats(db, group_id, period)


@router.get("/trend")
async def metrics_trend(
    period: str = Query("LAST_7_DAYS"),
    module: str | None = Query(None, description="模块过滤: QA | ASSISTANT"),
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await metrics_service.get_trend(db, period, module)


@router.get("/rank/users")
async def metrics_rank_users(
    period: str = Query("LAST_7_DAYS"),
    limit: int = Query(10, ge=1, le=100),
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await metrics_service.get_user_rank(db, period, limit)


@router.get("/rank/groups")
async def metrics_rank_groups(
    period: str = Query("LAST_7_DAYS"),
    limit: int = Query(10, ge=1, le=100),
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await metrics_service.get_group_rank(db, period, limit)
