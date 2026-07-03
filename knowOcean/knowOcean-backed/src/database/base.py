"""SQLAlchemy 声明式基类

对照 Java: MyBatis-Plus Entity (通过 @TableName 注解)
"""
import uuid
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


def gen_uuid() -> str:
    """生成 32 位无连字符 UUID，与 Java ASSIGN_UUID 策略一致"""
    return uuid.uuid4().hex


class TimestampMixin:
    """自动时间戳 mixin
    对照 Java: MyBatis-Plus 自动填充 (created_at, updated_at)
    """
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
