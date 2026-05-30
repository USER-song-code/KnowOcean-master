"""全局异常处理器

对照 Java: common/exception/GlobalExceptionHandler.java

将自定义异常映射为 HTTP 响应，统一使用 ApiResponse 格式。
"""
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from src.common.exceptions import (
    BusinessException, ForbiddenException, UnauthorizedException,
    NotFoundException, ConflictException,
)
from src.common.response import ApiResponse


async def business_exception_handler(request: Request, exc: BusinessException) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content=ApiResponse.fail(code=400, message=exc.message).model_dump(),
    )


async def forbidden_exception_handler(request: Request, exc: ForbiddenException) -> JSONResponse:
    return JSONResponse(
        status_code=403,
        content=ApiResponse.fail(code=403, message=exc.message).model_dump(),
    )


async def unauthorized_exception_handler(request: Request, exc: UnauthorizedException) -> JSONResponse:
    return JSONResponse(
        status_code=401,
        content=ApiResponse.fail(code=401, message=exc.message).model_dump(),
    )


async def not_found_exception_handler(request: Request, exc: NotFoundException) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content=ApiResponse.fail(code=404, message=exc.message).model_dump(),
    )


async def conflict_exception_handler(request: Request, exc: ConflictException) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content=ApiResponse.fail(code=409, message=exc.message).model_dump(),
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Pydantic 验证失败 → 400"""
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"] if loc != "body")
        errors.append(f"{field}: {error['msg']}")
    return JSONResponse(
        status_code=400,
        content=ApiResponse.fail(code=400, message="; ".join(errors)).model_dump(),
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """兜底: 未预期异常 → 500

    对照 Java: GlobalExceptionHandler 最底的 Exception handler
    """
    return JSONResponse(
        status_code=500,
        content=ApiResponse.error(message="服务器内部错误").model_dump(),
    )


def register_exception_handlers(app):
    """注册所有异常处理器到 FastAPI 应用"""
    app.add_exception_handler(BusinessException, business_exception_handler)
    app.add_exception_handler(ForbiddenException, forbidden_exception_handler)
    app.add_exception_handler(UnauthorizedException, unauthorized_exception_handler)
    app.add_exception_handler(NotFoundException, not_found_exception_handler)
    app.add_exception_handler(ConflictException, conflict_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
