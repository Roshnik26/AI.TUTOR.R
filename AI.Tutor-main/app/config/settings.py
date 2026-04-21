from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    APP_NAME: str = "Vector search"
    ENV: str = Field(default="development")
    DEBUG: bool = True

    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # Milvus
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    MILVUS_USER: str | None = None
    MILVUS_PASSWORD: str | None = None
    MILVUS_DB_NAME: str = "default"
    MILVUS_COLLECTION_NAME: str = "documents"

    VECTOR_DIMENSION: int = 384   # ⚠️ MiniLM uses 384, not 768
    INDEX_TYPE: str = "IVF_FLAT"
    METRIC_TYPE: str = "L2"
    NLIST: int = 128

    # Auth / security
    SECRET_KEY: str = "change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # 🔑 Mistral
    MISTRAL_API_KEY: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
