"""
数据库模型定义 - 使用 SQLAlchemy (同步模式，适合 SQLite)。

表结构：
  messages     - 所有对话消息（永久存储）
  escalations  - 需要人工介入的升级记录
  sessions     - 会话元信息（活跃状态、平台来源）

P0-5 修复: Escalation 新增 claimed_at 字段，不再误用 resolved_at 记录接单时间
"""

import os
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from config.settings import settings


class Base(DeclarativeBase):
    pass


class Message(Base):
    """对话消息记录"""

    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(64), nullable=False, index=True)
    platform = Column(String(16), default="test")  # 'pdd' / 'test'
    role = Column(String(16), nullable=False)  # 'user' / 'assistant'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now)


class Escalation(Base):
    """需要人工跟进的升级记录"""

    __tablename__ = "escalations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(64), nullable=False, index=True)
    platform = Column(String(16), default="test")
    trigger_message = Column(Text)  # 买家发的触发升级的消息
    ai_reply = Column(Text)  # AI 的回复（含转人工提示）
    reason = Column(String(64))  # 升级原因标签: 'large_order','bargain','urgent','complaint','other'
    status = Column(String(16), default="pending")  # 'pending' / 'claimed' / 'resolved'
    created_at = Column(DateTime, default=datetime.now)
    # P0-5: 新增 claimed_at，不再误用 resolved_at 记录接单时间
    claimed_at = Column(DateTime, nullable=True)  # 接单时间
    resolved_at = Column(DateTime, nullable=True)  # 最终处理完成时间
    operator_note = Column(Text, nullable=True)  # 人工客服备注
    operator_name = Column(String(64), nullable=True)  # 接单客服名称


class Session(Base):
    """会话元信息"""

    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(64), nullable=False, unique=True, index=True)
    platform = Column(String(16), default="test")
    status = Column(String(16), default="active")  # 'active' / 'escalated' / 'closed'
    is_ai_paused = Column(Boolean, default=False)  # P1-L2: 是否已暂停 AI 自动回复（人工接管使用）
    message_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class Order(Base):
    """PPT 生产流水线订单记录"""

    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_sn = Column(String(64), unique=True, index=True)  # PDD 订单号或系统生成单号
    user_id = Column(String(64), nullable=False, index=True)
    platform = Column(String(16), default="pdd")

    # 订单类型: 'single_page' / 'standard' / 'large'
    order_type = Column(String(16), default="standard")
    # 紧急度: 'normal' / 'urgent' / 'very_urgent'
    urgency = Column(String(16), default="normal")

    # 状态机：'consulting' -> 'req_fixed' -> 'wechat_pending' -> 'generating' -> 'processing' -> 'awaiting_review' -> 'shipped'
    status = Column(String(32), default="consulting")

    # 结构化需求 (JSON 存储)
    requirement_json = Column(Text, nullable=True)  # {"topic":"..","pages":10,"style":".."}

    # 微信对接信息
    wechat_qr_image_path = Column(Text, nullable=True)  # 顾客微信二维码图片存储路径
    wechat_added = Column(Boolean, default=False)  # 是否已添加微信
    wecom_chat_id = Column(String(64), nullable=True)  # 企业微信群聊 chatid

    # 生成结果
    file_url = Column(Text, nullable=True)  # 生成的 PPT 下载链接 (含/不含水印)
    clean_file_url = Column(Text, nullable=True)  # 去水印后的下载链接
    error_message = Column(Text, nullable=True)  # P1-L1: 生成失败时的异常信息

    # 时间戳
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    generated_at = Column(DateTime, nullable=True)  # 开始生成时间
    shipped_at = Column(DateTime, nullable=True)  # 最终发货时间


# ===== 数据库引擎 =====


def _make_engine():
    db_url = settings.db_url
    # 确保目录存在
    if db_url.startswith("sqlite:///"):
        db_path = db_url.replace("sqlite:///", "")
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

    connect_args = {}
    engine_kwargs = {"echo": False}

    if db_url.startswith("sqlite"):
        # SQLite 需特殊参数绕过多线程保护
        # P1-1: timeout=15 —— 让 SQLite 驱动在遇到写锁争用时自旋最多 15s，
        #        而非立刻抛出 OperationalError: database is locked。
        #        与下方 PRAGMA busy_timeout 双重保障，适配多个 BackgroundTasks 并发写入场景。
        connect_args = {
            "check_same_thread": False,
            "timeout": 15,
        }
    else:
        # PostgreSQL / MySQL 的生产级连接池配置
        engine_kwargs["pool_size"] = 10
        engine_kwargs["max_overflow"] = 20
        engine_kwargs["pool_pre_ping"] = True

    engine = create_engine(
        db_url,
        connect_args=connect_args,
        **engine_kwargs,
    )

    # P0-3/P0-8: 对于 SQLite，启用 WAL 模式和 Normal 同步模式，大幅提升并发读写性能
    if db_url.startswith("sqlite"):
        from sqlalchemy import event

        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA cache_size=-64000")  # 64MB Cache
            # P1-1: PRAGMA busy_timeout 作为 C 层二重保障（单位毫秒）
            # 即使 Python 层 timeout 未触发，底层 SQLite C 库也会自旋等待
            cursor.execute("PRAGMA busy_timeout=15000")
            cursor.close()
    else:
        # P3: 对于 PostgreSQL/MySQL 等，直接返回连接池引擎
        pass

    return engine


engine = _make_engine()
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def create_tables():
    """创建所有表（幂等操作）"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI 依赖注入：获取 DB Session（用完自动关闭）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
