"""认证业务逻辑

对照 Java: auth/service/AuthService.java
"""
from datetime import datetime
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from src.auth import jwt
from src.auth.schemas import CurrentUserProfile
from src.models.user import User
from src.common.exceptions import BusinessException, UnauthorizedException, ConflictException


async def register_user(
    db: AsyncSession,
    username: str,
    email: str,
    display_name: str,
    password: str,
) -> User:
    """注册新用户"""
    stmt = select(User).where(or_(User.username == username, User.email == email))
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing is not None:
        if existing.username == username:
            raise ConflictException("用户名已存在")
        else:
            raise ConflictException("邮箱已被注册")

    user = User(
        user_code=jwt.generate_refresh_token_value()[:32],
        username=username,
        email=email,
        display_name=display_name,
        password_hash=jwt.hash_password(password),
    )
    db.add(user)
    await db.flush()
    return user


async def login_user(
    db: AsyncSession,
    account: str,
    password: str,
) -> tuple[str, str, User]:
    """登录
    返回 (raw_refresh_token, token_id, User)
    """
    stmt = select(User).where(or_(User.username == account, User.email == account))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise BusinessException("账号或密码错误")
    if user.status != "ACTIVE":
        raise BusinessException("账号已被禁用")
    if not jwt.verify_password(password, user.password_hash):
        raise BusinessException("账号或密码错误")

    # 签发 refresh token
    raw_refresh, token_id = await jwt.store_refresh_token(db, user.id)

    # 更新最后登录时间
    user.last_login_at = datetime.utcnow()
    db.add(user)
    await db.flush()

    return raw_refresh, token_id, user


async def refresh_access_token(
    db: AsyncSession,
    raw_refresh_token: str,
) -> tuple[str, User]:
    """刷新 Access Token
    返回 (new_raw_refresh_token, User)
    """
    user_id = await jwt.verify_and_revoke_refresh_token(db, raw_refresh_token)
    if user_id is None:
        raise UnauthorizedException("Refresh Token 无效或已过期")

    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user is None or user.status != "ACTIVE":
        raise UnauthorizedException("账号不存在或已被禁用")

    new_raw_refresh, _ = await jwt.store_refresh_token(db, user.id)
    return new_raw_refresh, user


async def logout_user(db: AsyncSession, user_id: int) -> int:
    return await jwt.revoke_all_user_tokens(db, user_id)


async def get_user_profile(db: AsyncSession, user_id: int) -> User:
    """获取用户 ORM 对象"""
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user is None:
        raise BusinessException("用户不存在")
    return user


def user_to_profile(user: User) -> CurrentUserProfile:
    """User ORM → CurrentUserProfile (前端 camelCase)"""
    return CurrentUserProfile(
        userId=user.id,
        userCode=user.user_code,
        displayName=user.display_name,
        systemRole=user.system_role,
        mustChangePassword=user.must_change_password,
    )
