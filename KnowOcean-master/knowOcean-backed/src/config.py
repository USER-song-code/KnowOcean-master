"""KnowOcean Python Backend — 全局配置

对照 Java: AuthProperties.java + application.yml
"""
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    # === 服务器 ===
    server_host: str = "0.0.0.0"
    server_port: int = 10001
    debug: bool = False

    # === 数据库 ===
    database_host: str = "localhost"
    database_port: int = 5432
    database_name: str = "dd_rag"
    database_user: str = "postgres"
    database_password: str = ""

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.database_user}:{self.database_password}@{self.database_host}:{self.database_port}/{self.database_name}"

    @property
    def database_url_sync(self) -> str:
        return f"postgresql+psycopg2://{self.database_user}:{self.database_password}@{self.database_host}:{self.database_port}/{self.database_name}"

    # === JWT ===
    jwt_secret_key: str = "change-me-to-a-32-byte-random-secret-key"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 14
    jwt_refresh_cookie_name: str = "KnowOcean_DD_RAG_REFRESH_TOKEN"
    jwt_refresh_cookie_secure: bool = False
    jwt_refresh_cookie_http_only: bool = True
    jwt_refresh_cookie_same_site: str = "lax"

    # === AI 模型 ===
    dashscope_api_key: str = ""
    openai_api_key: str = ""
    dashscope_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode"
    ai_chat_model: str = "deepseek-v4-pro"
    ai_embedding_model: str = "text-embedding-v3"
    ai_embedding_dimensions: int = 512

    # === Elasticsearch ===
    es_host: str = "localhost"
    es_port: int = 9200
    es_index_name: str = "dd_rag_document_chunks"

    # === MinIO ===
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "knowocean-rag-documents"
    minio_secure: bool = False

    # === Redis ===
    redis_url: str = "redis://localhost:6379/0"

    # === Dev Admin ===
    dev_admin_enabled: bool = False
    dev_admin_username: str = "admin"
    dev_admin_password: str = "Admin123456"
    dev_admin_email: str = "admin@KnowOcean.local"

    # === 日志 ===
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
