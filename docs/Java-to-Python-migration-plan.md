# KnowOcean Java → Python 后端迁移方案

> 文档版本: v1.0  
> 创建日期: 2026-05-30  
> 目标: 将现有 Spring Boot 3.5 / Java 21 后端完整迁移至 Python 技术栈

---

## 一、现状概览

### 1.1 当前 Java 后端规模

| 维度 | 数量 |
|------|------|
| Controller 类 | 13 个 |
| Service 类 | 27 个 |
| Mapper/DAO 接口 | 13 个 |
| Entity 实体 | 16 个 |
| DTO/VO 类 | ~40 个 |
| 配置类 | 8 个 |
| MyBatis XML | 10 个 |
| API 端点 | ~44 个 |
| 数据库表 | 15 张 |

### 1.2 当前技术栈

| 组件 | 技术 | 版本 |
|------|------|------|
| 语言/运行时 | Java | 21 |
| Web 框架 | Spring Boot | 3.5.0 |
| AI 框架 | Spring AI + Alibaba DashScope | 1.1.2 |
| ORM | MyBatis-Plus | 3.5.15 |
| 关系数据库 | PostgreSQL + pgvector | 16 |
| 搜索引擎 | Elasticsearch + IK 分词 | 8.15.3 |
| 对象存储 | MinIO | 2025-09 |
| 认证 | JJWT (HMAC-SHA) + BCrypt | 0.12.6 |
| API 文档 | Knife4j / SpringDoc | 2.8.10 |
| 构建工具 | Maven | — |

---

## 二、目标 Python 技术栈

| 组件 | 推荐方案 | 备选方案 | 选型理由 |
|------|----------|----------|----------|
| 语言/运行时 | **Python 3.12+** | — | 最新的 `asyncio` 特性、类型注解增强 |
| Web 框架 | **FastAPI** + Uvicorn | Django Ninja | 原生异步、自动 OpenAPI 文档、Pydantic 深度集成 |
| ORM | **SQLAlchemy 2.0** + asyncpg | SQLModel | 社区最成熟、原生异步支持、迁移工具完善 |
| 向量数据库 | **pgvector** (Python SDK) | — | 复用现有 PG 基础设施，无需新增组件 |
| 搜索 | **elasticsearch-py 8.x** | — | 官方 Python 客户端，保持与 ES 8.15 兼容 |
| 对象存储 | **boto3** (S3 协议) | minio-py | boto3 生态更广、文档更多 |
| AI/LLM | **openai SDK** (兼容 DashScope) | LangChain | 项目已用 DashScope 兼容模式，直接用 openai 官方 SDK 更轻量 |
| 认证 | **PyJWT** + **passlib[bcrypt]** | python-jose | 最小化依赖，功能完全覆盖 |
| 数据校验 | **Pydantic v2** | — | FastAPI 内置，零额外依赖 |
| 异步任务 | **Celery** + Redis | ARQ, Dramatiq | 社区最大、支持定时重试、与当前 ETL 异步模式匹配 |
| 数据库迁移 | **Alembic** | — | SQLAlchemy 官配，最成熟 |
| API 文档 | **FastAPI 内建 OpenAPI** | — | 自动生成 Swagger UI + ReDoc |
| 包管理 | **uv** (Rye) / **Poetry** | pip + venv | 更快、锁定文件、现代 Python 包管理 |
| 日志 | **loguru** + structlog | logging | loguru 零配置即用、structlog 结构化输出 |
| 测试 | **pytest** + httpx | — | 社区标准 |

---

## 三、项目结构设计

