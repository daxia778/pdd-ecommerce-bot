"""
E2E 全链路模拟测试脚本。

模拟买家从咨询 → AI 回复 → 人工升级 → 接单 → 解决的完整业务闭环。
测试所有接口都返回预期字段且数据一致。

用法:
    python scripts/e2e_simulation.py
退出码:
    0 = 全部通过
    1 = 存在失败项
"""

import asyncio
import hashlib
import hmac
import json
import os
import sys
import time
import uuid

import httpx

# Add root directory to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import settings

BASE_URL = "http://127.0.0.1:8100"

# ===== 断言计数器 =====
_pass_count = 0
_fail_count = 0


def check(condition: bool, label: str, detail: str = "") -> bool:
    """断言包装器，通过/失败都计入统计。"""
    global _pass_count, _fail_count
    if condition:
        _pass_count += 1
        print(f"  ✅ {label}")
    else:
        _fail_count += 1
        msg = f"  ❌ {label}"
        if detail:
            msg += f" — {detail}"
        print(msg)
    return condition


def get_headers(payload_dict: dict) -> dict:
    headers = {"Content-Type": "application/json"}
    if settings.pdd_webhook_secret:
        body_bytes = json.dumps(payload_dict).encode("utf-8")
        sign = hmac.new(settings.pdd_webhook_secret.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()
        headers["X-PDD-Sign"] = sign
    return headers


async def simulate_e2e_flow() -> int:
    """返回失败数量，0 表示全部通过。"""
    print("🚀 开始模拟 PDD AI 客服全链路 E2E 流程...\n")

    buyer_id = f"test_buyer_{uuid.uuid4().hex[:8]}"
    print(f"👤 生成模拟买家 ID: {buyer_id}")

    async with httpx.AsyncClient(timeout=30) as client:
        # ── 0. 管理员登录 ──────────────────────────────────────
        print("\n🔐 0. 系统管理员登录...")
        login_res = await client.post(
            f"{BASE_URL}/api/v1/login", json={"username": "admin", "password": settings.admin_password}
        )
        check(login_res.status_code == 200, "登录状态码 200")
        token = login_res.json().get("access_token")
        check(token is not None, "获取到 JWT Token")
        if not token:
            print("  ⛔ 登录失败，终止测试。")
            return _fail_count
        auth_header = {"Authorization": f"Bearer {token}"}

        # ── 1. 模拟买家发送第一句话 ───────────────────────────
        print("\n💬 1. 模拟买家咨询: '你好，PPT 定制怎么收费？'")
        ts1 = int(time.time())
        payload1 = {
            "type": "customer_message",
            "buyer_id": buyer_id,
            "shop_id": "88888",
            "content": "你好，PPT定制怎么收费？",
            "timestamp": ts1,
        }
        res = await client.post(f"{BASE_URL}/api/v1/webhook/pdd", json=payload1, headers=get_headers(payload1))
        check(res.status_code == 200, "Webhook 第 1 条消息返回 200")
        check(res.json().get("msg") == "queued", "消息已入队")

        print("⏳ 等待 AI 处理 (15 秒)...")
        await asyncio.sleep(15)

        # ── 2. 验证消息记录 — A-1 & A-3 ──────────────────────
        print("\n🔍 2. 检查消息记录 (验证 A-1: AI 回复入库, A-3: 字段完整性)...")
        res = await client.get(f"{BASE_URL}/api/dashboard/messages/{buyer_id}", headers=auth_header)
        check(res.status_code == 200, "消息列表接口 200")
        msgs = res.json()
        check(len(msgs) >= 2, f"消息数量 >= 2 (实际: {len(msgs)})", "AI 回复应已入库")

        # A-3: 验证字段完整性
        if msgs:
            first_msg = msgs[0]
            check("platform" in first_msg, "消息包含 platform 字段")
            check("sender_type" in first_msg, "消息包含 sender_type 字段")
            check("role" in first_msg, "消息包含 role 字段")
            check(first_msg.get("platform") != "None" and first_msg.get("platform") is not None, "platform 不为 None")

            # 打印消息摘要
            for m in msgs[-4:]:
                sender = m.get("sender_type", "?")
                platform = m.get("platform", "?")
                print(f"    [{platform}] {sender}: {m.get('content', '')[:60]}")

        # A-1: 验证 AI 回复存在
        has_ai_reply = any(m.get("role") == "assistant" for m in msgs)
        check(has_ai_reply, "存在 assistant 角色的 AI 回复消息")

        # ── 3. 发送触发人工接管的消息 ─────────────────────────
        print("\n💬 3. 模拟买家触发升级: '人工客服，我要做10页，周五要，比较急'")
        ts2 = int(time.time())
        payload2 = {
            "type": "customer_message",
            "buyer_id": buyer_id,
            "shop_id": "88888",
            "content": "人工客服，我要做10页，周五要，比较急",
            "timestamp": ts2,
        }
        res = await client.post(f"{BASE_URL}/api/v1/webhook/pdd", json=payload2, headers=get_headers(payload2))
        check(res.status_code == 200, "Webhook 第 2 条消息返回 200")

        print("⏳ 等待 AI 处理 (15 秒)...")
        await asyncio.sleep(15)

        # ── 4. 检查升级池 — A-2 ──────────────────────────────
        print("\n🔍 4. 检查升级池 (验证 A-2: user_id 与 buyer_id 匹配)...")
        res = await client.get(f"{BASE_URL}/api/dashboard/escalations", headers=auth_header)
        check(res.status_code == 200, "升级池接口 200")
        escalations = res.json()
        if isinstance(escalations, dict):
            escalations = escalations.get("data", [])

        escalation_id = None
        for esc in escalations:
            # 验证字段存在性
            if esc.get("user_id") == buyer_id:
                escalation_id = esc["id"]
                trigger = esc.get("trigger_message", "")
                reason = esc.get("reason_label", "")
                print(f"    找到升级记录 ID: {escalation_id} | 触发消息: {trigger[:40]} | 原因: {reason}")
                break

        check(escalation_id is not None, f"升级池中找到 buyer_id={buyer_id} 的记录")

        if escalation_id:
            # ── 5. 人工接单 ──────────────────────────────────
            print("\n👨‍💻 5. 人工坐席接单 (Claim)")
            res = await client.post(
                f"{BASE_URL}/admin/api/admin/escalations/{escalation_id}/claim",
                json={"operator_name": "E2E测试坐席"},
                headers=auth_header,
            )
            check(res.status_code == 200, f"接单响应 200 (实际: {res.status_code})")

            # ── 6. 人工解决 ──────────────────────────────────
            print("\n✅ 6. 人工处理完毕 (Resolve)")
            res = await client.post(
                f"{BASE_URL}/api/dashboard/escalations/{escalation_id}/resolve",
                json={"operator_note": "E2E 测试 — 已接单处理"},
                headers=auth_header,
            )
            check(res.status_code == 200, f"解决响应 200 (实际: {res.status_code})")
        else:
            print("  ⚠️ 跳过步骤 5-6（未找到升级记录，可能是 AI 未触发人工转接关键词）")

        # ── 7. 系统健康度 ───────────────────────────────────
        print("\n🏥 7. 系统链路健康检查...")
        res = await client.get(f"{BASE_URL}/api/dashboard/system-health", headers=auth_header)
        check(res.status_code == 200, "健康检查接口 200")
        if res.status_code == 200:
            health = res.json()
            overall = health.get("overall", "unknown")
            print(f"    整体状态: {overall}")
            for comp in health.get("components", []):
                icon = comp.get("icon", "")
                print(f"    {icon} {comp['name']}: {comp['status']} | {comp['detail']}")

    # ── 汇总 ─────────────────────────────────────────────
    print(f"\n{'=' * 50}")
    print(f"🎉 E2E 测试完毕 | ✅ {_pass_count} 通过 | ❌ {_fail_count} 失败")
    print(f"{'=' * 50}")
    return _fail_count


if __name__ == "__main__":
    fails = asyncio.run(simulate_e2e_flow())
    sys.exit(1 if fails > 0 else 0)
