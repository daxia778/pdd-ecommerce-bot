"""
FastAPI 集成测试套件 - 使用 httpx.AsyncClient + dependency_overrides 注入测试 DB。

标准 FastAPI 测试模式：
  - app 不重新加载，直接引用真实 main.app
  - 通过 app.dependency_overrides[get_db] 注入隔离的测试 SQLite 数据库
  - lifespan 里的 create_tables() 对测试 DB 无效，但 conftest 里手动建表

覆盖：
  - 健康检查 /api/v1/health
  - 登录 /api/v1/login（成功/失败）
  - 聊天接口 /api/v1/chat
  - Dashboard 统计（带/不带 token）
  - Admin API 各接口
  - SessionManager 单元测试

运行：
    pytest tests/test_api.py -v
    pytest tests/ -v
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config.settings import settings
from main import app
from src.models.database import Base, get_db


@pytest.fixture(scope="module", autouse=True)
def wipe_admin_password_hash():
    """强制清除本地 .env 中的密码 hash 避免鉴权测试失败"""
    original = settings.admin_password_hash
    settings.admin_password_hash = ""
    yield
    settings.admin_password_hash = original


# =========================================================
# P1-4: LLM Mock — 避免测试消耗真实 Token / 触发限频
# =========================================================

STUB_LLM_REPLY = "您好！这是测试环境的AI模拟回复。"


@pytest.fixture(scope="module", autouse=True)
def mock_llm_globally():
    """
    模块级 LLM mock：在此测试文件执行期间拦截 LLMClient.chat，
    返回固定的 stub 回复而不调用真实 API。
    这样可以：
    1. 避免消耗 API Token
    2. 消除因网络或限频导致的测试不稳定
    3. 大幅加快测试执行速度
    """
    with patch(
        "src.core.llm_client.LLMClient.chat",
        new_callable=AsyncMock,
        return_value=STUB_LLM_REPLY,
    ):
        yield


# =========================================================
# 全局测试 DB — 在所有集成测试中共享
# =========================================================

TEST_DB_URL = "sqlite:///./data/sqlite/test_integration.db"

_test_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
)
Base.metadata.create_all(bind=_test_engine)

TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)


def override_get_db():
    """替换 get_db 依赖，注入测试专用数据库"""
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


# =========================================================
# Fixtures
# =========================================================


@pytest.fixture(scope="module", autouse=True)
def setup_dependency_override():
    """模块级：注入测试 DB，测试结束后清理 override"""
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def auth_client():
    """登录后携带 Bearer Token 的客户端"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/login", json={"username": "admin", "password": "admin888"})
        assert res.status_code == 200, f"登录失败: {res.text}"
        token = res.json()["access_token"]
        ac.headers.update({"Authorization": f"Bearer {token}"})
        yield ac


# =========================================================
# 1. 健康检查
# =========================================================


class TestHealth:
    async def test_health_ok(self, client):
        res = await client.get("/api/v1/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"
        assert "database" in data
        assert "llm_status" in data
        assert "knowledge_docs" in data

    async def test_api_root(self, client):
        res = await client.get("/api_root")
        assert res.status_code == 200
        data = res.json()
        assert data["version"] == "0.2.0"


# =========================================================
# 2. 鉴权
# =========================================================


class TestAuth:
    async def test_login_success(self, client):
        res = await client.post("/api/v1/login", json={"username": "admin", "password": "admin888"})
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client):
        res = await client.post("/api/v1/login", json={"username": "admin", "password": "wrongpassword"})
        assert res.status_code == 401

    async def test_login_wrong_username(self, client):
        res = await client.post("/api/v1/login", json={"username": "hacker", "password": "admin888"})
        assert res.status_code == 401


# =========================================================
# 3. 聊天接口
# =========================================================


