"""群组管理业务逻辑"""
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.group import Group, GroupMembership, GroupInvitation, GroupJoinRequest
from src.models.user import User
from src.common.exceptions import BusinessException, NotFoundException, ForbiddenException, ConflictException
from src.group.schemas import (
    GroupQueryResult, GroupItem, PendingInvitationItem,
    GroupMemberItem, OwnerJoinRequestItem, MyJoinRequestItem, MySentInvitationItem,
)
import uuid


# ============================================================
# 群组查询
# ============================================================

async def fetch_group_query_result(db: AsyncSession, user_id: int) -> GroupQueryResult:
    """查询群组列表 — 按 OWNER/MEMBER 分组 + 待处理邀请

    对应前端 GroupQueryResult: {ownedGroups, joinedGroups, pendingInvitations}
    """
    owned, joined = [], []

    # 查询所有群组成员关系
    stmt = (
        select(Group, GroupMembership.role)
        .join(GroupMembership, Group.id == GroupMembership.group_id)
        .where(GroupMembership.user_id == user_id, Group.status == "ACTIVE")
        .order_by(Group.created_at.desc())
    )
    result = await db.execute(stmt)
    for group, role in result.all():
        pending_count = 0
        if role == "OWNER":
            cnt = await db.execute(select(func.count()).where(
                GroupJoinRequest.group_id == group.id, GroupJoinRequest.status == "PENDING"
            ))
            pending_count = cnt.scalar() or 0

        item = GroupItem(
            groupId=group.id,
            groupCode=group.group_code,
            groupName=group.group_name,
            description=group.description or "",
            pendingRequestCount=pending_count,
            createdAt=group.created_at.isoformat() if group.created_at else None,
        )
        if role == "OWNER":
            owned.append(item)
        else:
            joined.append(item)

    # 待处理邀请 (发给我但未处理的)
    inv_stmt = (
        select(GroupInvitation, Group, User)
        .join(Group, GroupInvitation.group_id == Group.id)
        .join(User, GroupInvitation.inviter_user_id == User.id)
        .where(GroupInvitation.invitee_user_id == user_id, GroupInvitation.status == "PENDING")
        .order_by(GroupInvitation.created_at.desc())
    )
    inv_result = await db.execute(inv_stmt)
    invitations = []
    for inv, group, inviter in inv_result.all():
        invitations.append(PendingInvitationItem(
            invitationId=inv.id,
            groupId=group.id,
            groupName=group.group_name,
            inviterUserId=inviter.id,
            inviterDisplayName=inviter.display_name,
            status=inv.status,
            createdAt=inv.created_at.isoformat() if inv.created_at else None,
        ))

    return GroupQueryResult(
        ownedGroups=owned,
        joinedGroups=joined,
        pendingInvitations=invitations,
    )


# ============================================================
# 群组 CRUD
# ============================================================

async def create_group(db: AsyncSession, owner_user_id: int, name: str, description: str = "") -> Group:
    group = Group(
        group_code=uuid.uuid4().hex[:32],
        group_name=name,
        description=description,
        owner_user_id=owner_user_id,
    )
    db.add(group)
    await db.flush()

    membership = GroupMembership(group_id=group.id, user_id=owner_user_id, role="OWNER")
    db.add(membership)
    await db.flush()
    return group


async def get_group_members(db: AsyncSession, group_id: int) -> list[GroupMemberItem]:
    stmt = (
        select(GroupMembership, User)
        .join(User, GroupMembership.user_id == User.id)
        .where(GroupMembership.group_id == group_id)
        .order_by(GroupMembership.created_at.asc())
    )
    result = await db.execute(stmt)
    return [
        GroupMemberItem(
            userId=user.id,
            userCode=user.user_code,
            displayName=user.display_name,
            role=membership.role,
        )
        for membership, user in result.all()
    ]


async def remove_member(db: AsyncSession, group_id: int, target_user_id: int, operator_user_id: int) -> None:
    await _require_owner(db, group_id, operator_user_id)
    if target_user_id == operator_user_id:
        raise BusinessException("请使用退出群组功能")

    stmt = select(GroupMembership).where(
        GroupMembership.group_id == group_id, GroupMembership.user_id == target_user_id
    )
    result = await db.execute(stmt)
    m = result.scalar_one_or_none()
    if m is None:
        raise NotFoundException("该用户不在此群组中")
    if m.role == "OWNER":
        raise BusinessException("不能移除群组所有者")
    await db.delete(m)
    await db.flush()