```
knowocean-backend-py/
├── pyproject.toml              # 项目元数据 + 依赖管理
├── alembic.ini                 # 数据库迁移配置
├── Dockerfile                  # 容器构建文件
├── docker-compose.yml          # 本地开发环境
├── .env.example                # 环境变量模板
│
├── alembic/                    # 数据库迁移脚本
│   ├── env.py
│   └── versions/
│
├── src/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 应用入口
│   ├── config.py               # 全局配置 (pydantic-settings)
│   ├── dependencies.py         # FastAPI 依赖注入
│   │
│   ├── common/                 # 公共基础设施
│   │   ├── __init__.py
│   │   ├── exceptions.py       # 统一异常定义
│   │   ├── exception_handlers.py  # 全局异常处理器
│   │   ├── response.py         # 统一响应模型 ApiResponse
│   │   ├── security.py         # 认证上下文 (替代 UserContext)
│   │   └── logging_middleware.py  # 操作日志中间件
│   │
│   ├── auth/                   # 认证模块
│   │   ├── __init__.py
│   │   ├── router.py           # 路由: /api/auth/*
│   │   ├── schemas.py          # Pydantic: LoginRequest, RegisterRequest, AuthTokensResponse
│   │   ├── service.py          # 认证业务逻辑
│   │   ├── jwt.py              # JWT 生成/验证
│   │   └── dependencies.py     # 认证依赖: get_current_user
│   │
│   ├── user/                   # 用户模块
│   │   ├── __init__.py
│   │   ├── router.py           # 路由: /api/account/*, /api/admin/users/*
│   │   ├── schemas.py          # Pydantic 模型
│   │   └── service.py          # 用户管理逻辑
│   │
│   ├── group/                  # 群组/知识库模块
│   │   ├── __init__.py
│   │   ├── router.py           # 路由: /api/groups/*, /api/invitations/*
│   │   ├── schemas.py
│   │   └── service.py
│   │
│   ├── document/               # 文档管理模块
│   │   ├── __init__.py
│   │   ├── router.py           # 路由: /api/documents/*
│   │   ├── schemas.py
│   │   ├── service.py
│   │   └── upload/             # 分片上传子模块
│   │       ├── __init__.py
│   │       ├── service.py
│   │       └── chunk_storage.py
│   │
│   ├── ingestion/              # 文档 ETL 管线
│   │   ├── __init__.py
│   │   ├── router.py           # 内部回调路由
│   │   ├── service.py          # 异步 ETL 编排
│   │   ├── tasks.py            # Celery 任务
│   │   └── pipeline/
│   │       ├── __init__.py
│   │       ├── parser.py       # 文档解析 (PDF/Word/Markdown/TXT)
│   │       ├── chunker.py      # 文本分块
│   │       ├── cleaner.py      # 文本清理
│   │       └── vectorizer.py   # 向量化与入库
│   │
│   ├── qa/                     # RAG 问答模块
│   │   ├── __init__.py
│   │   ├── router.py           # 路由: /api/qa/*
│   │   ├── schemas.py
│   │   ├── service.py          # 问答编排
│   │   ├── retrieval.py        # 混合检索 (ES + pgvector)
│   │   ├── query_planner.py    # LLM 查询规划
│   │   └── citation.py         # 引用组装
│   │
│   ├── assistant/              # AI 助手模块
│   │   ├── __init__.py
│   │   ├── router.py           # 路由: /api/assistant/*
│   │   ├── schemas.py
│   │   ├── service.py          # 对话编排
│   │   ├── agent.py            # ReAct Agent (替代 Java Agent 4 文件)
│   │   ├── memory.py           # 会话记忆管理
│   │   └── stream.py           # SSE 流式响应
│   │
│   ├── metrics/                # 用量统计模块
│   │   ├── __init__.py
│   │   ├── router.py           # 路由: /api/admin/metrics/*
│   │   ├── schemas.py
│   │   ├── service.py
│   │   └── collector.py        # LLM 用量收集
│   │
│   ├── engine/                 # 存储 & 检索引擎
│   │   ├── __init__.py
│   │   ├── postgres.py         # PostgreSQL 连接 & session 管理
│   │   ├── elasticsearch.py    # ES 客户端 & 索引服务
│   │   ├── minio.py            # MinIO 客户端封装
│   │   └── vector.py           # pgvector 检索适配器
│   │
│   └── models/                 # SQLAlchemy ORM 模型 (替代 Entity + Mapper)
│       ├── __init__.py
│       ├── base.py             # 基类 (id, created_at, updated_at)
│       ├── user.py
│       ├── user_refresh_token.py
│       ├── group.py
│       ├── group_membership.py
│       ├── group_invitation.py
│       ├── group_join_request.py
│       ├── document.py
│       ├── document_upload_session.py
│       ├── document_upload_chunk.py
│       ├── document_chunk.py
│       ├── ingestion_job.py
│       ├── assistant_session.py
│       ├── assistant_message.py
│       ├── assistant_session_context.py
│       └── llm_usage_record.py
│
├── prompts/                    # LLM Prompt 模板 (替代 .st 文件)
│   ├── qa/
│   │   ├── rag_context.j2
│   │   ├── system.j2
│   │   └── user.j2
│   ├── assistant/
│   │   ├── runtime_compact_summary.j2
│   │   ├── session_compact_summary.j2
│   │   └── session_memory_update.j2
│   └── query_planning/
│       └── user.j2
│
└── tests/                      # 测试
    ├── __init__.py
    ├── conftest.py             # fixtures: 测试数据库, 测试客户端
    ├── test_auth/
    ├── test_user/
    ├── test_group/
    ├── test_document/
    ├── test_qa/
    └── test_assistant/
```

