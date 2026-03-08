"""
Alembic 迁移环境配置

L1 企业化: 从 config/settings.py 动态获取数据库 URL，
与项目统一配置源，无需在 alembic.ini 中硬编码 DB 地址。
"""

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# 将项目根目录加入 Python 路径，确保 from config.settings 等导入正常
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import settings  # noqa: E402
from src.models.database import Base  # noqa: E402

# Alembic Config 对象
config = context.config

# 动态设置数据库 URL（从 config/settings.py 读取，而不是 alembic.ini 硬编码）
config.set_main_option("sqlalchemy.url", settings.db_url)

# Python logging 配置
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 将项目模型的 MetaData 注册到 Alembic，使 autogenerate 能感知所有表
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """离线模式：仅生成 SQL 脚本，不实际连接数据库。"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # 让 Alembic 在 autogenerate 时能生成 render_as_batch 模式的迁移
        # （SQLite 不支持 ALTER COLUMN，需要重建表）
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """在线模式：连接数据库并执行迁移。"""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # SQLite 不支持 ALTER COLUMN，必须用 batch 模式
            render_as_batch=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
