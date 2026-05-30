"""认证 API 路由

对照 Java: auth/controller/AuthController.java
"""
from fastapi import APIRouter, Response, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.session import get_db
from src.auth.schemas import (
    LoginRequest, RegisterRequest,
    AuthSessionResponse, CurrentUserProfile,
)
from src.auth.service import (
    register_user, login_user, refresh_access_token, logout_user,
    get_user_profile, user_to_profile,
)
from src.auth.jwt import create_access_token, store_refresh_token
from src.auth.dependencies import require_auth
from src.common.response import ApiResponse
from src.common.security import UserIdentity
from src.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/api/auth", tags=["Auth"])

COOKIE_KWARGS = {
    "httponly": settings.jwt_refresh_cookie_http_only,
    "secure": settings.jwt_refresh_cookie_secure,
    "samesite": settings.jwt_refresh_cookie_same_site,
    "max_age": settings.jwt_refresh_token_expire_days * 86400,
    "path": "/",
}


def _get_refresh_token(request: Request) -> str | None:
    """从 cookie 中读取 refresh token (cookie 名称从配置读取)"""
    return request.cookies.get(settings.jwt_refresh_cookie_name)

def _build_session(access_token: str, user) -> AuthSessionResponse:
    return AuthSessionResponse(
        accessToken=access_token,
        currentUser=user_to_profile(user),
    )


@router.post("/register", response_model=ApiResponse[AuthSessionResponse])
async def register(body: RegisterRequest, response: Response, db: AsyncSession = Depends(get_db)):
    user = await register_user(db, body.username, body.email, body.display_name, body.password)
    access_token, _ = create_access_token(user.id, user.user_code, user.system_role)
    raw_refresh, _ = await store_refresh_token(db, user.id)
    response.set_cookie(key=settings.jwt_refresh_cookie_name, value=raw_refresh, **COOKIE_KWARGS)
    return ApiResponse.ok(data=_build_session(access_token, user))


@router.post("/login", response_model=ApiResponse[AuthSessionResponse])
async def login(body: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    raw_refresh, _, user = await login_user(db, body.account, body.password)
    access_token, _ = create_access_token(user.id, user.user_code, user.system_role)
    response.set_cookie(key=settings.jwt_refresh_cookie_name, value=raw_refresh, **COOKIE_KWARGS)
    return ApiResponse.ok(data=_build_session(access_token, user))


@router.post("/refresh", response_model=ApiResponse[AuthSessionResponse])
async def refresh(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    refresh_token = _get_refresh_token(request)
    if not refresh_token:
        from src.common.exceptions import UnauthorizedException
        raise UnauthorizedException("缺少 Refresh Token")

    new_raw_refresh, user = await refresh_access_token(db, refresh_token)
    access_token, _ = create_access_token(user.id, user.user_code, user.system_role)
    response.set_cookie(key=settings.jwt_refresh_cookie_name, value=new_raw_refresh, **COOKIE_KWARGS)
    return ApiResponse.ok(data=_build_session(access_token, user))


@router.post("/logout", response_model=ApiResponse)
async def logout(
    response: Response,
    user: UserIdentity = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    await logout_user(db, user.user_id)
    response.delete_cookie(key=settings.jwt_refresh_cookie_name, path="/")
    return ApiResponse.ok(message="已登出")


@router.get("/me", response_model=ApiResponse[CurrentUserProfile])
async def get_me(user: UserIdentity = Depends(require_auth), db: AsyncSession = Depends(get_db)):
    u = await get_user_profile(db, user.user_id)
    return ApiResponse.ok(data=user_to_profile(u))
