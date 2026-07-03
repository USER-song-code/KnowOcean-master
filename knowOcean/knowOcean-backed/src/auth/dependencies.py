"""认证依赖注入

对照 Java:
    - auth/security/JwtAuthenticationFilter.java (OncePerRequestFilter — 提取 Bearer token)
    - CurrentUserService.java (从 request attribute 读取 AuthenticatedUser)

FastAPI 中通过 Depends() 实现等效的请求级依赖注入。
"""
from fastapi import Request, Cookie, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.database.session import get_db
from src.auth.jwt import parse_access_token
from src.models.user import User
from src.common.security import UserIdentity


bearer_scheme = HTTPBearer(auto_error=False)


async def extract_access_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict | None:
    """从 Authorization: Bearer <token> 提取并验证 JWT
    对照 Java: JwtAuthenticationFilter.doFilterInternal()
    """
    if credentials is None:
        return None

    payload = parse_access_token(credentials.credentials)
    return payload


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    payload: dict | None = Depends(extract_access_token),
) -> UserIdentity | None:
    """获取当前用户身份 (可选认证)
    对照 Java: CurrentUserService.getCurrentUser(request) → nullable
    """
    if payload is None:
        return None

    user_id = int(payload.get("sub", "0"))
    if user_id == 0:
        return None

    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None or user.status != "ACTIVE":
        return None

    return UserIdentity(
        user_id=user.id,
        user_code=user.user_code,
        username=user.username,
        display_name=user.display_name,
        system_role=user.system_role,
        must_change_password=user.must_change_password,
    )


async def require_auth(user: UserIdentity | None = Depends(get_current_user)) -> UserIdentity:
    """要求认证的依赖 (控制器注入此依赖 → 自动要求登录)
    对照 Java: currentUserService.getRequiredCurrentUser(request)
    """
    from src.common.exceptions import UnauthorizedException

    if user is None:
        raise UnauthorizedException("请先登录")
    return user


async def require_admin(user: UserIdentity = Depends(require_auth)) -> UserIdentity:
    """要求系统管理员
    对照 Java: currentUserService.requireSystemAdmin(request)
    """
    from src.common.exceptions import ForbiddenException

    if not user.is_admin:
        raise ForbiddenException("仅系统管理员可执行此操作")
    return user
