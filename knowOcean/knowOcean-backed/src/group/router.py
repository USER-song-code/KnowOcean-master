"""群组管理 API 路由"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.session import get_db
from src.auth.dependencies import require_auth
from src.common.exceptions import ForbiddenException
from src.common.response import ApiResponse
from src.common.security import UserIdentity
from src.group.schemas import CreateGroupRequest, CreateInvitationRequest, CreateJoinRequestRequest
from src.group.service import (
    fetch_group_query_result, create_group, get_group_members, remove_member, leave_group,
    create_invitation, list_sent_invitations,
    accept_invitation, reject_invitation, cancel_invitation,
    submit_join_request, list_my_join_requests, list_pending_join_requests,
    approve_join_request, reject_join_request, check_membership,
)

group_router = APIRouter(prefix="/api/groups", tags=["Groups"])
invitation_router = APIRouter(prefix="/api/invitations", tags=["Invitations"])


@group_router.post("")
async def handle_create_group(body: CreateGroupRequest, user: UserIdentity = Depends(require_auth), db: AsyncSession = Depends(get_db)):
    group = await create_group(db, user.user_id, body.name, body.description)
    return ApiResponse.ok(data=group.id, message="群组创建成功")


@group_router.get("/my")
async def handle_list_groups(user: UserIdentity = Depends(require_auth), db: AsyncSession = Depends(get_db)):
    result = await fetch_group_query_result(db, user.user_id)
    return ApiResponse.ok(data=result)


@group_router.get("/invitations/my-sent")
async def handle_list_sent_invitations(user: UserIdentity = Depends(require_auth), db: AsyncSession = Depends(get_db)):
    return ApiResponse.ok(data=await list_sent_invitations(db, user.user_id))


@group_router.get("/{group_id}/members")
async def handle_list_members(group_id: int, user: UserIdentity = Depends(require_auth), db: AsyncSession = Depends(get_db)):
    if not await check_membership(db, group_id, user.user_id):
        raise ForbiddenException("你不是该群组的成员")
    return ApiResponse.ok(data=await get_group_members(db, group_id))


@group_router.delete("/{group_id}/members/{target_user_id}")
async def handle_remove_member(group_id: int, target_user_id: int, user: UserIdentity = Depends(require_auth), db: AsyncSession = Depends(get_db)):
    await remove_member(db, group_id, target_user_id, user.user_id)
    return ApiResponse.ok(message="成员已移除")


@group_router.post("/{group_id}/leave")
async def handle_leave_group(group_id: int, user: UserIdentity = Depends(require_auth), db: AsyncSession = Depends(get_db)):
    await leave_group(db, group_id, user.user_id)
    return ApiResponse.ok(message="已退出群组")


@group_router.post("/{group_id}/invitations")
async def handle_create_invitation(group_id: int, body: CreateInvitationRequest, user: UserIdentity = Depends(require_auth), db: AsyncSession = Depends(get_db)):
    inv = await create_invitation(db, group_id, user.user_id, body.invitee_user_id)
    return ApiResponse.ok(data=inv.id, message="邀请已发送")


@group_router.post("/join-requests")
async def handle_submit_join_request(body: CreateJoinRequestRequest, user: UserIdentity = Depends(require_auth), db: AsyncSession = Depends(get_db)):
    req = await submit_join_request(db, user.user_id, body.group_code)
    return ApiResponse.ok(data=req.id, message="申请已提交")


@group_router.get("/join-requests/my")
async def handle_list_my_join_requests(user: UserIdentity = Depends(require_auth), db: AsyncSession = Depends(get_db)):
    return ApiResponse.ok(data=await list_my_join_requests(db, user.user_id))


@group_router.get("/{group_id}/join-requests")
async def handle_list_pending_join_requests(group_id: int, user: UserIdentity = Depends(require_auth), db: AsyncSession = Depends(get_db)):
    return ApiResponse.ok(data=await list_pending_join_requests(db, group_id, user.user_id))


@group_router.post("/{group_id}/join-requests/{request_id}/approve")
async def handle_approve_join_request(group_id: int, request_id: int, user: UserIdentity = Depends(require_auth), db: AsyncSession = Depends(get_db)):
    await approve_join_request(db, group_id, request_id, user.user_id)
    return ApiResponse.ok(message="已批准该加入申请")


@group_router.post("/{group_id}/join-requests/{request_id}/reject")
async def handle_reject_join_request(group_id: int, request_id: int, user: UserIdentity = Depends(require_auth), db: AsyncSession = Depends(get_db)):
    await reject_join_request(db, group_id, request_id, user.user_id)
    return ApiResponse.ok(message="已拒绝该加入申请")


@invitation_router.post("/{invitation_id}/accept")
async def handle_accept_invitation(invitation_id: int, user: UserIdentity = Depends(require_auth), db: AsyncSession = Depends(get_db)):
    await accept_invitation(db, invitation_id, user.user_id)
    return ApiResponse.ok(message="已接受邀请")


@invitation_router.post("/{invitation_id}/reject")
async def handle_reject_invitation(invitation_id: int, user: UserIdentity = Depends(require_auth), db: AsyncSession = Depends(get_db)):
    await reject_invitation(db, invitation_id, user.user_id)
    return ApiResponse.ok(message="已拒绝邀请")


@invitation_router.post("/{invitation_id}/cancel")
async def handle_cancel_invitation(invitation_id: int, user: UserIdentity = Depends(require_auth), db: AsyncSession = Depends(get_db)):
    await cancel_invitation(db, invitation_id, user.user_id)
    return ApiResponse.ok(message="已取消邀请")
