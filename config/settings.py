"""
应用配置管理 - 使用 Pydantic Settings 从 .env 文件读取所有配置。

P1-7 增强: 新增 rag_relevance_threshold 配置项（RAG 相关性阈值）
"""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ===== LLM 配置 =====
    llm_provider: str = "zhipu"
    # 支持逗号分隔的多 Key，系统自动 Round-Robin
    zhipu_api_keys: str = ""
    deepseek_api_keys: str = ""
    gemini_api_keys: str = ""

    main_chat_model: str = "glm-4-flash"
    embedding_model: str = "embedding-3"

    # ===== 性能配置 =====
    max_history_length: int = 10
    max_retries: int = 3

    # ===== RAG 配置 =====
    # P1-7: RAG 相关性阈值，低于此分数的知识片段不注入 Prompt（0.0 = 不过滤）
    rag_relevance_threshold: float = 0.3

    # ===== 平台配置 (预留) =====
    pdd_app_key: str = ""
    pdd_app_secret: str = ""
    pdd_access_token: str = ""

    # ===== 数据库 =====
    db_url: str = "sqlite:///./data/sqlite/pdd_ecommerce.db"
    chroma_db_dir: str = "./data/chroma"
    
    # ===== Redis / Queue =====
    redis_url: str = "redis://localhost:6379/0"

    # ===== Admin Auth =====
    admin_username: str = "admin"
    admin_password: str = "pddbot2026"

    # ===== 网络代理 =====

    http_proxy: str = ""
    https_proxy: str = ""

    # ===== 解析后的 Key 列表 =====
    @property
    def zhipu_key_list(self) -> List[str]:
        return [k.strip() for k in self.zhipu_api_keys.split(",") if k.strip()]

    @property
    def has_zhipu_keys(self) -> bool:
        return len(self.zhipu_key_list) > 0


# 全局单例
settings = Settings()
