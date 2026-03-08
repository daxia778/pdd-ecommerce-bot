"""
LLM 客户端 - 封装 ZhipuAI (via LiteLLM) 的调用逻辑。
支持多 API Key Round-Robin 轮询，内置指数退避重试和响应时间追踪。

P0-1修复: 每次失败自动切换到下一个 Key，而非重试同一个 Key
P1-1增强: 记录每次调用的响应时间（ms）到日志
"""

from __future__ import annotations

import asyncio
import itertools
import os
import time

import litellm
from litellm import acompletion

from config.settings import settings
from src.utils.logger import logger

# 关闭 LiteLLM 的详细日志（生产环境）
litellm.set_verbose = False

# ZhipuAI / DeepSeek / Gemini 的 OpenAI 兼容接口地址
# 重试基础延迟（秒），每次失败后指数退避: delay = BASE * 2^(attempt-1)
_RETRY_BASE_DELAY = 1.0

PROVIDERS = {
    "zhipu": {"base_url": "https://open.bigmodel.cn/api/paas/v4/", "model": "openai/glm-4-flash"},
    "deepseek": {"base_url": "https://api.deepseek.com/v1", "model": "openai/deepseek-chat"},
    "gemini": {
        "base_url": None,  # LiteLLM 会自动处理 Gemini 的 base URL
        "model": "gemini/gemini-pro",
    },
}