---

## 四、核心组件对照迁移

### 4.1 Web 框架: Spring Boot → FastAPI

| Spring Boot 概念 | FastAPI 等价 | 说明 |
|------------------|-------------|------|
| `@RestController` | `APIRouter` + `@router.get/post/...` | 路由定义改为装饰器 |
| `@Service` | 普通 Python 类，通过依赖注入传递 | 去掉 `@Service` 注解 |
| `@Mapper` (MyBatis) | SQLAlchemy Session + Repository 模式 | ORM 方式完全不同 |
| `application.yml` | `.env` + `pydantic-settings` | 类型安全的配置管理 |
| `@Configuration` | 工厂函数 + `Depends()` | 显式依赖注入 |
| Filter / Interceptor | FastAPI Middleware + Dependency | 两种方式覆盖 |
| `@Async` / `@EventListener` | Celery Task / asyncio | 异步模式对应 |
| `@Scheduled` | Celery Beat / APScheduler | 定时任务 |
| `@Transactional` | SQLAlchemy Session 上下文管理 | 显式控制事务边界 |
| Spring Security | PyJWT + FastAPI Dependencies | 手动但更透明 |
| Spring Actuator | 自定义 `/health` + prometheus_client | 健康检查 |
| MyBatis XML Mapper | 纯 Python Repository 函数 | 用 SQLAlchemy 2.0 查询语法 |

#### 迁移示例: AuthController → FastAPI Router

**Java (当前):**
```java
@RestController
@RequestMapping("/api/auth")
public class AuthController {
    @PostMapping("/login")
    public ApiResponse<AuthTokensResponse> login(
            @Valid @RequestBody LoginRequest request,
            HttpServletResponse response) {
        // ...
    }
}
```

**Python (目标):**
```python
from fastapi import APIRouter, Response
from src.auth.schemas import LoginRequest, AuthTokensResponse
from src.common.response import ApiResponse

router = APIRouter(prefix="/api/auth", tags=["Auth"])

@router.post("/login", response_model=ApiResponse[AuthTokensResponse])
async def login(request: LoginRequest, response: Response) -> ApiResponse[AuthTokensResponse]:
    # ...
```

### 4.2 数据层: MyBatis-Plus → SQLAlchemy 2.0

| 当前 Java | 目标 Python |
|-----------|-------------|
| `BaseMapper<T>` 接口 | `BaseRepository` 泛型类 (自定义) |
| `LambdaQueryWrapper` | SQLAlchemy `select()` + `where()` |
| MyBatis XML 动态 SQL | SQLAlchemy 表达式语言 或 原生 SQL |
| MyBatis-Plus 分页插件 | `fastapi-pagination` 或手动 `LIMIT/OFFSET` |
| `@TableField` | 列属性在 `Column()` 中定义 |
| 自动填充 (`created_at`) | SQLAlchemy `default=` / `server_default=` |

#### 迁移示例: User Entity + Mapper → SQLAlchemy Model