class TestChatEndpoint:
    async def test_chat_basic(self, client):
        res = await client.post(
            "/api/v1/chat",
            json={"user_id": "test_integration_user", "message": "你好，PPT多少钱？", "platform": "test"},
        )
        assert res.status_code == 200
        data = res.json()
        assert "reply" in data
        assert len(data["reply"]) > 0
        assert "history_length" in data
        assert "escalated" in data

    async def test_chat_clear_history(self, client):
        res = await client.post(
            "/api/v1/chat",
            json={"user_id": "test_clear_user", "message": "清空", "platform": "test", "clear_history": True},
        )
        assert res.status_code == 200

    async def test_chat_escalation_flag_present(self, client):
        """escalated 字段必须始终存在"""
        res = await client.post(
            "/api/v1/chat", json={"user_id": "test_esc_user", "message": "请问你们的价格是多少", "platform": "test"}
        )
        assert res.status_code == 200
        assert "escalated" in res.json()


# =========================================================
# 4. Dashboard（需要 Bearer）
# =========================================================


class TestDashboard:
    async def test_stats_requires_auth(self, client):
        res = await client.get("/api/dashboard/stats")
        assert res.status_code == 401

    async def test_stats_with_auth(self, auth_client):
        res = await auth_client.get("/api/dashboard/stats")
        assert res.status_code == 200
        data = res.json()
        assert "active_sessions" in data
        assert "pending_escalations" in data

    async def test_sessions_with_auth(self, auth_client):
        res = await auth_client.get("/api/dashboard/sessions")
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    async def test_escalations_with_auth(self, auth_client):
        res = await auth_client.get("/api/dashboard/escalations")
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    async def test_orders_with_auth(self, auth_client):
        res = await auth_client.get("/api/dashboard/orders")
        assert res.status_code == 200
        assert isinstance(res.json(), list)


# =========================================================
# 5. Admin API
# =========================================================


class TestAdminAPI:
    async def test_admin_stats(self, auth_client):
        res = await auth_client.get("/admin/api/admin/stats")
        assert res.status_code == 200

    async def test_admin_sessions(self, auth_client):
        res = await auth_client.get("/admin/api/admin/sessions")
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    async def test_admin_escalations_all(self, auth_client):
        res = await auth_client.get("/admin/api/admin/escalations")
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    async def test_admin_escalations_filter_pending(self, auth_client):
        res = await auth_client.get("/admin/api/admin/escalations?status=pending")
        assert res.status_code == 200

    async def test_admin_knowledge_list(self, auth_client):
        res = await auth_client.get("/admin/api/admin/knowledge")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert "data" in data


# =========================================================
# 6. SessionManager 单元测试（不依赖 HTTP）
# =========================================================


class TestSessionManager:
    def setup_method(self):
        from src.core.session_manager import SessionManager

        self.sm = SessionManager(max_history=5)

    def test_add_and_get_history(self):
        self.sm.add_message_sync("user_a", "user", "你好")
        self.sm.add_message_sync("user_a", "assistant", "您好！")
        history = self.sm.get_history("user_a")
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"

    def test_max_history_truncation(self):
        for i in range(8):
            self.sm.add_message_sync("user_b", "user", f"消息{i}")
        history = self.sm.get_history("user_b")
        assert len(history) == 5

    def test_clear_session(self):
        self.sm.add_message_sync("user_c", "user", "你好")
        self.sm.clear_session("user_c")
        assert self.sm.get_history("user_c") == []

    def test_ai_pause_state(self):
        assert self.sm.is_ai_paused("user_d") is False
        self.sm.set_ai_paused("user_d", True)
        assert self.sm.is_ai_paused("user_d") is True
        self.sm.set_ai_paused("user_d", False)
        assert self.sm.is_ai_paused("user_d") is False

    def test_user_count(self):
        from src.core.session_manager import SessionManager

        sm2 = SessionManager(max_history=5)
        sm2.add_message_sync("ua", "user", "hi")
        sm2.add_message_sync("ub", "user", "hi")
        assert sm2.get_user_count() == 2
