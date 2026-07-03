"""用户模块 Pydantic 模型

对照 Java: user/model/dto/*.java + user/model/vo/*.java
"""
from pydantic import BaseModel, Field


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1, max_length=128, alias="currentPassword")
    new_password: str = Field(..., min_length=6, max_length=128, alias="newPassword")
    model_config = {"populate_by_name": True}


class UpdateUserStatusRequest(BaseModel):
    status: str = Field(..., pattern="^(ACTIVE|DISABLED)$")


class AdminUserItemResponse(BaseModel):
    """管理员用户列表项 — 前端 camelCase"""
    user_id: int = Field(..., alias="userId")
    user_code: str = Field(..., alias="userCode")
    username: str
    email: str
    display_name: str = Field(..., alias="displayName")
    system_role: str = Field(..., alias="systemRole")
    status: str
    must_change_password: bool = Field(..., alias="mustChangePassword")
    last_login_at: str | None = Field(default=None, alias="lastLoginAt")
    model_config = {"populate_by_name": True}