**Java:**
```java
@Data
@TableName("users")
public class User {
    @TableId(type = IdType.ASSIGN_UUID)
    private String id;
    private String username;
    private String email;
    private String passwordHash;
    private SystemRole systemRole;
}

@Mapper
public interface UserMapper extends BaseMapper<User> {
    User selectByEmail(String email);
}
```

**Python:**
```python
from sqlalchemy import String, Enum, select
from sqlalchemy.orm import Mapped, mapped_column
from src.models.base import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_generator)
    username: Mapped[str] = mapped_column(String(100), unique=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column("password_hash", String(255))
    system_role: Mapped[SystemRole] = mapped_column(Enum(SystemRole, name="system_role"))

# 查询直接在 service 中使用 Repository 模式
class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        return (await self.session.execute(stmt)).scalar_one_or_none()
```

### 4.3 AI 集成: Spring AI → OpenAI Python SDK

| Spring AI 概念 | Python 等价 |
|---------------|-------------|
| `DashScopeChatModel` | `openai.AsyncOpenAI(base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")` |
| `ChatClient` | `await client.chat.completions.create()` |
| `ChatClient.builder().defaultAdvisors()` | 自定义 Pipeline 函数 |
| `Flux<SseEvent>` | `AsyncGenerator[str, None]` (SSE 流) |
| `StringTemplate` (`.st`) | Jinja2 模板 |
| Spring AI Tool 注解 | 函数签名描述 (OpenAI function calling) |

### 4.4 向量检索: pgvector 适配

Java 的 `PgVectorRetrievalAdapter` 手动构建 SQL 查询，Python 中 `pgvector` 库直接支持 SQLAlchemy:

```python
from pgvector.sqlalchemy import Vector as VectorColumn
from sqlalchemy import text

class VectorStore(Base):
    __tablename__ = "vector_store"
    id: Mapped[str] = ...
    embedding: Mapped[list[float]] = mapped_column(VectorColumn(512))

async def similarity_search(session: AsyncSession, query_vector: list[float], limit: int = 10):
    stmt = (
        select(VectorStore)
        .order_by(VectorStore.embedding.cosine_distance(query_vector))
        .limit(limit)
    )
    return (await session.execute(stmt)).scalars().all()
```

### 4.5 异步 ETL 管线: @Async/@EventListener → Celery

| Java 模式 | Python 等价 |
|-----------|-------------|
| `@EventListener(DocumentIngestionRequestedEvent)` | Celery Task 触发 |
| `@Async` CompletableFuture | `celery_app.send_task()` |
| `IngestionJob` 状态机 | Celery 任务状态 + 自定义 Job 表 |
| `DocumentIngestionAsyncService` | `tasks/ingestion.py` Celery Task |
| Polaris 分布式锁 (worker_id) | Redis 分布式锁/Celery 内置 |

### 4.6 认证机制: JJWT + BCrypt → PyJWT + passlib

```python
# JWT 生成
import jwt
from datetime import datetime, timedelta

def create_access_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

# 密码验证
from passlib.context import CryptContext
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
```

---

## 五、数据库迁移策略

### 5.1 总体策略: **保持现有数据库不变**

**不修改** 现有的 PostgreSQL 数据库结构，仅替换应用层代码。原因:
- 15 张表结构已经稳定运行
- pgvector 扩展无需变更
- 零数据迁移风险
- 可以做到**并行运行、逐步切流**

### 5.2 需要处理的差异

| 差异点 | Java 处理 | Python 处理 |
|--------|----------|-------------|
| 主键策略 (ASSIGN_UUID) | Java 端生成 32 位 UUID (无连字符) | Python 端 `uuid.uuid4().hex` |
| 枚举映射 | MyBatis-Plus 自动映射 Java Enum ↔ DB varchar | SQLAlchemy Enum 类型或手动 varchar 映射 |
| JSONB 字段 | MyBatis 自动序列化 | SQLAlchemy `JSONB` 类型自动处理 |
| pgvector `VECTOR(512)` | Spring AI 自动映射 `float[]` | `pgvector.sqlalchemy.Vector` |
| 时间戳 | `LocalDateTime` | `datetime.datetime` (UTC) |

### 5.3 迁移工具

