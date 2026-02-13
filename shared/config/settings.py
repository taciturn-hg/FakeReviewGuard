
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Pydantic v2 推荐配置写法
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore" # 忽略 .env 中多余的字段
    )

    # Project Info
    PROJECT_NAME: str = "FakeReviewGuard"
    VERSION: str = "1.0.0"
    
    # Database
    # 格式: mysql+pymysql://user:password@host:port/dbname
    DATABASE_URL: str = "mysql+pymysql://fake_review_guard:123456@localhost:3306/fake_review_guard"
    
    # Security
    SECRET_KEY: str = "B6sTXbttgaNk-klxVSnbswwZ2MpoEmIT3WBn-TMmjC4"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # LLM Configuration
    LLM_API_KEY: str = "your-api-key-here"
    LLM_MODEL_NAME: str = "gpt-3.5-turbo" # or local model path
    LLM_API_BASE: str = "https://api.openai.com/v1"
    
    # Crawler Configuration
    CRAWLER_USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    CRAWLER_TIMEOUT: int = 30
    
settings = Settings()
