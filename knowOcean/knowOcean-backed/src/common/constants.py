"""系统常量 & 枚举

对照 Java: common/enums/SystemRole.java, UserStatus.java
"""
from enum import StrEnum


class SystemRole(StrEnum):
    ADMIN = "ADMIN"
    USER = "USER"


class UserStatus(StrEnum):
    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"
