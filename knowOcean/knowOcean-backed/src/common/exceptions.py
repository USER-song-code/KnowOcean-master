"""统一异常体系

对照 Java: common/exception/BusinessException.java (400),
             ForbiddenException.java (403),
             UnauthorizedException.java (401)
"""


class BusinessException(Exception):
    """业务异常 — HTTP 400"""
    def __init__(self, message: str = "请求参数错误"):
        self.message = message
        super().__init__(message)


class ForbiddenException(Exception):
    """权限不足 — HTTP 403"""
    def __init__(self, message: str = "权限不足"):
        self.message = message
        super().__init__(message)


class UnauthorizedException(Exception):
    """未认证 — HTTP 401"""
    def __init__(self, message: str = "请先登录"):
        self.message = message
        super().__init__(message)


class NotFoundException(Exception):
    """资源不存在 — HTTP 404"""
    def __init__(self, message: str = "资源不存在"):
        self.message = message
        super().__init__(message)


class ConflictException(Exception):
    """资源冲突 — HTTP 409"""
    def __init__(self, message: str = "资源冲突"):
        self.message = message
        super().__init__(message)
