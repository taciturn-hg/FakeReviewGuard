
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
    # 生产环境请在 .env 中配置 DATABASE_URL
    DATABASE_URL: str = "mysql+pymysql://fake_review_guard:123456@localhost:3306/fake_review_guard"
    
    # Security
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # LLM Configuration
    # DeepSeek Config
    # 生产环境请在 .env 中配置 API Key
    LLM_API_KEY: str = "sk-afc7316c31784ae5b7db844c482410be"
    LLM_MODEL_NAME: str = "deepseek-chat" 
    LLM_API_BASE: str = "https://api.deepseek.com"
    DEEPSEEK_API_KEY: str = "sk-afc7316c31784ae5b7db844c482410be"
    
    # Crawler Configuration
    CRAWLER_USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    CRAWLER_TIMEOUT: int = 30
    
settings = Settings()