class LLMClient:
    """
    多 Provider 多 Key Failover LLM 客户端。
    - 优先尝试 Zhipu (配置的多个 Key 轮次)
    - P2: 如果 Zhipu 全军覆没则退避降级到 DeepSeek -> Gemini
    - 记录每次调用耗时
    """

    def __init__(self):
        # 按优先级组装可用资源池
        self._providers_pool = []

        if settings.zhipu_key_list:
            self._providers_pool.append(
                {
                    "name": "zhipu",
                    "keys": settings.zhipu_key_list,
                    "cycle": itertools.cycle(settings.zhipu_key_list),
                    "banned": set(),
                }
            )

        if settings.deepseek_key_list:
            self._providers_pool.append(
                {
                    "name": "deepseek",
                    "keys": settings.deepseek_key_list,
                    "cycle": itertools.cycle(settings.deepseek_key_list),
                    "banned": set(),
                }
            )

        if settings.gemini_key_list:
            self._providers_pool.append(
                {
                    "name": "gemini",
                    "keys": settings.gemini_key_list,
                    "cycle": itertools.cycle(settings.gemini_key_list),
                    "banned": set(),
                }
            )

        if not self._providers_pool:
            raise ValueError("未配置任何完整的 LLM API KEYS (Zhipu/DeepSeek/Gemini均为空)")

        logger.info(f"LLMClient(Failover模式) 初始化 | 提供商优先级: {[p['name'] for p in self._providers_pool]}")

        # 如果配置了代理，设置环境变量
        if settings.https_proxy:
            os.environ["HTTPS_PROXY"] = settings.https_proxy
            logger.info(f"使用代理: {settings.https_proxy}")

    def _next_key_for_provider(self, provider: dict) -> str | None:
        """为特定 provider 获取下一个可用的 API Key"""
        if len(provider["banned"]) >= len(provider["keys"]):
            return None  # 该厂商所有 Key 已被封杀

        for _ in range(len(provider["keys"])):
            key = next(provider["cycle"])
            if key not in provider["banned"]:
                return key
        return None

    # ── P1-Root-Cause-Sweep: Token 安全截断 ─────────────────
    # 模型上下文安全预算（预留 max_tokens 给输出 + 500 buffer 给 metadata）
    _MODEL_CONTEXT_LIMIT = 8192  # GLM-4-Flash / DeepSeek-Chat 的公共安全值

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """
        粗略估算文本 Token 数量。

        由于 tiktoken 不支持 ZhipuAI/DeepSeek 的 tokenizer，
        这里使用经验公式：
        - 中文/日韩字符: 每字 ≈ 1.5 tokens
        - 英文/数字: 每 word ≈ 1.3 tokens
        实测误差在 ±15% 以内，对于安全截断场景足够。
        """
        cjk_count = sum(1 for c in text if "\u4e00" <= c <= "\u9fff" or "\u3000" <= c <= "\u303f")
        ascii_words = len(text.encode("ascii", errors="ignore").split())
        return int(cjk_count * 1.5 + ascii_words * 1.3 + 10)  # +10 for message metadata

    def _truncate_messages_to_fit(self, messages: list[dict], max_output_tokens: int) -> list[dict]:
        """
        确保 messages 总 Token 数不会超出模型的上下文窗口。

        策略：
        1. 保留 system prompt（第一条消息，如有）
        2. 保留最近的对话消息
        3. 丢弃最早的历史消息（FIFO）
        4. 如果单条消息过长，截断其 content
        """
        budget = self._MODEL_CONTEXT_LIMIT - max_output_tokens - 500  # 预留输出 + metadata
        if budget <= 0:
            budget = 2048  # 极端情况下的最低保障

        # 分离 system 和 conversation 消息
        system_msgs = [m for m in messages if m.get("role") == "system"]
        conv_msgs = [m for m in messages if m.get("role") != "system"]

        # 计算 system prompt 消耗
        system_cost = sum(self._estimate_tokens(str(m.get("content", ""))) for m in system_msgs)
        remaining = budget - system_cost

        if remaining <= 0:
            # system prompt 本身就超了，截断 system prompt
            for m in system_msgs:
                content = str(m.get("content", ""))
                if len(content) > 3000:
                    m["content"] = content[:3000] + "\n...[系统提示已截断]"
            remaining = 1024  # 保留一点空间给对话

        # 从最新消息开始向前累积，直到用完预算
        kept = []
        for msg in reversed(conv_msgs):
            content = str(msg.get("content", ""))
            cost = self._estimate_tokens(content)

            if cost > remaining:
                # 单条消息过长 — 截断
                if remaining > 200:
                    # 保留部分内容
                    ratio = remaining / max(cost, 1)
                    keep_chars = max(int(len(content) * ratio * 0.8), 100)
                    msg = {**msg, "content": content[:keep_chars] + "\n...[消息已截断]"}
                    kept.append(msg)
                break

            kept.append(msg)
            remaining -= cost
            if remaining <= 0:
                break

        kept.reverse()

        truncated_count = len(conv_msgs) - len(kept)
        if truncated_count > 0:
            logger.info(
                f"Token安全截断 | 原始: {len(conv_msgs)} 条 → 保留: {len(kept)} 条 | 丢弃最早 {truncated_count} 条历史"
            )

        return system_msgs + kept

    async def chat(
        self,
        messages: list[dict],
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str:
        """
        发送对话请求并返回 AI 回复文本。

        P1-Root-Cause-Sweep: 新增 Token 安全截断，防止 payload 超出模型上下文导致 API 报错。

        Args:
            messages: 对话历史，格式 [{"role": "user", "content": "..."}]
            system_prompt: 系统提示词（可选）
            temperature: 生成温度
            max_tokens: 最大 Token 数

        Returns:
            AI 回复的文本内容

        Raises:
            RuntimeError: 所有重试均失败后抛出
        """
        # 组装完整消息列表
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        # P1-Root-Cause-Sweep: Token 安全截断
        full_messages = self._truncate_messages_to_fit(full_messages, max_tokens)

        last_error = None

        for p_idx, provider in enumerate(self._providers_pool):
            p_name = provider["name"]
            p_config = PROVIDERS[p_name]
            # 每个厂商最多重试的次数 (配置指定的重试次数 or 该厂商的 Key 数量)
            max_attempts = max(settings.max_retries, len(provider["keys"]))

            for attempt in range(max_attempts):
                api_key = self._next_key_for_provider(provider)
                if not api_key:
                    logger.warning(f"厂商 [{p_name}] 的所有 API Key 已耗尽/被封禁，准备降级到下一厂商")
                    break  # 跳出内层循环，直接进入下一个 provider

                if attempt > 0:
                    delay = _RETRY_BASE_DELAY * (2 ** (attempt - 1))
                    delay = min(delay, 16.0)
                    logger.warning(
                        f"LLM 退避等待 {delay:.1f}s 后重试 | 厂商 {p_name} | 尝试 {attempt + 1}/{max_attempts}"
                    )
                    await asyncio.sleep(delay)

                try:
                    logger.debug(
                        f"LLM 调用 | 厂商 {p_name} | 尝试 {attempt + 1}/{max_attempts} | Key: ...{api_key[-8:]}"
                    )
                    t_start = time.monotonic()

                    # LiteLLM 对不同厂商传参
                    response = await acompletion(
                        model=p_config["model"],
                        messages=full_messages,
                        api_key=api_key,
                        base_url=p_config["base_url"],
                        temperature=temperature,
                        max_tokens=max_tokens,
                        timeout=30,
                    )

                    elapsed_ms = int((time.monotonic() - t_start) * 1000)
                    reply = response.choices[0].message.content
                    logger.info(
                        f"LLM 成功 ({'Failover兜底' if p_idx > 0 else '默认'}) | 厂商: {p_name} | "
                        f"模型: {p_config['model']} | 耗时: {elapsed_ms}ms"
                    )
                    return reply

                except litellm.AuthenticationError as e:
                    last_error = e
                    logger.error(f"LLM 鉴权失败，剔除厂商 [{p_name}] 的 Key: ...{api_key[-8:]} | {e}")
                    provider["banned"].add(api_key)
                except Exception as e:
                    last_error = e
                    logger.warning(f"LLM 调用失败 | 厂商: {p_name} | Key: ...{api_key[-8:]} | {type(e).__name__}: {e}")

        # 如果所有 provider 循环都结束且没有返回
        raise RuntimeError(f"致命错误：LLM 调用在所有可用后端厂商的重试后全部失败。最后一个错误: {last_error}")


# 全局单例（懒加载）
_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    """获取全局 LLM 客户端单例"""
    global _client
    if _client is None:
        _client = LLMClient()
    return _client
