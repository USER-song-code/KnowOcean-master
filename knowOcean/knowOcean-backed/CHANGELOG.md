# KnowOcean Python Backend — 重构变更日志

> 从 Java (Spring Boot 3.5) 迁移至 Python (FastAPI + SQLAlchemy 2.0)
> 参照文档: `docs/Java-to-Python-migration-plan.md` + `docs/KnowOcean-refactoring-plan.md`

---

## 变更记录

### 2026-05-30 — 阶段 0: 项目基础设施搭建

#### 新建文件

| 文件 | 说明 |
|------|------|
| `pyproject.toml` | 项目元数据, 依赖管理 (FastAPI, SQLAlchemy, asyncpg, PyJWT, passlib, etc.) |
| `.env.example` | 环境变量模板 |
| `src/__init__.py` | 包初始化 |
| `src/main.py` | FastAPI 应用入口, 生命周期管理, 中间件注册, 路由注册 |
| `src/config.py` | 全局配置 (pydantic-settings), 读取 .env / 环境变量 |
| `src/database/__init__.py` | 数据库包 |
| `src/database/base.py` | SQLAlchemy declarative base + 通用 mixin (id, created_at, updated_at) |
| `src/database/session.py` | 异步数据库会话管理 (asyncpg + SQLAlchemy async engine) |
| `src/common/__init__.py` | 公共模块包 |
| `src/common/response.py` | 统一响应模型 `ApiResponse[T]`, 兼容 Java 端格式 |
| `src/common/exceptions.py` | 统一异常体系: `BusinessException(400)`, `ForbiddenException(403)`, `UnauthorizedException(401)` |
| `src/common/exception_handlers.py` | FastAPI 全局异常处理器, 映射异常 → HTTP 响应 |
| `src/common/security.py` | 认证上下文工具: `get_current_user_id`, `require_admin` |
| `src/common/constants.py` | 系统常量: SystemRole, UserStatus 枚举 |
| `src/models/__init__.py` | ORM 模型包 |
| `src/models/user.py` | User ORM 模型 → `users` 表 |
| `src/models/user_refresh_token.py` | UserRefreshToken ORM 模型 → `user_refresh_tokens` 表 |
| `src/auth/__init__.py` | 认证模块包 |
| `src/auth/schemas.py` | Pydantic 请求/响应模型: LoginRequest, RegisterRequest, AuthTokensResponse, CurrentUserResponse |
| `src/auth/jwt.py` | JWT 服务: access token 签发/验证, refresh token 管理 |
| `src/auth/dependencies.py` | FastAPI 依赖: JWT Bearer 提取, 当前用户注入 |
| `src/auth/service.py` | 认证业务逻辑: 登录/注册/刷新/登出 |
| `src/auth/router.py` | 认证 API 路由: /api/auth/* |

#### 对照 Java 原实现

| Python 文件 | 对应的 Java 文件 |
|-------------|-----------------|
| `src/main.py` | `KnowOceanBackendApplication.java` |
| `src/config.py` | `application.yml` + `AuthProperties.java` |
| `src/common/response.py` | `common/api/ApiResponse.java` |
| `src/common/exceptions.py` | `common/exception/BusinessException.java` 等 |
| `src/common/exception_handlers.py` | `common/exception/GlobalExceptionHandler.java` |
| `src/common/security.py` | `common/security/UserContext.java` + `CurrentUserService.java` |
| `src/database/session.py` | MyBatis-Plus 全局配置 (SqlSessionFactory) |
| `src/database/base.py` | Entity 基类 (MyBatis-Plus 自动映射) |
| `src/models/user.py` | `user/model/entity/User.java` + `user/mapper/UserMapper.java` |
| `src/models/user_refresh_token.py` | `auth/model/entity/UserRefreshToken.java` + `auth/mapper/UserRefreshTokenMapper.java` |
| `src/auth/schemas.py` | `auth/model/dto/*.java` + `auth/model/vo/*.java` |
| `src/auth/jwt.py` | `auth/security/JwtAccessTokenService.java` + `auth/security/RefreshTokenService.java` |
| `src/auth/dependencies.py` | `auth/security/JwtAuthenticationFilter.java` |
| `src/auth/service.py` | `auth/service/AuthService.java` |
| `src/auth/router.py` | `auth/controller/AuthController.java` |

#### 关键设计决策

1. **异步优先**: 所有数据库操作使用 `AsyncSession` + `asyncpg`，路由使用 `async def`
2. **API 兼容**: `ApiResponse` 格式完全兼容 Java 端 `{success, code, data, message}`
3. **JWT 双令牌**: Access Token (30min Bearer) + Refresh Token (14天 httpOnly Cookie)
4. **密码安全**: 使用 `passlib[bcrypt]` 替代 Spring Security Crypto
5. **数据库不变**: 连接现有 PostgreSQL 16 + pgvector，复用所有表结构

---

#### 阶段 0 完成总结

| 维度 | 数量 |
|------|------|
| 新建文件 | 24 个 |
| 实现的 API 端点 | 5 个 (`/api/auth/*`) |
| ORM 模型 | 2 个 (User, UserRefreshToken) |
| 异常类型 | 5 个 (Business, Forbidden, Unauthorized, NotFound, Conflict) |
| Pydantic Schema | 4 个 (LoginRequest, RegisterRequest, AuthTokensResponse, CurrentUserResponse) |
| 对照的 Java 源文件 | ~15 个 |

> 安全改进 (vs Java 原实现):
> - CORS 中间件已配置 (Java 端缺失 — 重构计划 Issue 2.6)
> - API Key 不再硬编码 (使用 .env 环境变量)
> - JWT 密钥无默认值 (强制环境变量配置)
> - Dev Admin 密码记录在 .env 中而非源码

---

### 2026-05-30 — 阶段 1: 用户管理模块

#### 新建文件

| 文件 | 说明 |
|------|------|
| `src/user/__init__.py` | 用户模块包 |
| `src/user/schemas.py` | Pydantic 模型: ChangePasswordRequest, UpdateUserStatusRequest, AdminUserItemResponse |
| `src/user/service.py` | 业务逻辑: 修改密码, 用户列表/详情, 状态管理 |
| `src/user/router.py` | API 路由: `/api/account/*` (1 端点) + `/api/admin/users/*` (3 端点) |

#### 新增 API 端点

| 方法 | 路径 | 说明 | 对照 Java |
|------|------|------|----------|
| POST | `/api/account/change-password` | 修改当前用户密码 | `AccountController.java` |
| GET | `/api/admin/users` | 用户列表 (支持搜索/筛选/分页) | `AdminUserController.java` |
| GET | `/api/admin/users/{user_id}` | 用户详情 | `AdminUserController.java` |
| PATCH | `/api/admin/users/{user_id}/status` | 启用/禁用用户 | `AdminUserController.java` |

#### 安全规则

- 修改密码: 验证当前密码, 新密码不能与当前密码相同, 修改后清除 `must_change_password`
- 用户列表/详情/状态修改: 全部需要 ADMIN 角色 (通过 `require_admin` 依赖)
- 不能修改自己的账号状态

#### 对照 Java 原实现

| Python 文件 | 对应的 Java 文件 |
|-------------|-----------------|
| `src/user/schemas.py` | `user/model/dto/ChangePassword.java`, `UpdateUserStatus.java`, `user/model/vo/AdminUserItemResponse.java` |
| `src/user/service.py` | `user/service/AccountService.java`, `AdminUserService.java`, `UserQueryService.java` |
| `src/user/router.py` | `user/controller/AccountController.java`, `AdminUserController.java` |

#### 当前总端点: 9 (auth: 5 + user: 4)


### 2026-05-30 — 阶段 2: 群组管理模块

#### 新建文件

| 文件 | 说明 |
|------|------|
| `src/models/group.py` | 4 个 ORM 模型: Group, GroupMembership, GroupInvitation, GroupJoinRequest |
| `src/group/schemas.py` | Pydantic 模型: 6 个 Request/Response |
| `src/group/service.py` | 业务逻辑: 15 个方法, 含权限校验工具 `check_membership` |
| `src/group/router.py` | 15 个端点: `/api/groups/*` (12) + `/api/invitations/*` (3) |

#### 新增 API 端点 (15)

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| POST | `/api/groups` | 登录 | 创建群组 |
| GET | `/api/groups/my` | 登录 | 可见群组列表 |
| GET | `/api/groups/invitations/my-sent` | 登录 | 发出的邀请 |
| GET | `/api/groups/{id}/members` | 成员 | 群组成员列表 |
| DELETE | `/api/groups/{id}/members/{uid}` | OWNER | 移除成员 |
| POST | `/api/groups/{id}/leave` | 成员 | 退出群组 |
| POST | `/api/groups/{id}/invitations` | OWNER | 邀请用户 |
| POST | `/api/groups/join-requests` | 登录 | 提交加入申请 |
| GET | `/api/groups/join-requests/my` | 登录 | 我的申请 |
| GET | `/api/groups/{id}/join-requests` | OWNER | 待处理申请 |
| POST | `/api/groups/{id}/join-requests/{rid}/approve` | OWNER | 批准申请 |
| POST | `/api/groups/{id}/join-requests/{rid}/reject` | OWNER | 拒绝申请 |
| POST | `/api/invitations/{id}/accept` | 被邀请人 | 接受邀请 |
| POST | `/api/invitations/{id}/reject` | 被邀请人 | 拒绝邀请 |
| POST | `/api/invitations/{id}/cancel` | 邀请人 | 取消邀请 |

#### 安全规则

- 所有群组写操作 (邀请/移除/审批) 通过 `_require_owner()` 验证 OWNER 角色
- `check_membership()` 供后续模块 (document/qa/assistant) 跨模块复用
- 防重复: 邀请检测已有邀请, 申请检测已有申请/已是成员

#### 当前总端点: 24 (auth: 5 + user: 4 + group: 15)

---

- **Python**: 3.14.3 (`D:\Python\python\python.exe`)
- **已安装包**: 83 个 (fastapi 0.136.3, sqlalchemy 2.0.50, asyncpg 0.31.0, uvicorn 0.48.0, etc.)
- **修复**: `elasticsearch-py` → `elasticsearch` (包名修正)
- **验证通过**: 所有核心模块 import 成功, FastAPI app 创建成功 (11 条路由)

---

## 待完成

- [x] 阶段 1: 用户管理模块 (`/api/account/*`, `/api/admin/users/*`) ✅
- [x] 阶段 2: 群组管理模块 (`/api/groups/*`, `/api/invitations/*`) ✅
- [ ] 阶段 3: 文档管理模块 (`/api/documents/*`) + MinIO 引擎
- [ ] 阶段 2: 群组管理模块 (`/api/groups/*`, `/api/invitations/*`)
- [ ] 阶段 3: 文档管理模块 (`/api/documents/*`) + MinIO 引擎
- [ ] 阶段 4: ETL 管线 (Celery + 文档解析)
- [ ] 阶段 5: RAG 问答模块 (`/api/qa/*`) + ES 混合检索
- [ ] 阶段 6: AI 助手模块 (`/api/assistant/*`) + SSE 流式
- [ ] 阶段 7: 用量统计模块 (`/api/admin/metrics/*`)
- [ ] 阶段 8: 测试 + Docker 部署