创建 Alembic 初始迁移，使用 `--sql` 模式生成 SQL 供审核，不执行 DDL:

```bash
alembic init alembic
# 编辑 alembic.ini 指向现有 PG 数据库
alembic revision --autogenerate -m "initial_schema_from_existing_db"
```

---

## 六、API 兼容性保证

为保持前端无感知，新 Python 后端 **完全兼容** 现有 API 契约:

1. **URL 路径不变**: 所有 `/api/*` 路由保持一致
2. **请求/响应格式不变**: 保持统一的 `ApiResponse<T>` 包裹格式:
   ```json
   { "success": true, "code": 200, "data": {...}, "message": null }
   ```
3. **认证方式不变**: 仍使用 `Authorization: Bearer <token>` + httpOnly Cookie Refresh Token
4. **SSE 事件格式不变**: 流式响应事件类型保持一致 (`token`, `citation`, `error`, `done`)
5. **分片上传协议不变**: `init` → `chunks` → `complete` 流程完全兼容
6. **错误码体系不变**: 复用现有异常类体系

### API 兼容性测试策略

```python
# tests/test_api_compat.py - 使用现有前端请求录制作为测试用例
import httpx

async def test_login_returns_same_response_shape():
    """验证 Python 后端的 login 响应与 Java 完全一致"""
    async with httpx.AsyncClient(base_url=PYTHON_BACKEND) as client:
        resp = await client.post("/api/auth/login", json={...})
        assert resp.json()["success"] == True
        assert set(resp.json().keys()) == {"success", "code", "data", "message"}
```

---

## 七、分阶段实施计划

### 阶段 0: 基础设施搭建 (预计 2-3 天)

| 任务 | 产出 | 预估人天 |
|------|------|----------|
| 初始化 Python 项目 (uv/Poetry) | `pyproject.toml` 配置完成 | 0.5 |
| 配置 FastAPI 应用骨架 | Docker 中可启动的空应用 | 0.5 |
| SQLAlchemy 连接池配置 | 连接到现有 PG 数据库 | 0.5 |
| Alembic 初始迁移 | 从现有 DB 生成 ORM 模型 | 0.5 |
| ES + MinIO 客户端封装 | 连接验证通过 | 0.5 |
| CI/CD 流水线调整 | 可自动化构建 Python 镜像 | 1 |

### 阶段 1: 公共模块 + 认证 (预计 3-4 天)

| 任务 | 涉及文件 |
|------|----------|
| 统一响应 & 异常处理 | `common/response.py`, `common/exceptions.py`, `common/exception_handlers.py` |
| JWT 认证 + Cookie Refresh Token | `auth/jwt.py`, `auth/dependencies.py`, `auth/router.py` |
| 用户注册/登录/退出 | `auth/service.py`, `auth/schemas.py` |
| 当前用户上下文 (`UserContext`) | `common/security.py` |
| 操作日志中间件 | `common/logging_middleware.py` |
| **阶段 1 可独立部署验证** | `/api/auth/*` + `/api/account/*` |

### 阶段 2: 用户管理 + 群组 (预计 3-4 天)

| 任务 | 涉及文件 |
|------|----------|
| 用户个人账户管理 | `user/router.py`, `user/service.py` |
| 管理员用户管理 | `user/router.py` (admin endpoints) |
| 群组 CRUD + 成员管理 | `group/router.py`, `group/service.py` |
| 邀请 + 加入请求 | group 子路由 |
| 权限校验依赖注入 | `dependencies.py` |

### 阶段 3: 文档管理 + 存储引擎 (预计 5-6 天)

| 任务 | 涉及文件 |
|------|----------|
| MinIO 客户端封装 (兼容 S3) | `engine/minio.py` |
| 直接上传 + 分片上传 | `document/router.py`, `document/upload/` |
| 文档列表/预览/下载/删除 | `document/service.py` |
| Elasticsearch 索引服务 | `engine/elasticsearch.py` |
| **此阶段完成可替换文档模块** | 独立验证通过 |

### 阶段 4: ETL 管线 (预计 5-7 天) — **最复杂模块**