async def leave_group(db: AsyncSession, group_id: int, user_id: int) -> None:
    stmt = select(GroupMembership).where(
        GroupMembership.group_id == group_id, GroupMembership.user_id == user_id
    )
    result = await db.execute(stmt)
    m = result.scalar_one_or_none()
    if m is None:
        raise NotFoundException("你不在此群组中")
    if m.role == "OWNER":
        raise BusinessException("群组所有者不能退出")
    await db.delete(m)
    await db.flush()


# ============================================================
# 邀请
# ============================================================

async def create_invitation(db: AsyncSession, group_id: int, inviter_user_id: int, invitee_user_id: int) -> GroupInvitation:
    await _require_owner(db, group_id, inviter_user_id)
    if inviter_user_id == invitee_user_id:
        raise BusinessException("不能邀请自己")

    stmt = select(GroupMembership).where(
        GroupMembership.group_id == group_id, GroupMembership.user_id == invitee_user_id
    )
    if (await db.execute(stmt)).scalar_one_or_none():
        raise BusinessException("该用户已在群组中")

    stmt = select(GroupInvitation).where(
        GroupInvitation.group_id == group_id, GroupInvitation.invitee_user_id == invitee_user_id,
        GroupInvitation.status == "PENDING",
    )
    if (await db.execute(stmt)).scalar_one_or_none():
        raise ConflictException("已向该用户发送过邀请")

    inv = GroupInvitation(group_id=group_id, inviter_user_id=inviter_user_id, invitee_user_id=invitee_user_id)
    db.add(inv)
    await db.flush()
    return inv


async def list_sent_invitations(db: AsyncSession, user_id: int) -> list[MySentInvitationItem]:
    stmt = (
        select(GroupInvitation, Group, User)
        .join(Group, GroupInvitation.group_id == Group.id)
        .join(User, GroupInvitation.invitee_user_id == User.id)
        .where(GroupInvitation.inviter_user_id == user_id)
        .order_by(GroupInvitation.created_at.desc())
    )
    result = await db.execute(stmt)
    return [
        MySentInvitationItem(
            invitationId=inv.id, groupId=group.id, groupName=group.group_name,
            inviteeUserId=user.id, inviteeDisplayName=user.display_name,
            status=inv.status,
            createdAt=inv.created_at.isoformat() if inv.created_at else None,
        )
        for inv, group, user in result.all()
    ]


async def accept_invitation(db: AsyncSession, invitation_id: int, user_id: int) -> None:
    stmt = select(GroupInvitation).where(GroupInvitation.id == invitation_id)
    result = await db.execute(stmt)
    inv = result.scalar_one_or_none()
    if inv is None: raise NotFoundException("邀请不存在")
    if inv.invitee_user_id != user_id: raise ForbiddenException("此邀请不是发给你的")
    if inv.status != "PENDING": raise BusinessException("此邀请已经处理过了")

    inv.status = "ACCEPTED"; inv.decided_at = datetime.utcnow()
    db.add(inv)
    db.add(GroupMembership(group_id=inv.group_id, user_id=user_id, role="MEMBER"))
    await db.flush()


async def reject_invitation(db: AsyncSession, invitation_id: int, user_id: int) -> None:
    stmt = select(GroupInvitation).where(GroupInvitation.id == invitation_id)
    inv = (await db.execute(stmt)).scalar_one_or_none()
    if inv is None: raise NotFoundException("邀请不存在")
    if inv.invitee_user_id != user_id: raise ForbiddenException("此邀请不是发给你的")
    if inv.status != "PENDING": raise BusinessException("此邀请已经处理过了")
    inv.status = "REFUSED"; inv.decided_at = datetime.utcnow()
    db.add(inv)
    await db.flush()


async def cancel_invitation(db: AsyncSession, invitation_id: int, user_id: int) -> None:
    stmt = select(GroupInvitation).where(GroupInvitation.id == invitation_id)
    inv = (await db.execute(stmt)).scalar_one_or_none()
    if inv is None: raise NotFoundException("邀请不存在")
    if inv.inviter_user_id != user_id: raise ForbiddenException("只能取消自己发出的邀请")
    if inv.status != "PENDING": raise BusinessException("此邀请已经处理过了")
    inv.status = "CANCELLED"; inv.decided_at = datetime.utcnow()
    db.add(inv)
    await db.flush()


# ============================================================
# 加入申请
# ============================================================

