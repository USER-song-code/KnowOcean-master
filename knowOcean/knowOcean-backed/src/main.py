"""KnowOcean Python Backend — FastAPI 应用入口

对照 Java: KnowOceanBackendApplication.java (SpringBootApplication)

启动: uvicorn src.main:app --host 0.0.0.0 --port 10001 --reload
"""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.config import get_settings
from src.common.exception_handlers import register_exception_handlers
from src.auth.router import router as auth_router
from src.user.router import account_router, admin_user_router
from src.group.router import group_router, invitation_router
from src.document.router import router as document_router
from src.qa.router import router as qa_router
from src.assistant.router import router as assistant_router
from src.metrics.router import router as metrics_router
from src.logging.router import router as oplog_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动
    if settings.dev_admin_enabled:
        from src.database.session import async_session_factory
        async with async_session_factory() as session:
            from sqlalchemy import select
            from src.models.user import User
            from src.auth.jwt import hash_password
            import uuid

            stmt = select(User).where(User.username == settings.dev_admin_username)
            result = await session.execute(stmt)
            admin = result.scalar_one_or_none()

            if admin is None:
                admin = User(
                    user_code=uuid.uuid4().hex[:32],
                    username=settings.dev_admin_username,
                    email=settings.dev_admin_email,
                    display_name="系统管理员",
                    password_hash=hash_password(settings.dev_admin_password),
                    system_role="ADMIN",
                )
                session.add(admin)
                await session.commit()

    # 启动 Mock ETL 后台任务 (仅开发环境)
    mock_etl_task = None
    if settings.mock_etl_enabled:
        try:
            from src.document.mock_etl import start_mock_etl_loop
            mock_etl_task = asyncio.create_task(start_mock_etl_loop())
        except Exception:
            pass

    yield

    if mock_etl_task:
        mock_etl_task.cancel()
    from src.database.session import engine
    await engine.dispose()


app = FastAPI(
    title="KnowOcean API",
    description="KnowOcean RAG 知识平台 — Python 后端 (从 Spring Boot 迁移)",
    version="5.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(auth_router)
app.include_router(account_router)
app.include_router(admin_user_router)
app.include_router(group_router)
app.include_router(invitation_router)
app.include_router(document_router)
app.include_router(qa_router)
app.include_router(assistant_router)
app.include_router(metrics_router)
app.include_router(oplog_router)


@app.get("/", tags=["Health"])
async def root():
    return {"service": "KnowOcean Python Backend", "status": "running"}


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "UP"}
