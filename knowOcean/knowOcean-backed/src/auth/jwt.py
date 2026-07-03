"""JWT 服务: Access Token 签发/验证 + Refresh Token 管理

对照 Java:
    - auth/security/JwtAccessTokenService.java (issue/parse JWT)
    - auth/security/RefreshTokenService.java (refresh token CRUD)
    - auth/security/AuthCookieSupport.java (cookie 操作)
"""
import uuid
from datetime import datetime, timedelta
from jose import jwt, JWTError
import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.config import get_settings
from src.models.user_refresh_token import UserRefreshToken

settings = get_settings()

# ============================================================
# Password hashing — 对照 Java: PasswordHasher.java
# ============================================================


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ============================================================
# Access Token — 对照 Java: JwtAccessTokenService.java
# ============================================================


def create_access_token(user_id: int, user_code: str, system_role: str) -> tuple[str, int]:
    """签发 JWT Access Token
    对照 Java: JwtAccessTokenService.issue(userId, userCode, role)
    返回 (token, expires_in_seconds)
    """
    expires_in = settings.jwt_access_token_expire_minutes * 60
    now = datetime.utcnow()
    payload = {
        "sub": str(user_id),
        "user_code": user_code,
        "role": system_role,
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, expires_in


def parse_access_token(token: str) -> dict | None:
    """解析 JWT Access Token
    对照 Java: JwtAccessTokenService.parse(token)
    返回 payload dict，验证失败返回 None
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        return None


# ============================================================
# Refresh Token — 对照 Java: RefreshTokenService.java
# ============================================================


def generate_refresh_token_value() -> str:
    """生成随机 Refresh Token 字符串"""
    return uuid.uuid4().hex + uuid.uuid4().hex  # 64 字符


async def store_refresh_token(session: AsyncSession, user_id: int) -> tuple[str, str]:
    """存储新的 Refresh Token，返回 (raw_token, token_id)

    对照 Java: RefreshTokenService.create(userId) → RefreshTokenRecord
    """
    raw_token = generate_refresh_token_value()
    token_id = uuid.uuid4().hex
    token_hash = hash_password(raw_token)
    now = datetime.utcnow()

    record = UserRefreshToken(
        user_id=user_id,
        token_id=token_id,
        token_hash=token_hash,
        expires_at=now + timedelta(days=settings.jwt_refresh_token_expire_days),
    )
    session.add(record)
    await session.flush()
    return raw_token, token_id


async def verify_and_revoke_refresh_token(session: AsyncSession, raw_token: str) -> int | None:
    """验证 Refresh Token 并吊销旧令牌

    Java 格式: tokenId.secret — 用 tokenId 做索引查找
    Python 格式: 64 hex chars — 用最后登录用户的 token 快速验证

    安全特性: 每次使用后立即吊销旧令牌 → 防止 Refresh Token 重放攻击
    """
    now = datetime.utcnow()

    # 1. 尝试 Java 格式: tokenId.secret (索引查找)
    if "." in raw_token:
        token_id = raw_token.split(".")[0]
        stmt = select(UserRefreshToken).where(
            UserRefreshToken.token_id == token_id,
            UserRefreshToken.revoked_at.is_(None),
            UserRefreshToken.expires_at > now,
        )
        result = await session.execute(stmt)
        record = result.scalar_one_or_none()
        if record and verify_password(raw_token, record.token_hash):
            record.revoked_at = now
            session.add(record)
            await session.flush()
            return record.user_id

    # 2. 回退: 按最近登录用户搜索 (避免全表 bcrypt 遍历)
    stmt = (
        select(UserRefreshToken)
        .where(
            UserRefreshToken.revoked_at.is_(None),
            UserRefreshToken.expires_at > now,
        )
        .order_by(UserRefreshToken.created_at.desc())
        .limit(20)
    )
    result = await session.execute(stmt)
    for record in result.scalars().all():
        if verify_password(raw_token, record.token_hash):
            record.revoked_at = now
            session.add(record)
            await session.flush()
            return record.user_id

    return None


async def revoke_all_user_tokens(session: AsyncSession, user_id: int) -> int:
    """吊销用户的所有 Refresh Token (登出时调用)

    对照 Java: RefreshTokenService.revokeAll(userId)
    返回吊销数量
    """
    from sqlalchemy import update as sql_update

    now = datetime.utcnow()
    stmt = (
        sql_update(UserRefreshToken)
        .where(UserRefreshToken.user_id == user_id, UserRefreshToken.revoked_at.is_(None))
        .values(revoked_at=now)
    )
    result = await session.execute(stmt)
    await session.flush()
    return result.rowcount
