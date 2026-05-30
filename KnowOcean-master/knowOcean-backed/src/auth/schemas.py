"""认证模块 Pydantic 模型

对照 Java: auth/model/dto/*.java + auth/model/vo/*.java

注意: 前端使用 camelCase，因此所有响应字段使用 alias 映射。
"""
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """对照 Java: auth/model/dto/LoginRequest.java

    前端发送 loginId (驼峰)，后端字段名 account 用于内部服务。
    """
    account: str = Field(..., min_length=1, max_length=128, alias="loginId")
    password: str = Field(..., min_length=1, max_length=128)

    model_config = {"populate_by_name": True}


class RegisterRequest(BaseModel):
    """对照 Java: auth/model/dto/RegisterRequest.java"""
    username: str = Field(..., min_length=2, max_length=64)
    email: str = Field(..., min_length=1, max_length=128)
    display_name: str = Field(..., min_length=1, max_length=128, alias="displayName")
    password: str = Field(..., min_length=6, max_length=128)


class CurrentUserProfile(BaseModel):
    """当前用户信息 (内嵌于 AuthSessionResponse)
    对照 Java: auth/model/vo/CurrentUserProfileResponse.java
    前端: CurrentUserProfile interface
    """
    user_id: int = Field(..., alias="userId")
    user_code: str = Field(..., alias="userCode")
    display_name: str = Field(..., alias="displayName")
    system_role: str = Field(..., alias="systemRole")
    must_change_password: bool = Field(..., alias="mustChangePassword")

    model_config = {"populate_by_name": True}


class AuthSessionResponse(BaseModel):
    """登录/注册/刷新成功后返回
    前端: AuthSessionResponse interface
    """
    access_token: str = Field(..., alias="accessToken")
    current_user: CurrentUserProfile = Field(..., alias="currentUser")

    model_config = {"populate_by_name": True}