| 任务 | 涉及文件 |
|------|----------|
| Celery 任务框架搭建 | `ingestion/tasks.py` |
| PDF 解析 (pdfplumber/PyPDF2) | `ingestion/pipeline/parser.py` |
| Word 解析 (python-docx) | `ingestion/pipeline/parser.py` |
| Markdown/TXT 解析 | `ingestion/pipeline/parser.py` |
| 文本清洗 | `ingestion/pipeline/cleaner.py` |
| 语义分块 | `ingestion/pipeline/chunker.py` |
| 向量 embedding 生成 + pgvector 写入 | `ingestion/pipeline/vectorizer.py` |
| 异步任务状态管理 | `ingestion/service.py` |
| 启动恢复 (失败文档重试) | 应用 `startup` 事件 |

### 阶段 5: RAG 问答 (预计 4-5 天)

| 任务 | 涉及文件 |
|------|----------|
| 混合检索 (ES + pgvector) | `qa/retrieval.py` |
| LLM 查询规划 | `qa/query_planner.py` |
| 同步问答接口 | `qa/router.py` (POST /ask) |
| SSE 流式问答 | `qa/router.py` (POST /stream-ask) |
| 引用组装 | `qa/citation.py` |
| Prompt 模板 (Jinja2) | `prompts/qa/*.j2` |

### 阶段 6: AI 助手 (预计 4-5 天)

| 任务 | 涉及文件 |
|------|----------|
| 会话 CRUD | `assistant/router.py` |
| 同步/流式聊天 | `assistant/service.py`, `assistant/stream.py` |
| ReAct Agent 实现 | `assistant/agent.py` |
| 知识库工具 (Tool) | `assistant/agent.py` |
| 会话记忆/摘要 | `assistant/memory.py` |
| 记忆压缩/定时维护 | `assistant/memory.py` |

### 阶段 7: 用量统计 + 收尾 (预计 2-3 天)

| 任务 | 涉及文件 |
|------|----------|
| 用量收集器 | `metrics/collector.py` |
| 统计/趋势/排名接口 | `metrics/router.py`, `metrics/service.py` |
| 健康检查端点 | `main.py` |
| 全局测试 + 集成测试 | `tests/` |
| API 兼容性回归测试 | `tests/test_api_compat.py` |

### 阶段 8: 部署 + 灰度切换 (预计 2-3 天)

| 任务 |
|------|
| Dockerfile 编写 + 多阶段构建优化 |
| docker-compose 更新 (替换 Java 服务) |
| 蓝绿部署: Java/Python 并行运行 |
| 灰度切流: 按路由逐步切换 DNS/Nginx |
| 监控告警配置 (Prometheus metrics) |
| 性能基准测试 (Java vs Python) |

---

## 八、总工时估算

| 阶段 | 内容 | 人天 |
|------|------|------|
| 0 | 基础设施 | 2-3 |
| 1 | 公共模块 + 认证 | 3-4 |
| 2 | 用户管理 + 群组 | 3-4 |
| 3 | 文档管理 + 存储 | 5-6 |
| 4 | ETL 管线 | 5-7 |
| 5 | RAG 问答 | 4-5 |
| 6 | AI 助手 | 4-5 |
| 7 | 统计 + 收尾 | 2-3 |
| 8 | 部署上线 | 2-3 |
| **合计** | | **27-37 人天** |

---

## 九、风险识别与应对

| 风险 | 影响 | 概率 | 应对措施 |
|------|------|------|----------|
| **ES 查询语法差异** | 检索结果不一致 | 中 | Java elasticsearch-java → elasticsearch-py 查询 DSL 逐条对照验证，编写对比测试 |
| **PDF 解析质量差异** | 中文文档抽取不完整 | 高 | 提前对比 PDFBox vs pdfplumber/PyMuPDF 抽取质量；保留 Java 解析器作为备选 |
| **pgvector 向量精度差异** | 相似度排序差异 | 低 | 同一模型 (text-embedding-v3)，嵌入算法一致，仅序列化差异 |
| **Celery 任务可靠性** | ETL 失败重试不如 Java 内建的 CompletableFuture | 中 | 配置 Celery 死信队列 + 幂等重试；保留自定义 Job 状态表 |
| **性能回退** | Python GIL 导致高并发下吞吐下降 | 中 | Uvicorn + `workers=N` 多进程模式；异步任务 (Celery) 避开 GIL |
| **SSE 流式输出中断** | 长时间 SSE 连接不稳定 | 低 | FastAPI `StreamingResponse` + 心跳 keep-alive；超时配置 |
| **数据库连接池差异** | SQLAlchemy asyncpg vs HikariCP 性能差异 | 低 | asyncpg 连接池性能优秀；配置合适的 pool_size |
| **依赖缺失** | 某个 Maven 依赖在 Python 生态中无对应库 | 中 | 阶段 0 提前验证所有依赖映射，需要时编写适配层 |

