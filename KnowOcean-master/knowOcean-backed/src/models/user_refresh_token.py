"""UserRefreshToken ORM 模型

对照 Java: auth/model/entity/UserRefreshToken.java

数据库表: user_refresh_tokens
- id: BIGSERIAL PK
- user_id: BIGINT FK → users.id
- token_id: VARCHAR(64) UNIQUE — UUID 去横线
- token_hash: VARCHAR(256) — BCrypt 哈希后的 token
- expires_at: TIMESTAMP NOT NULL
- revoked_at: TIMESTAMP — NULL 表示有效
- created_at
"""
from datetime import datetime
from sqlalchemy import String, BigInteger, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from src.database.base import Base, gen_uuid


class UserRefreshToken(Base):
    __tablename__ = "user_refresh_tokens"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    token_id: Mapped[str] = mapped_column(String(64), nullable=False, default=gen_uuid)
    token_hash: Mapped[str] = mapped_column("token_hash", String(256), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
