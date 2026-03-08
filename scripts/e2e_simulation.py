"""
E2E 全链路模拟测试脚本 (增强版)。

模拟完整的生命周期：
1. 普通问答 (RAG & 缓存机制)
2. 人工接管池流转 (Escalation)
3. 自动生成订单 & 微信二维码对接流转 (Order State Machine)
    - chatting -> wechat_pending -> req_fixed

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
    print("🚀 开始模拟 PDD AI 客服全链路 E2E 流程 (增强版)...\n")

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
        print("\n💬 1. 模拟买家咨询 (一般售前触发缓存/RAG): '你好，PPT定制怎么收费？'")
        ts1 = int(time.time())
        payload1 = {
            "type": "customer_message",
            "buyer_id": buyer_id,
            "shop_id": "88888",
            "content": "你好，PPT定制怎么收费？",
            "timestamp": ts1,
        }
        res = await client.post(f"{BASE_URL}/api/v1/webhook/pdd", json=payload1, headers=get_headers(payload1))
        check(res.status_code == 200, "Webhook 通信正常")

        print("⏳ 等待 AI 处理 (15 秒)...")
        await asyncio.sleep(15)

        # ── 2. 验证消息记录 ──────────────────────
        print("\n🔍 2. 检查消息记录...")
        res = await client.get(f"{BASE_URL}/api/dashboard/messages/{buyer_id}", headers=auth_header)
        msgs = res.json()
        check(len(msgs) >= 2, f"成功收到 AI 回复 (当前消息数: {len(msgs)})")
        if msgs:
            print(f"    AI 回复内容: {msgs[-1].get('content', '')[:60]}...")

        # ── 3. 触发订单生成指令 ─────────────────────────
        print("\n💳 3. 模拟买家同意下单: '好的，请直接帮我下单，我要做10页的商业计划书，现在马上开始！'")
        ts2 = int(time.time())
        payload2 = {
            "type": "customer_message",
            "buyer_id": buyer_id,
            "shop_id": "88888",
            "content": "好的，请直接帮我下单，我要做10页的商业计划书，风格要商务的，现在马上开始！",
            "timestamp": ts2,
        }
        res = await client.post(f"{BASE_URL}/api/v1/webhook/pdd", json=payload2, headers=get_headers(payload2))
        check(res.status_code == 200, "Webhook 第 2 条消息返回 200")

        print("⏳ 等待 AI 判断意图并生单 (15 秒)...")
        await asyncio.sleep(15)

        # ── 4. 检查系统自动下单 ──────────────────────────────
        print("\n📦 4. 验证订单自动生成状态机 (consulting -> wechat_pending)...")
        res = await client.get(f"{BASE_URL}/api/dashboard/orders?show_all=true", headers=auth_header)
        orders = res.json()

        my_order = None
        for o in orders:
            if o.get("user_id") == buyer_id:
                my_order = o
                break

        check(my_order is not None, "系统已成功为客户创建订单")
        if my_order:
            order_id = my_order.get("id")
            order_sn = my_order.get("order_sn")
            check(
                my_order.get("status") == "wechat_pending",
                f"工单状态为: wechat_pending (实际: {my_order.get('status')})",
            )
            print(
                f"    已生成单号: {order_sn} | 状态: {my_order.get('status')} | 需求: {my_order.get('requirement', '')[:60]}"
            )

            # ── 5. 模拟发送微信二维码图片 ──────────────────────────────────
            print("\n📱 5. 模拟买家发送微信二维码 (触发工厂交付流)")
            # Webhook 这里不再是用 customer_message 过 LLM，而是模拟我们在 PDD 后台收到图片后映射到二维码接收端点
            qr_res = await client.post(
                f"{BASE_URL}/api/v1/wechat_qr?user_id={buyer_id}&image_url=http://fake.url/qr.png",
                headers=auth_header,
            )
            # 这是一个 P0 故障测试点：之前 /wechat_qr 代码在某些分支可能有 bug
            check(qr_res.status_code == 200, "二维码接收并处理成功")

            # 验证订单状态是否流转到 req_fixed
            res = await client.get(f"{BASE_URL}/api/dashboard/orders?show_all=true", headers=auth_header)
            updated_orders = res.json()
            updated_order = next((o for o in updated_orders if o.get("id") == order_id), None)
            if updated_order:
                check(
                    updated_order.get("status") in ("req_fixed", "generating", "processing", "awaiting_review"),
                    f"工单自动流转启动成功 (进入: {updated_order.get('status')})",
                )
                print("    ✨ 订单流转完毕！现在系统将自动推送到企业微信。")

        # ── 6. 模拟人工升级 ───────────────────────────────────
        print("\n🆘 6. 模拟买家极端催促，触发售后升级: '我马上要，太急了！如果太慢我要投诉！'")
        ts3 = int(time.time())
        payload3 = {
            "type": "customer_message",
            "buyer_id": buyer_id,
            "shop_id": "88888",
            "content": "我马上要，太急了！如果太慢我要投诉，找人工对接",
            "timestamp": ts3,
        }
        await client.post(f"{BASE_URL}/api/v1/webhook/pdd", json=payload3, headers=get_headers(payload3))

        print("⏳ 等待 AI 安全网/重定向阻断 (15 秒)...")
        await asyncio.sleep(15)

        res = await client.get(f"{BASE_URL}/api/dashboard/escalations", headers=auth_header)
        escalations = res.json()
        esc = next((e for e in escalations if e.get("user_id") == buyer_id), None)

        check(esc is not None, "意图分类器成功拦截特殊情绪并转人工")
        if esc:
            print(f"    触发升级: {esc.get('trigger_message')} | 原因: {esc.get('reason_label')}")

            print("\n👨‍💻 7. 管理员接单与处理...")
            esc_id = esc["id"]
            # Admin claim
            c_res = await client.post(
                f"{BASE_URL}/admin/api/admin/escalations/{esc_id}/claim",
                json={"operator_name": "E2E测试坐席"},
                headers=auth_header,
            )
            check(c_res.status_code == 200, "接单成功")

            # Admin resolve
            r_res = await client.post(
                f"{BASE_URL}/api/dashboard/escalations/{esc_id}/resolve",
                json={"operator_note": "急单已通过加急流程处理完毕"},
                headers=auth_header,
            )
            check(r_res.status_code == 200, "处理关闭成功")

    # ── 汇总 ─────────────────────────────────────────────
    print(f"\n{'='*50}")
    print(f"🎉 增强版 E2E 测试完毕 | ✅ {_pass_count} 通过 | ❌ {_fail_count} 失败")
    print(f"{'='*50}")
    return _fail_count


if __name__ == "__main__":
    fails = asyncio.run(simulate_e2e_flow())
    sys.exit(1 if fails > 0 else 0)
