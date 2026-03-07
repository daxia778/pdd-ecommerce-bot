"""
pytest 基础测试套件 - 覆盖核心业务逻辑。

运行方式:
    pytest tests/ -v
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

# ============================
# 1. auth.py: 密码哈希验证
# ============================


class TestPasswordVerification:
    """测试密码哈希/校验逻辑"""

    def test_plain_password_backward_compat(self):
        """向后兼容：明文密码（无冒号）直接 compare_digest"""
        from src.utils.auth import verify_password

        assert verify_password("pddbot2026", "pddbot2026") is True

    def test_plain_password_wrong(self):
        from src.utils.auth import verify_password

        assert verify_password("wrongpass", "pddbot2026") is False

    def test_hashed_password_correct(self):
        """哈希密码正确匹配"""
        from scripts.generate_hash import hash_password
        from src.utils.auth import verify_password

        hashed = hash_password("testpass123")
        assert verify_password("testpass123", hashed) is True

    def test_hashed_password_wrong(self):
        """哈希密码错误不匹配"""
        from scripts.generate_hash import hash_password
        from src.utils.auth import verify_password

        hashed = hash_password("testpass123")
        assert verify_password("wrongpass", hashed) is False

    def test_hashed_password_tampered(self):
        """篡改后的哈希不应通过"""
        from src.utils.auth import verify_password

        fake_hash = "sha256:fakesalt:fakehexhash"
        assert verify_password("anything", fake_hash) is False


# ============================
# 2. escalation_detector.py
# ============================


class TestEscalationDetector:
    """测试人工升级检测"""

    def test_detect_escalation_keyword(self):
        from src.core.escalation_detector import detect_escalation

        assert detect_escalation("亲，已为您标记，人工客服会尽快跟进") is True

    def test_no_escalation_normal_reply(self):
        from src.core.escalation_detector import detect_escalation

        has = detect_escalation("您好，我们的PPT定制价格从150元起。")
        assert has is False

    def test_identify_reason_bargain(self):
        from src.core.escalation_detector import identify_reason

        code, label = identify_reason("能不能便宜一点，少一点")
        assert code == "bargain"

    def test_identify_reason_urgent(self):
        from src.core.escalation_detector import identify_reason

        code, label = identify_reason("我今天就要用！加急！")
        assert code == "urgent"

    def test_identify_reason_complaint(self):
        from src.core.escalation_detector import identify_reason

        code, label = identify_reason("这个根本不对，我要投诉！")
        assert code == "complaint"

    def test_identify_reason_other(self):
        from src.core.escalation_detector import identify_reason

        code, label = identify_reason("我想了解一下")
        assert code == "other"


# ============================
# 3. db_service.py: SQLite CRUD
# ============================


@pytest.fixture
def in_memory_db():
    """创建内存 SQLite 用于测试，测试后自动销毁"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from src.models.database import Base

    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    yield db
    db.close()


class TestDbService:
    """测试数据库 CRUD 操作"""

    def test_save_message_and_upsert_session(self, in_memory_db):
        from src.models.database import Session as SessionModel
        from src.services.db_service import save_message_and_upsert_session

        msg = save_message_and_upsert_session(
            in_memory_db, user_id="test_user", role="user", content="你好", platform="test"
        )
        assert msg.id is not None
        assert msg.content == "你好"

        # 验证 session 被创建
        session = in_memory_db.query(SessionModel).filter_by(user_id="test_user").first()
        assert session is not None
        assert session.message_count == 1

    def test_message_count_increments(self, in_memory_db):
        from src.models.database import Session as SessionModel
        from src.services.db_service import save_message_and_upsert_session

        for i in range(3):
            save_message_and_upsert_session(
                in_memory_db, user_id="test_user2", role="user", content=f"消息{i}", platform="test"
            )

        session = in_memory_db.query(SessionModel).filter_by(user_id="test_user2").first()
        assert session.message_count == 3

    def test_create_and_resolve_escalation(self, in_memory_db):
        from src.services.db_service import create_escalation, resolve_escalation

        esc = create_escalation(
            in_memory_db,
            user_id="test_user3",
            trigger_message="我要投诉",
            ai_reply="人工客服会尽快处理",
            reason="complaint",
        )
        assert esc.status == "pending"

        resolved = resolve_escalation(in_memory_db, escalation_id=esc.id, operator_note="已处理")
        assert resolved.status == "resolved"
        assert resolved.resolved_at is not None

    def test_claim_escalation(self, in_memory_db):
        from src.services.db_service import claim_escalation, create_escalation

        esc = create_escalation(
            in_memory_db, user_id="test_user4", trigger_message="能便宜吗", ai_reply="已为您标记", reason="bargain"
        )
        claimed = claim_escalation(in_memory_db, escalation_id=esc.id, operator_name="客服小张")
        assert claimed.status == "claimed"
        assert claimed.claimed_at is not None
        assert claimed.operator_name == "客服小张"
