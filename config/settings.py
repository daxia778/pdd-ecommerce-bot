"""
应用配置管理 - 使用 Pydantic Settings 从 .env 文件读取所有配置。

P1-7 增强: 新增 rag_relevance_threshold 配置项（RAG 相关性阈值）
P0-3 修复: 补充 deepseek_key_list / gemini_key_list 解析 property
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


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
    # Webhook HMAC 签名密钥（空 = 跳过签名校验）
    pdd_webhook_secret: str = ""

    # ===== 数据库 =====
    db_url: str = "sqlite:///./data/sqlite/pdd_ecommerce.db"
    chroma_db_dir: str = "./data/chroma"

    # ===== Redis / Queue =====
    redis_url: str = "redis://localhost:6379/0"

    # ===== Admin Auth =====
    admin_username: str = "admin"
    admin_password: str = "pddbot2026"
    admin_password_hash: str = ""

    # JWT 签名密钥（生产环境务必在 .env 中设置为随机长字符串）
    jwt_secret_key: str = "dev-secret-key-change-in-prod"

    # ===== CORS 配置 =====
    # 逗号分隔的允许跨域来源；生产环境改为实际域名
    cors_origins: str = "http://localhost:8100,http://127.0.0.1:8100,http://localhost:3000"

    # ===== 企业微信配置（对接设计师工作流）=====
    wecom_corp_id: str = ""  # 企业ID
    wecom_corp_secret: str = ""  # 应用Secret
    wecom_agent_id: int = 0  # 应用AgentId
    # 默认通知的设计师 UserID 列表（逗号分隔）
    wecom_default_notify_ids_str: str = ""

    @property
    def wecom_default_notify_ids(self) -> list[str]:
        return [uid.strip() for uid in self.wecom_default_notify_ids_str.split(",") if uid.strip()]

    # ===== 网络代理 =====
    http_proxy: str = ""
    https_proxy: str = ""

    # ===== NotebookLM 自动化配置 =====
    # 目标笔记本 URL（打开笔记本后复制地址栏 URL 填入 .env）
    notebooklm_notebook_url: str = "https://notebooklm.google.com/"
    # 本服务对外 URL（用于构造生成文件的下载链接）
    pdd_bot_base_url: str = "http://localhost:8100"

    # ===== 解析后的 Key 列表 =====
    @property
    def zhipu_key_list(self) -> list[str]:
        return [k.strip() for k in self.zhipu_api_keys.split(",") if k.strip()]

    @property
    def has_zhipu_keys(self) -> bool:
        return len(self.zhipu_key_list) > 0

    # P0-3: 补充 DeepSeek & Gemini 的 Key 列表解析
    @property
    def deepseek_key_list(self) -> list[str]:
        return [k.strip() for k in self.deepseek_api_keys.split(",") if k.strip()]

    @property
    def has_deepseek_keys(self) -> bool:
        return len(self.deepseek_key_list) > 0

    @property
    def gemini_key_list(self) -> list[str]:
        return [k.strip() for k in self.gemini_api_keys.split(",") if k.strip()]

    @property
    def has_gemini_keys(self) -> bool:
        return len(self.gemini_key_list) > 0


# 全局单例
settings = Settings()
