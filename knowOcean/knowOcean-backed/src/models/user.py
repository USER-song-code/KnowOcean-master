"""User ORM 模型

对照 Java: user/model/entity/User.java

数据库表: users
- id: BIGSERIAL PK
- user_code: VARCHAR(64) UNIQUE NOT NULL — 用户编码，前端展示用
- username: VARCHAR(64) UNIQUE NOT NULL
- email: VARCHAR(128) UNIQUE NOT NULL
- display_name: VARCHAR(128) NOT NULL
- password_hash: VARCHAR(256) NOT NULL — BCrypt 哈希
- system_role: VARCHAR(16) NOT NULL DEFAULT 'USER' — ADMIN | USER
- status: VARCHAR(16) NOT NULL DEFAULT 'ACTIVE' — ACTIVE | DISABLED
- must_change_password: BOOLEAN DEFAULT FALSE
- last_login_at: TIMESTAMP
- created_at / updated_at
"""
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from src.database.base import Base, TimestampMixin, gen_uuid


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, default=gen_uuid)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)
    password_hash: Mapped[str] = mapped_column("password_hash", String(256), nullable=False)
    system_role: Mapped[str] = mapped_column(String(16), nullable=False, default="USER")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="ACTIVE")
    must_change_password: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
