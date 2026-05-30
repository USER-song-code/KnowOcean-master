"""用户管理 API 路由

对照 Java:
    - user/controller/AccountController.java (/api/account/*)
    - user/controller/AdminUserController.java (/api/admin/users/*)
"""
from fastapi import APIRouter, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.session import get_db
from src.auth.dependencies import require_auth, require_admin
from src.common.response import ApiResponse
from src.common.security import UserIdentity
from src.user.schemas import ChangePasswordRequest, UpdateUserStatusRequest, AdminUserItemResponse
from src.user.service import change_password, list_users, get_user_by_id, update_user_status

# 个人账户路由
account_router = APIRouter(prefix="/api/account", tags=["Account"])

# 管理员用户路由
admin_user_router = APIRouter(prefix="/api/admin/users", tags=["Admin - Users"])


@account_router.post("/change-password", response_model=ApiResponse)
async def handle_change_password(
    body: ChangePasswordRequest,
    user: UserIdentity = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """修改当前用户密码
    对照 Java: AccountController.changePassword()
    """
    await change_password(db, user.user_id, body.current_password, body.new_password)
    return ApiResponse.ok(message="密码修改成功")


@admin_user_router.get("")
async def handle_list_users(
    keyword: str | None = Query(None, description="搜索关键词 (用户名/邮箱)"),
    status: str | None = Query(None, description="筛选状态: ACTIVE | DISABLED"),
    role: str | None = Query(None, description="筛选角色: ADMIN | USER"),
    admin: UserIdentity = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """用户列表 (管理员) — 返回数组，前端期望 data 直接是 AdminUserItem[]
    对照 Java: AdminUserController.listUsers()
    """
    items, _ = await list_users(db, keyword=keyword, status=status, system_role=role, limit=200, offset=0)
    return ApiResponse.ok(data=items)


@admin_user_router.get("/{user_id}", response_model=ApiResponse[AdminUserItemResponse])
async def handle_get_user(
    user_id: int,
    admin: UserIdentity = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """获取用户详情 (管理员)
    对照 Java: AdminUserController.getUser(userId)
    """
    user = await get_user_by_id(db, user_id)
    return ApiResponse.ok(data=user)


@admin_user_router.patch("/{user_id}/status", response_model=ApiResponse)
async def handle_update_user_status(
    user_id: int,
    body: UpdateUserStatusRequest,
    admin: UserIdentity = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """修改用户状态 (管理员)
    对照 Java: AdminUserController.updateStatus(userId, dto)
    """
    if user_id == admin.user_id:
        from src.common.exceptions import BusinessException
        raise BusinessException("不能修改自己的账号状态")
    await update_user_status(db, user_id, body.status)
    return ApiResponse.ok(message=f"用户状态已更新为 {body.status}")
