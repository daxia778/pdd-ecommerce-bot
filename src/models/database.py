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
from sqlalchemy import (
    create_engine, Column, Integer, String, Text,
    DateTime, Boolean
)
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from config.settings import settings


class Base(DeclarativeBase):
    pass


class Message(Base):
    """对话消息记录"""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(64), nullable=False, index=True)
    platform = Column(String(16), default="test")     # 'pdd' / 'test'
    role = Column(String(16), nullable=False)          # 'user' / 'assistant'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now)


class Escalation(Base):
    """需要人工跟进的升级记录"""
    __tablename__ = "escalations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(64), nullable=False, index=True)
    platform = Column(String(16), default="test")
    trigger_message = Column(Text)    # 买家发的触发升级的消息
    ai_reply = Column(Text)           # AI 的回复（含转人工提示）
    reason = Column(String(64))       # 升级原因标签: 'large_order','bargain','urgent','complaint','other'
    status = Column(String(16), default="pending")    # 'pending' / 'claimed' / 'resolved'
    created_at = Column(DateTime, default=datetime.now)
    # P0-5: 新增 claimed_at，不再误用 resolved_at 记录接单时间
    claimed_at = Column(DateTime, nullable=True)       # 接单时间
    resolved_at = Column(DateTime, nullable=True)      # 最终处理完成时间
    operator_note = Column(Text, nullable=True)        # 人工客服备注
    operator_name = Column(String(64), nullable=True)  # 接单客服名称


class Session(Base):
    """会话元信息"""
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(64), nullable=False, unique=True, index=True)
    platform = Column(String(16), default="test")
    status = Column(String(16), default="active")     # 'active' / 'escalated' / 'closed'
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
    
    # 状态机：'consulting' -> 'req_fixed' -> 'generating' -> 'processing' -> 'awaiting_review' -> 'shipped'
    status = Column(String(32), default="consulting")
    
    # 结构化需求 (JSON 存储)
    requirement_json = Column(Text, nullable=True)  # {"topic": "...", "pages": 10, "style": "..."}
    
    # 生成结果
    file_url = Column(Text, nullable=True)         # 生成的 PPT 下载链接 (含/不含水印)
    clean_file_url = Column(Text, nullable=True)   # 去水印后的下载链接
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    generated_at = Column(DateTime, nullable=True)  # 开始生成时间
    shipped_at = Column(DateTime, nullable=True)    # 最终发货时间


# ===== 数据库引擎 =====

def _make_engine():
    db_url = settings.db_url
    # 确保目录存在
    if db_url.startswith("sqlite:///"):
        db_path = db_url.replace("sqlite:///", "")
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
            
    engine = create_engine(
        db_url,
        connect_args={"check_same_thread": False},  # SQLite 多线程安全
        echo=False,
    )
    
    # P0-3/P0-8: 对于 SQLite，启用 WAL 模式和 Normal 同步模式，大幅提升高并发下的读写性能与稳定性
    if db_url.startswith("sqlite"):
        from sqlalchemy import event
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA cache_size=-64000") # 64MB Cache
            cursor.close()
            
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
