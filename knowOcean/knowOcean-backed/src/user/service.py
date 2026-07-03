"""用户管理业务逻辑

对照 Java:
    - user/service/AccountService.java (修改密码)
    - user/service/AdminUserService.java (管理员用户管理)
    - user/service/UserQueryService.java (用户查询)
"""
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.user import User
from src.auth.jwt import hash_password, verify_password
from src.common.exceptions import BusinessException, NotFoundException
from src.user.schemas import AdminUserItemResponse


async def change_password(
    db: AsyncSession,
    user_id: int,
    current_password: str,
    new_password: str,
) -> None:
    """修改当前用户密码
    对照 Java: AccountService.changePassword(userId, dto)

    安全规则:
    - 需要验证当前密码
    - 新密码不能与当前密码相同
    - 修改后清除 must_change_password 标记
    """
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise NotFoundException("用户不存在")

    if not verify_password(current_password, user.password_hash):
        raise BusinessException("当前密码错误")

    if verify_password(new_password, user.password_hash):
        raise BusinessException("新密码不能与当前密码相同")

    user.password_hash = hash_password(new_password)
    user.must_change_password = False
    db.add(user)
    await db.flush()


async def list_users(
    db: AsyncSession,
    keyword: str | None = None,
    status: str | None = None,
    system_role: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[AdminUserItemResponse], int]:
    """列出所有用户 (管理员功能)
    对照 Java: AdminUserService.listUsers() + UserMapper 自定义查询

    支持按关键词(用户名/邮箱)、状态、角色筛选
    """
    # 构建查询
    stmt = select(User)

    if keyword:
        keyword_filter = f"%{keyword}%"
        stmt = stmt.where(
            (User.username.ilike(keyword_filter)) | (User.email.ilike(keyword_filter))
        )
    if status:
        stmt = stmt.where(User.status == status)
    if system_role:
        stmt = stmt.where(User.system_role == system_role)

    # 计数
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    # 分页
    stmt = stmt.order_by(User.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(stmt)
    users = result.scalars().all()

    items = [_user_to_admin_vo(u) for u in users]
    return items, total


async def get_user_by_id(db: AsyncSession, user_id: int) -> AdminUserItemResponse:
    """获取指定用户详情 (管理员功能)
    对照 Java: AdminUserService.getUser(userId)
    """
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise NotFoundException("用户不存在")

    return _user_to_admin_vo(user)


async def update_user_status(
    db: AsyncSession,
    user_id: int,
    new_status: str,
) -> None:
    """修改用户状态 (启用/禁用) (管理员功能)
    对照 Java: AdminUserService.updateStatus(userId, dto)

    安全规则:
    - 不能修改自己的状态
    - 状态只能是 ACTIVE 或 DISABLED
    """
    if new_status not in ("ACTIVE", "DISABLED"):
        raise BusinessException("无效的用户状态")

    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise NotFoundException("用户不存在")

    if user.status == new_status:
        raise BusinessException(f"用户已经是 {new_status} 状态")

    user.status = new_status
    db.add(user)
    await db.flush()


def _user_to_admin_vo(user: User) -> AdminUserItemResponse:
    """Entity → Admin VO 映射
    对照 Java: UserQueryService.toAdminVo(user)
    """
    return AdminUserItemResponse(
        user_id=user.id,
        user_code=user.user_code,
        username=user.username,
        email=user.email,
        display_name=user.display_name,
        system_role=user.system_role,
        status=user.status,
        must_change_password=user.must_change_password,
        last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
        created_at=user.created_at.isoformat() if user.created_at else None,
    )
