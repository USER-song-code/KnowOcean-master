"""群组模块 Pydantic 模型 — 字段名匹配前端 camelCase"""
from pydantic import BaseModel, Field


# --- 请求 ---

class CreateGroupRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=128, description="群组名称")
    description: str = Field(default="", max_length=2000)
    model_config = {"populate_by_name": True}


class CreateInvitationRequest(BaseModel):
    invitee_user_id: int = Field(..., gt=0, alias="inviteeUserId")
    model_config = {"populate_by_name": True}


class CreateJoinRequestRequest(BaseModel):
    group_code: str = Field(..., min_length=1, max_length=64, alias="groupCode")
    model_config = {"populate_by_name": True}


# --- 响应 ---

class GroupItem(BaseModel):
    group_id: int = Field(..., alias="groupId")
    group_code: str = Field(..., alias="groupCode")
    group_name: str = Field(..., alias="groupName")
    description: str = ""
    pending_request_count: int = Field(default=0, alias="pendingRequestCount")
    created_at: str | None = Field(default=None, alias="createdAt")
    model_config = {"populate_by_name": True}


class PendingInvitationItem(BaseModel):
    invitation_id: int = Field(..., alias="invitationId")
    group_id: int = Field(..., alias="groupId")
    group_name: str = Field(..., alias="groupName")
    inviter_user_id: int = Field(..., alias="inviterUserId")
    inviter_display_name: str = Field(default="", alias="inviterDisplayName")
    status: str
    created_at: str | None = Field(default=None, alias="createdAt")
    model_config = {"populate_by_name": True}


class GroupQueryResult(BaseModel):
    owned_groups: list[GroupItem] = Field(default_factory=list, alias="ownedGroups")
    joined_groups: list[GroupItem] = Field(default_factory=list, alias="joinedGroups")
    pending_invitations: list[PendingInvitationItem] = Field(default_factory=list, alias="pendingInvitations")
    model_config = {"populate_by_name": True}


class GroupMemberItem(BaseModel):
    user_id: int = Field(..., alias="userId")
    user_code: str = Field(..., alias="userCode")
    display_name: str = Field(..., alias="displayName")
    role: str
    model_config = {"populate_by_name": True}


class OwnerJoinRequestItem(BaseModel):
    request_id: int = Field(..., alias="requestId")
    group_id: int = Field(..., alias="groupId")
    applicant_user_id: int = Field(..., alias="applicantUserId")
    applicant_user_code: str = Field(..., alias="applicantUserCode")
    applicant_display_name: str = Field(..., alias="applicantDisplayName")
    status: str
    created_at: str | None = Field(default=None, alias="createdAt")
    model_config = {"populate_by_name": True}


class MyJoinRequestItem(BaseModel):
    request_id: int = Field(..., alias="requestId")
    group_id: int = Field(..., alias="groupId")
    group_code: str = Field(..., alias="groupCode")
    group_name: str = Field(..., alias="groupName")
    status: str
    created_at: str | None = Field(default=None, alias="createdAt")
    model_config = {"populate_by_name": True}


class MySentInvitationItem(BaseModel):
    invitation_id: int = Field(..., alias="invitationId")
    group_id: int = Field(..., alias="groupId")
    group_name: str = Field(..., alias="groupName")
    invitee_user_id: int = Field(..., alias="inviteeUserId")
    invitee_display_name: str = Field(default="", alias="inviteeDisplayName")
    status: str
    created_at: str | None = Field(default=None, alias="createdAt")
    model_config = {"populate_by_name": True}
