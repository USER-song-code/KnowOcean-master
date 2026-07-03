"""认证上下文工具

对照 Java: common/security/UserContext.java (ThreadLocal) + CurrentUserService.java

Java 中使用 ThreadLocal 存储 AuthenticatedUser record; Python 中
使用 FastAPI 的依赖注入 + contextvars 实现等效功能。
"""
from contextvars import ContextVar
from dataclasses import dataclass
from fastapi import Request, Depends
from src.common.exceptions import UnauthorizedException, ForbiddenException

# ContextVar = Java ThreadLocal
_current_user_ctx: ContextVar["UserIdentity | None"] = ContextVar("current_user", default=None)


@dataclass
class UserIdentity:
    """当前用户身份
    对照 Java: CurrentUserService.CurrentUser record
    """
    user_id: int
    user_code: str
    username: str
    display_name: str
    system_role: str  # 'ADMIN' | 'USER'
    must_change_password: bool = False

    @property
    def is_admin(self) -> bool:
        return self.system_role == "ADMIN"


def set_current_user(user: UserIdentity | None) -> None:
    _current_user_ctx.set(user)


def get_current_user() -> UserIdentity | None:
    return _current_user_ctx.get(None)


def require_current_user() -> UserIdentity:
    """获取当前用户，未认证时抛出 UnauthorizedException
    对照 Java: currentUserService.getRequiredCurrentUser(request)
    """
    user = get_current_user()
    if user is None:
        raise UnauthorizedException("请先登录")
    return user


def require_admin() -> UserIdentity:
    """要求当前用户必须是 ADMIN
    对照 Java: currentUserService.requireSystemAdmin(request)
    """
    user = require_current_user()
    if not user.is_admin:
        raise ForbiddenException("仅系统管理员可执行此操作")
    return user
