"""
LLM 客户端 - 封装 ZhipuAI (via LiteLLM) 的调用逻辑。
支持多 API Key Round-Robin 轮询，内置指数退避重试和响应时间追踪。

P0-1修复: 每次失败自动切换到下一个 Key，而非重试同一个 Key
P1-1增强: 记录每次调用的响应时间（ms）到日志
"""
import asyncio
import itertools
import os
import time
from typing import List, Optional
import litellm
from litellm import acompletion

from config.settings import settings
from src.utils.logger import logger

# 关闭 LiteLLM 的详细日志（生产环境）
litellm.set_verbose = False

# ZhipuAI 的 OpenAI 兼容接口地址
ZHIPU_BASE_URL = "https://open.bigmodel.cn/api/paas/v4/"

# 指数退避基础等待时间（秒）
_RETRY_BASE_DELAY = 1.0


class LLMClient:
    """
    多 Key Round-Robin LLM 客户端。
    - 每次请求自动选择下一个 API Key（轮询）
    - P0-1: API Key 失败时切换到下一个 Key，不重试同一个 Key
    - P0-1: 指数退避等待（1s, 2s, 4s...），避免立即重打 LLM 接口
    - P1-1: 记录每次调用耗时（ms）
    """

    def __init__(self):
        self._keys: List[str] = settings.zhipu_key_list
        if not self._keys:
            raise ValueError("未配置 ZHIPU_API_KEYS，请检查 .env 文件")

        # 无限循环迭代器，实现 Round-Robin
        self._key_cycle = itertools.cycle(self._keys)
        self._model = settings.main_chat_model
        logger.info(f"LLMClient 初始化完成 | 模型: {self._model} | Key 数量: {len(self._keys)}")

        # 如果配置了代理，设置环境变量
        if settings.https_proxy:
            os.environ["HTTPS_PROXY"] = settings.https_proxy
            logger.info(f"使用代理: {settings.https_proxy}")

    def _next_key(self) -> str:
        """获取下一个 API Key（Round-Robin）"""
        return next(self._key_cycle)

    async def chat(
        self,
        messages: List[dict],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str:
        """
        发送对话请求并返回 AI 回复文本。

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

        last_error = None
        max_attempts = max(settings.max_retries, len(self._keys))

        for attempt in range(max_attempts):
            # P0-1: 每次失败都切换到下一个 Key，不重用失败的 Key
            api_key = self._next_key()

            # P0-1: 指数退避（从第2次尝试开始等待）
            if attempt > 0:
                delay = _RETRY_BASE_DELAY * (2 ** (attempt - 1))
                delay = min(delay, 16.0)  # 最大等待 16 秒
                logger.warning(f"LLM 退避等待 {delay:.1f}s 后重试 | 尝试 {attempt + 1}/{max_attempts}")
                await asyncio.sleep(delay)

            try:
                logger.debug(f"LLM 调用 | 尝试 {attempt + 1}/{max_attempts} | Key: ...{api_key[-8:]}")

                # P1-1: 记录响应时间
                t_start = time.monotonic()

                response = await acompletion(
                    model=f"openai/{self._model}",   # openai 兼容格式
                    messages=full_messages,
                    api_key=api_key,
                    base_url=ZHIPU_BASE_URL,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=30,
                )

                elapsed_ms = int((time.monotonic() - t_start) * 1000)
                reply = response.choices[0].message.content
                usage = response.usage
                logger.info(
                    f"LLM 成功 | 模型: {self._model} | "
                    f"耗时: {elapsed_ms}ms | "
                    f"Input: {usage.prompt_tokens} | "
                    f"Output: {usage.completion_tokens} tokens"
                )
                return reply

            except Exception as e:
                last_error = e
                logger.warning(
                    f"LLM 调用失败 (尝试 {attempt + 1}/{max_attempts}) "
                    f"Key: ...{api_key[-8:]} | {type(e).__name__}: {e}"
                )

        raise RuntimeError(f"LLM 调用在 {max_attempts} 次重试（多 Key）后全部失败: {last_error}")


# 全局单例（懒加载）
_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """获取全局 LLM 客户端单例"""
    global _client
    if _client is None:
        _client = LLMClient()
    return _client
