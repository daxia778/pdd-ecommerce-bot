"""
企业微信 API 客户端 — 对接后续工作流。

功能预留：
1. 添加外部联系人（通过微信二维码）
2. 创建群聊（拉设计师 + 顾客）
3. 发送消息（分享需求到群内）
4. 接收回调事件

当前状态：接口预留，等企业微信应用审核通过后填入凭证即可启用。
"""

from __future__ import annotations

import httpx

from config.settings import settings
from src.utils.logger import logger


class WeComClient:
    """
    企业微信 API 客户端。
    文档参考: https://developer.work.weixin.qq.com/document/path/90664
    """

    def __init__(self):
        self.corp_id = settings.wecom_corp_id
        self.corp_secret = settings.wecom_corp_secret
        self.agent_id = settings.wecom_agent_id
        self.base_url = "https://qyapi.weixin.qq.com/cgi-bin"
        self._access_token: str | None = None
        self._token_expires_at: float = 0

    @property
    def is_configured(self) -> bool:
        """检查企业微信是否已配置凭证"""
        return bool(self.corp_id and self.corp_secret)

    async def _get_access_token(self) -> str:
        """获取/刷新 access_token（有效期 2 小时）"""
        import time

        if self._access_token and time.time() < self._token_expires_at:
            return self._access_token

        if not self.is_configured:
            raise RuntimeError("企业微信未配置 WECOM_CORP_ID / WECOM_CORP_SECRET")

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/gettoken",
                params={"corpid": self.corp_id, "corpsecret": self.corp_secret},
            )
            data = resp.json()

        if data.get("errcode", 0) != 0:
            raise RuntimeError(f"获取企业微信 token 失败: {data}")

        self._access_token = data["access_token"]
        self._token_expires_at = time.time() + data.get("expires_in", 7200) - 300  # 提前 5 分钟刷新
        logger.info("企业微信 access_token 获取成功")
        return self._access_token

    # ──────────────────────────────────────────────
    # 1. 发送应用消息（通知工作人员）
    # ──────────────────────────────────────────────

    async def send_text_message(self, user_ids: list[str], content: str) -> bool:
        """
        向指定员工发送文本消息。
        user_ids: 企业微信内部 UserID 列表
        """
        if not self.is_configured:
            logger.debug("企业微信未配置，跳过消息发送")
            return False

        token = await self._get_access_token()
        payload = {
            "touser": "|".join(user_ids),
            "msgtype": "text",
            "agentid": self.agent_id,
            "text": {"content": content},
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/message/send?access_token={token}",
                json=payload,
            )
            data = resp.json()

        if data.get("errcode", 0) != 0:
            logger.error(f"企业微信消息发送失败: {data}")
            return False

        logger.info(f"企业微信消息已发送 | 接收人: {user_ids}")
        return True

    # ──────────────────────────────────────────────
    # 2. 创建群聊（拉设计师 + 分享需求）
    # ──────────────────────────────────────────────

    async def create_group_chat(
        self,
        name: str,
        owner_id: str,
        member_ids: list[str],
    ) -> str | None:
        """
        创建企业微信群聊。
        返回群聊 chatid，失败返回 None。
        """
        if not self.is_configured:
            logger.debug("企业微信未配置，跳过群聊创建")
            return None

        token = await self._get_access_token()
        payload = {
            "name": name,
            "owner": owner_id,
            "userlist": member_ids,
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/appchat/create?access_token={token}",
                json=payload,
            )
            data = resp.json()

        if data.get("errcode", 0) != 0:
            logger.error(f"企业微信创建群聊失败: {data}")
            return None

        chat_id = data.get("chatid")
        logger.info(f"企业微信群聊创建成功 | chatid: {chat_id} | name: {name}")
        return chat_id

    # ──────────────────────────────────────────────
    # 3. 向群聊发送消息（分享需求）
    # ──────────────────────────────────────────────

    async def send_group_message(self, chat_id: str, content: str) -> bool:
        """向群聊发送文本消息"""
        if not self.is_configured:
            return False

        token = await self._get_access_token()
        payload = {
            "chatid": chat_id,
            "msgtype": "text",
            "text": {"content": content},
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/appchat/send?access_token={token}",
                json=payload,
            )
            data = resp.json()

        if data.get("errcode", 0) != 0:
            logger.error(f"企业微信群消息发送失败: {data}")
            return False

        return True

    # ──────────────────────────────────────────────
    # 4. 完整工作流：通知 + 建群 + 分享需求
    # ──────────────────────────────────────────────

    async def notify_new_order(
        self,
        order_sn: str,
        user_id: str,
        requirement: dict,
        designer_ids: list[str] | None = None,
    ) -> dict:
        """
        新订单通知完整工作流：
        1. 通知指定设计师（或默认组）有新订单
        2. 创建群聊
        3. 在群内分享需求详情

        返回: {"notified": bool, "chat_id": str | None}
        """
        if not self.is_configured:
            logger.info(f"企业微信未配置，跳过新订单通知 | order: {order_sn}")
            return {"notified": False, "chat_id": None}

        # 默认通知人
        target_ids = designer_ids or settings.wecom_default_notify_ids

        if not target_ids:
            logger.warning("未配置 WECOM_DEFAULT_NOTIFY_IDS，无法通知")
            return {"notified": False, "chat_id": None}

        # 构造需求摘要
        topic = requirement.get("topic", "未命名")
        pages = requirement.get("pages", "?")
        style = requirement.get("style", "未指定")
        details = requirement.get("details", "无")
        urgency = requirement.get("urgency", "normal")
        order_type = requirement.get("order_type", "standard")

        urgency_label = {"normal": "🟢 正常", "urgent": "🟡 加急", "very_urgent": "🔴 非常紧急"}.get(urgency, "🟢 正常")

        notify_content = (
            f"📋 新PPT订单通知\n"
            f"━━━━━━━━━━━━━\n"
            f"订单号: {order_sn}\n"
            f"客户ID: {user_id}\n"
            f"类型: {order_type}\n"
            f"紧急度: {urgency_label}\n"
            f"━━━━━━━━━━━━━\n"
            f"主题: {topic}\n"
            f"页数: {pages}\n"
            f"风格: {style}\n"
            f"详情: {details}\n"
            f"━━━━━━━━━━━━━\n"
            f"请尽快处理！"
        )

        # Step 1: 发送通知
        notified = await self.send_text_message(target_ids, notify_content)

        # Step 2: 创建群聊（可选）
        chat_id = None
        if len(target_ids) >= 2:
            chat_id = await self.create_group_chat(
                name=f"PPT-{order_sn[-6:]} {topic[:10]}",
                owner_id=target_ids[0],
                member_ids=target_ids,
            )

            # Step 3: 群内分享需求
            if chat_id:
                await self.send_group_message(chat_id, notify_content)

        # Step 4: 为设计师（默认群主/第一接收人）单独私发一份“一键出图 Prompt”
        designer_prompt = (
            f"🎯 专属出图提示词 (请直接复制给 AI 助手): \n\n"
            f"请帮我制作一份【{style}】风格的PPT，总页数约为【{pages}】页。\n"
            f"大纲与主题：{topic}。\n"
            f"客户特别备注要求：{details}。\n"
            f"要求逻辑清晰，大纲层次分明，版面现代简洁，适合{order_type}的应用场景。\n"
            f"请先给我输出完整的 Markdown 格式文字大纲。"
        )
        await self.send_text_message([target_ids[0]], designer_prompt)

        return {"notified": notified, "chat_id": chat_id}


# 全局单例
wecom_client = WeComClient()
