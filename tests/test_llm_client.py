"""
LLM 客户端单元测试 — 测试 Failover 和重试逻辑。

使用 mock 替代真实 API 调用，验证:
  - 正常调用流程
  - 多 Key 轮询
  - Failover 降级
  - 全部失败时抛出 RuntimeError
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestLLMClientInit:
    """测试 LLM 客户端初始化"""

    def test_no_keys_raises_error(self):
        """没有任何 API Key 应抛出 ValueError"""
        with patch("src.core.llm_client.settings") as mock_settings:
            mock_settings.zhipu_key_list = []
            mock_settings.deepseek_key_list = []
            mock_settings.gemini_key_list = []
            mock_settings.https_proxy = ""

            from src.core.llm_client import LLMClient

            with pytest.raises(ValueError, match="未配置任何"):
                LLMClient()

    def test_single_provider_init(self):
        """单个厂商多 Key 应正常初始化"""
        with patch("src.core.llm_client.settings") as mock_settings:
            mock_settings.zhipu_key_list = ["key1", "key2"]
            mock_settings.deepseek_key_list = []
            mock_settings.gemini_key_list = []
            mock_settings.https_proxy = ""

            from src.core.llm_client import LLMClient

            client = LLMClient()
            assert len(client._providers_pool) == 1
            assert client._providers_pool[0]["name"] == "zhipu"

    def test_multi_provider_priority(self):
        """多厂商应按 Zhipu > DeepSeek > Gemini 优先级排列"""
        with patch("src.core.llm_client.settings") as mock_settings:
            mock_settings.zhipu_key_list = ["zk1"]
            mock_settings.deepseek_key_list = ["dk1"]
            mock_settings.gemini_key_list = ["gk1"]
            mock_settings.https_proxy = ""

            from src.core.llm_client import LLMClient

            client = LLMClient()
            names = [p["name"] for p in client._providers_pool]
            assert names == ["zhipu", "deepseek", "gemini"]


class TestLLMClientChat:
    """测试 LLM 聊天调用逻辑"""

    @pytest.fixture
    def mock_client(self):
        """创建已初始化的 mock LLM 客户端"""
        with patch("src.core.llm_client.settings") as mock_settings:
            mock_settings.zhipu_key_list = ["key1", "key2"]
            mock_settings.deepseek_key_list = ["dk1"]
            mock_settings.gemini_key_list = []
            mock_settings.https_proxy = ""
            mock_settings.max_retries = 2

            from src.core.llm_client import LLMClient

            client = LLMClient()
            return client

    @pytest.mark.asyncio
    async def test_successful_chat(self, mock_client):
        """正常调用应返回 AI 回复文本（流式模式）"""

        # P4-Stream: mock 流式响应 — acompletion 返回 AsyncIterator[chunk]
        async def mock_stream(*args, **kwargs):
            """模拟流式 chunk 迭代器"""
            for text in ["测试", "回复"]:
                chunk = MagicMock()
                chunk.choices = [MagicMock()]
                chunk.choices[0].delta = MagicMock()
                chunk.choices[0].delta.content = text
                yield chunk

        with patch("src.core.llm_client.acompletion", return_value=mock_stream()):
            reply = await mock_client.chat(
                messages=[{"role": "user", "content": "你好"}],
            )
            assert reply == "测试回复"

    @pytest.mark.asyncio
    async def test_all_keys_fail_raises_error(self, mock_client):
        """所有 Key 都失败应抛出 RuntimeError"""
        with (
            patch(
                "src.core.llm_client.acompletion",
                new_callable=AsyncMock,
                side_effect=Exception("API Error"),
            ),
            pytest.raises(RuntimeError, match="全部失败"),
        ):
            await mock_client.chat(
                messages=[{"role": "user", "content": "你好"}],
            )

    @pytest.mark.asyncio
    async def test_system_prompt_prepended(self, mock_client):
        """system_prompt 应作为第一条消息插入"""

        # P4-Stream: mock 流式响应
        async def mock_stream(*args, **kwargs):
            chunk = MagicMock()
            chunk.choices = [MagicMock()]
            chunk.choices[0].delta = MagicMock()
            chunk.choices[0].delta.content = "OK"
            yield chunk

        with patch("src.core.llm_client.acompletion", return_value=mock_stream()) as mock_call:
            await mock_client.chat(
                messages=[{"role": "user", "content": "Hi"}],
                system_prompt="你是客服",
            )
            # 验证传入 acompletion 的 messages 列表第一条是 system
            call_args = mock_call.call_args
            msgs = call_args.kwargs.get("messages") or call_args[1].get("messages")
            assert msgs[0]["role"] == "system"
            assert msgs[0]["content"] == "你是客服"
