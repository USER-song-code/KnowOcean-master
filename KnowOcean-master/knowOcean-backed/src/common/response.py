"""统一响应模型

对照 Java: common/api/ApiResponse.java (record)

Java 原始格式:
    public record ApiResponse<T>(boolean success, T data, String message) {
        public static <T> ApiResponse<T> success(T data) { ... }
        public static <T> ApiResponse<T> error(String message) { ... }
    }
"""
from typing import Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    code: int = 200
    data: T | None = None
    message: str | None = None

    @staticmethod
    def ok(data: T = None, message: str | None = None) -> "ApiResponse[T]":
        return ApiResponse(success=True, code=200, data=data, message=message)

    @staticmethod
    def fail(code: int = 400, message: str = "请求失败") -> "ApiResponse":
        return ApiResponse(success=False, code=code, data=None, message=message)

    @staticmethod
    def error(message: str = "服务器内部错误") -> "ApiResponse":
        return ApiResponse(success=False, code=500, data=None, message=message)
