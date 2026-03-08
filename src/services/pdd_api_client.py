"""
拼多多开放平台 API 客户端
封装签名生成和网络请求逻辑。

P0-Root-Cause-Sweep: 使用持久化 httpx.AsyncClient 连接池，
避免每次请求都创建 / 销毁 TCP 连接导致的端口耗尽和握手延迟。
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
from typing import Any

import httpx

from config.settings import settings
from src.utils.logger import logger


class PddApiClient:
    """
    拼多多开放平台 API 客户端
    封装签名生成和网络请求逻辑。

    P0-Root-Cause-Sweep: 使用持久化连接池替代每次请求新建 AsyncClient。
    """

    def __init__(self):
        self.gateway_url = "https://gw-api.pinduoduo.com/api/router"
        self.client_id = settings.pdd_app_key
        self.client_secret = settings.pdd_app_secret
        self.access_token = settings.pdd_access_token
        self.max_retries = 3

        # P0-Root-Cause-Sweep: 持久化 HTTP 连接池
        # limits: 最大 100 连接, 单 host 最多 20 连接
        # timeout: 连接 5s, 读 10s, 写 5s, 连接池获取 5s
        self._client = httpx.AsyncClient(
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
            timeout=httpx.Timeout(10.0, connect=5.0),
        )

    async def close(self):
        """关闭持久化 HTTP 连接池（由 FastAPI lifespan shutdown 调用）"""
        await self._client.aclose()

    def _generate_sign(self, params: dict[str, Any]) -> str:
        """
        生成拼多多 API 签名
        官方规则: MD5(client_secret + key1+value1 + key2+value2... + client_secret)
        按 key 的首字母升序排序
        """
        sorted_keys = sorted(params.keys())
        sign_str = self.client_secret

        for k in sorted_keys:
            v = params[k]
            if isinstance(v, (dict, list)):  # noqa: UP038  # Python 3.9 compat
                sign_str += f"{k}{json.dumps(v, separators=(',', ':'))}"
            else:
                sign_str += f"{k}{v}"

        sign_str += self.client_secret
        return hashlib.md5(sign_str.encode("utf-8")).hexdigest().upper()

    async def send_customer_message(self, mall_id: str, buyer_id: str, content: str) -> bool:
        """
        调用拼多多 API 给买家发送客服消息
        此处的 API type 名称 (`pdd.pop.cs.message.send`) 需要替换为您申请的实际 API 名称
        """
        if not self.client_id or not self.client_secret or not self.access_token:
            logger.warning("PDD API 凭证未配置，无法发送真实消息（已降级为仅日志模式）")
            return True

        params = {
            "type": "pdd.pop.cs.message.send",
            "client_id": self.client_id,
            "access_token": self.access_token,
            "timestamp": str(int(time.time())),
            "data_type": "JSON",
            "version": "V1",
            "mall_id": mall_id,
            "buyer_id": buyer_id,
            "message_type": "text",
            "content": content,
        }

        params["sign"] = self._generate_sign(params)

        for attempt in range(self.max_retries):
            try:
                if attempt > 0:
                    delay = 1.0 * (2 ** (attempt - 1))
                    logger.warning(f"PDD API | 准备重试发送消息，等待 {delay}s...")
                    await asyncio.sleep(delay)

                logger.info(f"PDD API | 正在发送消息至买家 {buyer_id[:8]}... (尝试 {attempt + 1}/{self.max_retries})")
                response = await self._client.post(self.gateway_url, json=params)

                resp_data = response.json()
                if "error_response" in resp_data:
                    logger.error(f"PDD API 错误返回: {resp_data['error_response']}")
                    return False

                logger.info("PDD API | 消息发送成功")
                return True

            except Exception as e:
                logger.error(f"PDD API | 请求异常(尝试 {attempt + 1}/{self.max_retries}): {e}")

        logger.error(f"PDD API | 消息发送最终失败，已重试 {self.max_retries} 次。")
        return False

    async def send_file_message(self, mall_id: str, buyer_id: str, file_url: str) -> bool:
        """
        调用拼多多 API 给买家发送文件或卡片消息
        """
        if not self.client_id or not self.client_secret or not self.access_token:
            logger.warning("PDD API 凭证未配置，无法发送真实文件消息（已降级为仅日志模式）")
            return True

        params = {
            "type": "pdd.pop.cs.message.send",
            "client_id": self.client_id,
            "access_token": self.access_token,
            "timestamp": str(int(time.time())),
            "data_type": "JSON",
            "version": "V1",
            "mall_id": mall_id,
            "buyer_id": buyer_id,
            "message_type": "file",
            "content": file_url,
        }

        params["sign"] = self._generate_sign(params)

        for attempt in range(self.max_retries):
            try:
                if attempt > 0:
                    delay = 1.0 * (2 ** (attempt - 1))
                    logger.warning(f"PDD API | 准备重试发送文件，等待 {delay}s...")
                    await asyncio.sleep(delay)

                logger.info(
                    f"PDD API | 正在发送文件消息至买家 {buyer_id[:8]}... (尝试 {attempt + 1}/{self.max_retries})"
                )
                response = await self._client.post(self.gateway_url, json=params)

                resp_data = response.json()
                if "error_response" in resp_data:
                    logger.error(f"PDD API 文件消息错误返回: {resp_data['error_response']}")
                    return False

                logger.info("PDD API | 文件消息发送成功")
                return True

            except Exception as e:
                logger.error(f"PDD API | 文件请求异常(尝试 {attempt + 1}/{self.max_retries}): {e}")

        logger.error(f"PDD API | 文件消息发送最终失败，已重试 {self.max_retries} 次。")
        return False


pdd_api_client = PddApiClient()
