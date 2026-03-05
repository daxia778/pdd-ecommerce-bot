"""
LLM 客户端 - 封装 ZhipuAI (via LiteLLM) 的调用逻辑。
支持多 API Key Round-Robin 轮询，内置重试和超时控制。
"""
import itertools
import os
from typing import List, Optional
import litellm
from litellm import acompletion

from config.settings import settings
from src.utils.logger import logger

# 关闭 LiteLLM 的详细日志（生产环境）
litellm.set_verbose = False

# ZhipuAI 的 OpenAI 兼容接口地址
ZHIPU_BASE_URL = "https://open.bigmodel.cn/api/paas/v4/"


class LLMClient:
    """
    多 Key Round-Robin LLM 客户端。
    - 每次请求自动选择下一个 API Key（轮询）
    - API Key 失败时自动重试下一个
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
        """
        # 组装完整消息列表
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        last_error = None
        # 最多尝试所有 Key 各一次，再 + max_retries 次
        for attempt in range(settings.max_retries):
            api_key = self._next_key()
            try:
                logger.debug(f"LLM 调用 | 尝试 {attempt + 1}/{settings.max_retries} | Key: ...{api_key[-8:]}")

                response = await acompletion(
                    model=f"openai/{self._model}",   # 使用 openai 兼容格式
                    messages=full_messages,
                    api_key=api_key,
                    base_url=ZHIPU_BASE_URL,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=30,
                )

                reply = response.choices[0].message.content
                usage = response.usage
                logger.info(
                    f"LLM 成功 | 模型: {self._model} | "
                    f"Input: {usage.prompt_tokens} tokens | "
                    f"Output: {usage.completion_tokens} tokens"
                )
                return reply

            except Exception as e:
                last_error = e
                logger.warning(f"LLM 调用失败 (尝试 {attempt + 1}): {type(e).__name__}: {e}")
                if attempt < settings.max_retries - 1:
                    continue

        raise RuntimeError(f"LLM 调用在 {settings.max_retries} 次重试后失败: {last_error}")


# 全局单例（懒加载）
_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """获取全局 LLM 客户端单例"""
    global _client
    if _client is None:
        _client = LLMClient()
    return _client