async def submit_join_request(db: AsyncSession, user_id: int, group_code: str) -> GroupJoinRequest:
    stmt = select(Group).where(Group.group_code == group_code, Group.status == "ACTIVE")
    group = (await db.execute(stmt)).scalar_one_or_none()
    if group is None:
        raise NotFoundException("群组不存在或已归档")

    stmt = select(GroupMembership).where(GroupMembership.group_id == group.id, GroupMembership.user_id == user_id)
    if (await db.execute(stmt)).scalar_one_or_none():
        raise BusinessException("你已经是该群组的成员")

    stmt = select(GroupJoinRequest).where(
        GroupJoinRequest.group_id == group.id, GroupJoinRequest.applicant_user_id == user_id,
        GroupJoinRequest.status == "PENDING",
    )
    if (await db.execute(stmt)).scalar_one_or_none():
        raise ConflictException("你已提交过加入申请")

    req = GroupJoinRequest(group_id=group.id, applicant_user_id=user_id)
    db.add(req)
    await db.flush()
    return req


async def list_my_join_requests(db: AsyncSession, user_id: int) -> list[MyJoinRequestItem]:
    stmt = (
        select(GroupJoinRequest, Group)
        .join(Group, GroupJoinRequest.group_id == Group.id)
        .where(GroupJoinRequest.applicant_user_id == user_id)
        .order_by(GroupJoinRequest.created_at.desc())
    )
    result = await db.execute(stmt)
    return [
        MyJoinRequestItem(
            requestId=req.id, groupId=group.id, groupCode=group.group_code,
            groupName=group.group_name, status=req.status,
            createdAt=req.created_at.isoformat() if req.created_at else None,
        )
        for req, group in result.all()
    ]


async def list_pending_join_requests(db: AsyncSession, group_id: int, operator_user_id: int) -> list[OwnerJoinRequestItem]:
    await _require_owner(db, group_id, operator_user_id)
    stmt = (
        select(GroupJoinRequest, User)
        .join(User, GroupJoinRequest.applicant_user_id == User.id)
        .where(GroupJoinRequest.group_id == group_id, GroupJoinRequest.status == "PENDING")
        .order_by(GroupJoinRequest.created_at.asc())
    )
    result = await db.execute(stmt)
    return [
        OwnerJoinRequestItem(
            requestId=req.id, groupId=group_id,
            applicantUserId=user.id, applicantUserCode=user.user_code,
            applicantDisplayName=user.display_name, status=req.status,
            createdAt=req.created_at.isoformat() if req.created_at else None,
        )
        for req, user in result.all()
    ]


async def approve_join_request(db: AsyncSession, group_id: int, request_id: int, operator_user_id: int) -> None:
    await _require_owner(db, group_id, operator_user_id)
    stmt = select(GroupJoinRequest).where(GroupJoinRequest.id == request_id, GroupJoinRequest.group_id == group_id)
    req = (await db.execute(stmt)).scalar_one_or_none()
    if req is None: raise NotFoundException("申请不存在")
    if req.status != "PENDING": raise BusinessException("此申请已经处理过了")
    req.status = "APPROVED"; req.decided_by_user_id = operator_user_id; req.decided_at = datetime.utcnow()
    db.add(req)
    db.add(GroupMembership(group_id=group_id, user_id=req.applicant_user_id, role="MEMBER"))
    await db.flush()


async def reject_join_request(db: AsyncSession, group_id: int, request_id: int, operator_user_id: int) -> None:
    await _require_owner(db, group_id, operator_user_id)
    stmt = select(GroupJoinRequest).where(GroupJoinRequest.id == request_id, GroupJoinRequest.group_id == group_id)
    req = (await db.execute(stmt)).scalar_one_or_none()
    if req is None: raise NotFoundException("申请不存在")
    if req.status != "PENDING": raise BusinessException("此申请已经处理过了")
    req.status = "REJECTED"; req.decided_by_user_id = operator_user_id; req.decided_at = datetime.utcnow()
    db.add(req)
    await db.flush()


async def check_membership(db: AsyncSession, group_id: int, user_id: int) -> bool:
    stmt = select(GroupMembership).where(GroupMembership.group_id == group_id, GroupMembership.user_id == user_id)
    return (await db.execute(stmt)).scalar_one_or_none() is not None


async def _require_owner(db: AsyncSession, group_id: int, user_id: int) -> GroupMembership:
    stmt = select(GroupMembership).where(GroupMembership.group_id == group_id, GroupMembership.user_id == user_id)
    m = (await db.execute(stmt)).scalar_one_or_none()
    if m is None: raise ForbiddenException("你不是该群组的成员")
    if m.role != "OWNER": raise ForbiddenException("仅群组所有者可以执行此操作")
    return m
