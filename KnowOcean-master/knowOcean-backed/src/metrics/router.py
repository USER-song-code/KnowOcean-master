"""用量统计模块 (stub)"""
from fastapi import APIRouter, Depends
from src.auth.dependencies import require_admin
from src.common.response import ApiResponse

router = APIRouter(prefix="/api/admin/metrics", tags=["Admin - Metrics"])


@router.get("/overview")
async def metrics_overview(admin=Depends(require_admin)):
    return ApiResponse.ok(data={"totalUsers": 0, "totalGroups": 0, "totalDocuments": 0, "totalTokens": 0, "totalCost": 0})


@router.get("/platform")
async def metrics_platform(admin=Depends(require_admin)):
    return ApiResponse.ok(data={"tokens": 0, "cost": 0, "requests": 0})


@router.get("/user/{user_id}")
async def metrics_user(user_id: int, admin=Depends(require_admin)):
    return ApiResponse.ok(data={"tokens": 0, "cost": 0, "requests": 0})


@router.get("/group/{group_id}")
async def metrics_group(group_id: int, admin=Depends(require_admin)):
    return ApiResponse.ok(data={"tokens": 0, "cost": 0, "requests": 0})


@router.get("/trend")
async def metrics_trend(admin=Depends(require_admin)):
    return ApiResponse.ok(data=[])


@router.get("/rank/users")
async def metrics_rank_users(admin=Depends(require_admin)):
    return ApiResponse.ok(data=[])


@router.get("/rank/groups")
async def metrics_rank_groups(admin=Depends(require_admin)):
    return ApiResponse.ok(data=[])