### 关键风险: PDF 解析质量

当前 Java 使用 Apache PDFBox 2.0.31，Python 可选:

| 方案 | 优点 | 缺点 |
|------|------|------|
| pdfplumber | 表格提取优秀 | 纯英文文档提取略慢 |
| PyMuPDF (fitz) | 速度最快 | 部分中文 PDF 需要字体处理 |
| pdfplumber + PyMuPDF | 双引擎兜底 | 复杂度增加 |

**建议**: 使用 PyMuPDF 作为主引擎，pdfplumber 作为表格文档的备选。

---

## 十、关键决策点 (需确认)

1. **Celery vs 纯 asyncio 后台任务**: 如果不需要分布式 worker 和定时重试，可以用 FastAPI `BackgroundTasks` + `asyncio` 简化；但如果未来需要水平扩展 ETL，Celery 是更好的选择。

2. **保持 pgvector vs 迁移到专业向量库 (Milvus/Qdrant)**: 当前 512 维向量 + HNSW 索引在 pgvector 上性能足够，建议保持不动，减少基础设施迁移。

3. **前台 API 全异步 vs 部分同步**: FastAPI 路由默认 `async def`，但 SQLAlchemy async 下数据库操作也需要异步。建议全部使用 async session。

4. **LangChain vs 纯 OpenAI SDK**: LangChain 提供了 RAG 编排抽象但抽象层厚重。当前 Java 代码未使用 LangChain4j，而是直接与 DashScope 交互。建议 Python 端也保持轻量，直接使用 openai SDK。

---

## 十一、附录

### A. 依赖对照速查表

| Java 依赖 | Python 替代 |
|-----------|-------------|
| `spring-boot-starter-web` | `fastapi` + `uvicorn` |
| `spring-boot-starter-security` | `fastapi` + `python-jose` + `passlib` |
| `mybatis-plus-spring-boot3-starter` | `sqlalchemy[asyncio]` + `asyncpg` |
| `spring-ai-alibaba-starter-dashscope` | `openai` (兼容模式) |
| `spring-ai-pgvector-store` | `pgvector` + `sqlalchemy` |
| `elasticsearch-java (8.15)` | `elasticsearch-py (8.x)` |
| `minio (8.5.x)` | `boto3` |
| `knife4j-openapi3-jakarta` | FastAPI 内建 OpenAPI |
| `pdfbox (2.0.31)` | `pdfplumber` / `PyMuPDF` |
| `poi / poi-ooxml (5.2.5)` | `python-docx` |
| `lombok` | Pydantic + `@dataclass` |
| `spring-boot-starter-actuator` | `prometheus_client` + 自定义 `/health` |
| Maven Wrapper | `uv` / `Poetry` |

### B. 数据库表映射清单

