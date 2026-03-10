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

    async def send_image_message(self, mall_id: str, buyer_id: str, image_url: str) -> bool:
        """
        调用拼多多 API 给买家发送图片消息。
        message_type 必须设为 "image"，content 填图片 URL。

        注意：拼多多要求图片 URL 必须是公网可访问的，
        或者是通过 pdd.goods.img.upload 上传后获得的 URL。
        """
        if not self.client_id or not self.client_secret or not self.access_token:
            logger.warning("PDD API 凭证未配置，无法发送真实图片消息（已降级为仅日志模式）")
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
            "message_type": "image",
            "content": image_url,
        }

        params["sign"] = self._generate_sign(params)

        for attempt in range(self.max_retries):
            try:
                if attempt > 0:
                    delay = 1.0 * (2 ** (attempt - 1))
                    logger.warning(f"PDD API | 准备重试发送图片，等待 {delay}s...")
                    await asyncio.sleep(delay)

                logger.info(
                    f"PDD API | 正在发送图片消息至买家 {buyer_id[:8]}... (尝试 {attempt + 1}/{self.max_retries})"
                )
                response = await self._client.post(self.gateway_url, json=params)

                resp_data = response.json()
                if "error_response" in resp_data:
                    logger.error(f"PDD API 图片消息错误返回: {resp_data['error_response']}")
                    # 降级尝试：如果 image 类型不支持，尝试 file 类型
                    if attempt == self.max_retries - 1:
                        logger.warning("PDD API | 图片消息失败，降级尝试 file 类型...")
                        return await self.send_file_message(mall_id, buyer_id, image_url)
                    continue

                logger.info("PDD API | 图片消息发送成功")
                return True

            except Exception as e:
                logger.error(f"PDD API | 图片请求异常(尝试 {attempt + 1}/{self.max_retries}): {e}")

        logger.error(f"PDD API | 图片消息发送最终失败，已重试 {self.max_retries} 次。")
        return False

    async def send_file_message(self, mall_id: str, buyer_id: str, file_url: str) -> bool:
        """
        调用拼多多 API 给买家发送文件或卡片消息。
        自动检测：如果是图片类型 URL，优先走 image 通道。
        """
        # 自动检测图片类型，优先用 image 消息类型
        if any(file_url.lower().endswith(ext) for ext in (".png", ".jpg", ".jpeg", ".gif", ".webp")):
            logger.info(f"PDD API | 检测到图片文件，优先使用 image 消息类型 | url: {file_url[-30:]}")
            return await self.send_image_message(mall_id, buyer_id, file_url)

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

    # ==========================================================================
    # PDD 平台订单查询（只读）—— 预留接口，接入后需实际测试
    # 文档参考: https://open.pinduoduo.com/application/document/api?id=pdd.order.list.get
    # ==========================================================================

    async def get_order_list(
        self,
        *,
        order_status: int | None = None,
        start_confirm_at: int | None = None,
        end_confirm_at: int | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """
        查询店铺订单列表（只读）。

        Args:
            order_status: 订单状态筛选
                1=待付款, 2=待发货, 3=已发货, 5=已完成, 6=已关闭
            start_confirm_at: 订单确认时间起始（Unix 秒级时间戳）
            end_confirm_at: 订单确认时间结束（Unix 秒级时间戳）
            page: 页码，从1开始
            page_size: 每页条数，最大100

        Returns:
            {"success": bool, "total_count": int, "orders": list[dict], "error": str|None}
        """
        if not self.client_id or not self.client_secret or not self.access_token:
            logger.warning("PDD API 凭证未配置，无法查询订单（返回模拟空数据）")
            return {"success": False, "total_count": 0, "orders": [], "error": "PDD 凭证未配置"}

        params: dict[str, Any] = {
            "type": "pdd.order.list.get",
            "client_id": self.client_id,
            "access_token": self.access_token,
            "timestamp": str(int(time.time())),
            "data_type": "JSON",
            "version": "V1",
            "page": str(page),
            "page_size": str(min(page_size, 100)),
        }
        if order_status is not None:
            params["order_status"] = str(order_status)
        if start_confirm_at is not None:
            params["start_confirm_at"] = str(start_confirm_at)
        if end_confirm_at is not None:
            params["end_confirm_at"] = str(end_confirm_at)

        params["sign"] = self._generate_sign(params)

        try:
            response = await self._client.post(self.gateway_url, json=params)
            resp_data = response.json()

            if "error_response" in resp_data:
                err = resp_data["error_response"]
                logger.error(f"PDD 订单查询错误: {err}")
                return {"success": False, "total_count": 0, "orders": [], "error": str(err)}

            result = resp_data.get("order_list_get_response", {})
            orders = result.get("order_list", [])
            total = result.get("total_count", len(orders))
            logger.info(f"PDD 订单查询成功 | 共 {total} 条 | 本页 {len(orders)} 条")
            return {"success": True, "total_count": total, "orders": orders, "error": None}

        except Exception as e:
            logger.error(f"PDD 订单查询异常: {e}")
            return {"success": False, "total_count": 0, "orders": [], "error": str(e)}

    async def get_order_detail(self, order_sn: str) -> dict:
        """
        根据订单号查询单个订单详情（只读）。

        Args:
            order_sn: 拼多多平台订单号

        Returns:
            {"success": bool, "order": dict|None, "error": str|None}
        """
        if not self.client_id or not self.client_secret or not self.access_token:
            logger.warning("PDD API 凭证未配置，无法查询订单详情")
            return {"success": False, "order": None, "error": "PDD 凭证未配置"}

        params: dict[str, Any] = {
            "type": "pdd.order.information.get",
            "client_id": self.client_id,
            "access_token": self.access_token,
            "timestamp": str(int(time.time())),
            "data_type": "JSON",
            "version": "V1",
            "order_sn": order_sn,
        }
        params["sign"] = self._generate_sign(params)

        try:
            response = await self._client.post(self.gateway_url, json=params)
            resp_data = response.json()

            if "error_response" in resp_data:
                err = resp_data["error_response"]
                logger.error(f"PDD 订单详情查询错误: {err}")
                return {"success": False, "order": None, "error": str(err)}

            order_info = resp_data.get("order_information_get_response", {}).get("order_info", None)
            if order_info:
                logger.info(f"PDD 订单详情查询成功 | order_sn: {order_sn}")
            return {"success": True, "order": order_info, "error": None}

        except Exception as e:
            logger.error(f"PDD 订单详情查询异常: {e}")
            return {"success": False, "order": None, "error": str(e)}

    async def get_order_status(self, order_sn: str) -> dict:
        """
        快速查询订单状态（只读，精简版）。
        比 get_order_detail 更轻量，仅返回状态和金额。

        Returns:
            {"success": bool, "order_sn": str, "status": int|None,
             "status_label": str, "pay_amount": float|None, "error": str|None}
        """
        STATUS_LABELS = {
            1: "待付款",
            2: "待发货",
            3: "已发货",
            5: "已完成",
            6: "已关闭",
        }

        detail = await self.get_order_detail(order_sn)
        if not detail["success"] or not detail["order"]:
            return {
                "success": False,
                "order_sn": order_sn,
                "status": None,
                "status_label": "查询失败",
                "pay_amount": None,
                "error": detail.get("error"),
            }

        order = detail["order"]
        status_code = order.get("order_status")
        pay_amount = order.get("pay_amount")  # 单位: 分
        return {
            "success": True,
            "order_sn": order_sn,
            "status": status_code,
            "status_label": STATUS_LABELS.get(status_code, f"未知({status_code})"),
            "pay_amount": pay_amount / 100.0 if pay_amount else None,  # 转为元
            "error": None,
        }


pdd_api_client = PddApiClient()
