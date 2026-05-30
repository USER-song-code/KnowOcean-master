"""Group / GroupMembership / GroupInvitation / GroupJoinRequest ORM 模型

对照 Java: group/model/entity/Group.java, GroupMembership.java, GroupInvitation.java, GroupJoinRequest.java

数据库表: groups, group_memberships, group_invitations, group_join_requests
"""
from datetime import datetime
from sqlalchemy import String, BigInteger, ForeignKey, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from src.database.base import Base, TimestampMixin, gen_uuid


class Group(Base, TimestampMixin):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    group_code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, default=gen_uuid)
    group_name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    owner_user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="ACTIVE")


class GroupMembership(Base, TimestampMixin):
    __tablename__ = "group_memberships"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("groups.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False, default="MEMBER")  # OWNER | MEMBER


class GroupInvitation(Base, TimestampMixin):
    __tablename__ = "group_invitations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("groups.id"), nullable=False)
    inviter_user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    invitee_user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="PENDING")  # PENDING | ACCEPTED | REFUSED | CANCELLED
    decided_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class GroupJoinRequest(Base, TimestampMixin):
    __tablename__ = "group_join_requests"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("groups.id"), nullable=False)
    applicant_user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="PENDING")  # PENDING | APPROVED | REJECTED | CANCELLED
    decided_by_user_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