| # | 表名 | Java Entity | Python Model |
|---|------|-------------|--------------|
| 1 | `users` | `User` | `models/user.py: User` |
| 2 | `user_refresh_tokens` | `UserRefreshToken` | `models/user_refresh_token.py` |
| 3 | `groups` | `GroupEntity` | `models/group.py: Group` |
| 4 | `group_memberships` | `GroupMembershipEntity` | `models/group_membership.py` |
| 5 | `group_invitations` | `GroupInvitationEntity` | `models/group_invitation.py` |
| 6 | `group_join_requests` | `GroupJoinRequestEntity` | `models/group_join_request.py` |
| 7 | `documents` | `DocumentEntity` | `models/document.py` |
| 8 | `document_upload_sessions` | `DocumentUploadSessionEntity` | `models/document_upload_session.py` |
| 9 | `document_upload_chunks` | `DocumentUploadChunkEntity` | `models/document_upload_chunk.py` |
| 10 | `document_chunks` | `DocumentChunkEntity` | `models/document_chunk.py` |
| 11 | `ingestion_jobs` | `IngestionJobEntity` | `models/ingestion_job.py` |
| 12 | `vector_store` | (pgvector Spring AI 管理) | `models/vector_store.py` |
| 13 | `assistant_sessions` | `AssistantSessionEntity` | `models/assistant_session.py` |
| 14 | `assistant_messages` | `AssistantMessageEntity` | `models/assistant_message.py` |
| 15 | `assistant_session_contexts` | `AssistantSessionContextEntity` | `models/assistant_session_context.py` |
| — | `llm_usage_records` | `LlmUsageRecordEntity` | `models/llm_usage_record.py` |

### C. API 端点完整清单 (逐步迁移检查表)

```
Auth (5)
  [ ] POST /api/auth/login
  [ ] POST /api/auth/register
  [ ] POST /api/auth/refresh
  [ ] POST /api/auth/logout
  [ ] GET  /api/auth/me

Account (1)
  [ ] POST /api/account/change-password

Admin Users (3)
  [ ] GET  /api/admin/users
  [ ] GET  /api/admin/users/{userId}
  [ ] PATCH /api/admin/users/{userId}/status

Groups (14)
  [ ] POST   /api/groups
  [ ] GET    /api/groups/my
  [ ] GET    /api/groups/invitations/my-sent
  [ ] GET    /api/groups/{groupId}/members
  [ ] DELETE /api/groups/{groupId}/members/{userId}
  [ ] POST   /api/groups/{groupId}/leave
  [ ] POST   /api/groups/{groupId}/invitations
  [ ] POST   /api/groups/join-requests
  [ ] GET    /api/groups/join-requests/my
  [ ] GET    /api/groups/{groupId}/join-requests
  [ ] POST   /api/groups/{groupId}/join-requests/{requestId}/approve
  [ ] POST   /api/groups/{groupId}/join-requests/{requestId}/reject

Invitations (3)
  [ ] POST /api/invitations/{invitationId}/accept
  [ ] POST /api/invitations/{invitationId}/reject
  [ ] POST /api/invitations/{invitationId}/cancel

Documents (11)
  [ ] POST   /api/documents/upload/init
  [ ] POST   /api/documents/upload/chunks
  [ ] GET    /api/documents/upload/{uploadId}
  [ ] POST   /api/documents/upload/{uploadId}/complete
  [ ] POST   /api/documents/upload
  [ ] GET    /api/documents
  [ ] DELETE /api/documents/{documentId}
  [ ] POST   /api/documents/{documentId}/retry-ingestion
  [ ] GET    /api/documents/{documentId}/preview
  [ ] GET    /api/documents/{documentId}/download

QA (2)
  [ ] POST /api/qa/ask
  [ ] POST /api/qa/stream-ask

Assistant (8)
  [ ] POST   /api/assistant/chat
  [ ] POST   /api/assistant/chat/stream
  [ ] POST   /api/assistant/sessions
  [ ] GET    /api/assistant/sessions
  [ ] GET    /api/assistant/sessions/{sessionId}
  [ ] PATCH  /api/assistant/sessions/{sessionId}
  [ ] DELETE /api/assistant/sessions/{sessionId}
  [ ] GET    /api/assistant/sessions/{sessionId}/context

Admin Metrics (7)
  [ ] GET /api/admin/metrics/overview
  [ ] GET /api/admin/metrics/platform
  [ ] GET /api/admin/metrics/user/{userId}
  [ ] GET /api/admin/metrics/group/{groupId}
  [ ] GET /api/admin/metrics/trend
  [ ] GET /api/admin/metrics/rank/users
  [ ] GET /api/admin/metrics/rank/groups

总计: ~44 端点
```
