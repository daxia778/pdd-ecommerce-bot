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


def get_headers(payload_dict):
    headers = {"Content-Type": "application/json"}
    if settings.pdd_webhook_secret:
        body_bytes = json.dumps(payload_dict).encode("utf-8")
        sign = hmac.new(settings.pdd_webhook_secret.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()
        headers["X-PDD-Sign"] = sign
    return headers


async def simulate_e2e_flow():
    print("🚀 开始模拟 PDD AI 客服全链路 E2E 流程...\n")

    buyer_id = f"test_buyer_{str(uuid.uuid4())[:8]}"
    print(f"👤 生成模拟买家 ID: {buyer_id}")

    async with httpx.AsyncClient() as client:
        # 0. 先登录获取 admin token
        print("🔐 0. 系统管理员登录...")
        login_res = await client.post(
            f"{BASE_URL}/api/v1/login", json={"username": "admin", "password": settings.admin_password}
        )
        token = login_res.json().get("access_token") if login_res.status_code == 200 else None
        auth_header = {"Authorization": f"Bearer {token}"} if token else {}
        if not token:
            print("  ❌ 登录失败，终止测试。")
            return
        else:
            print("  ✅ 登录成功，获取 Token。")

        # 1. 模拟买家发送第一句话 (打招呼/咨询定价)
        print("\n💬 1. 模拟买家发送第一句话: '你好，PPT定制怎么收费？'")
        ts1 = int(time.time())
        payload1 = {
            "type": "customer_message",
            "buyer_id": buyer_id,
            "shop_id": "88888",
            "content": "你好，PPT定制怎么收费？",
            "timestamp": ts1,
        }

        res = await client.post(f"{BASE_URL}/api/v1/webhook/pdd", json=payload1, headers=get_headers(payload1))
        print(f"  [Webhook 响应]: {res.status_code} - {res.text}")

        print("⏳ 等待 AI 处理 (5 秒)...")
        await asyncio.sleep(5)

        # 2. 验证消息是否被记录，且状态机状态为何
        print("🔍 2. 检查会话状态...")
        res = await client.get(f"{BASE_URL}/api/dashboard/messages/{buyer_id}", headers=auth_header)
        if res.status_code == 200:
            msgs = res.json()
            print(f"  [消息记录]: 共 {len(msgs)} 条")
            for m in msgs[-3:]:
                print(f"    - [{m.get('platform')}] {m.get('sender_type')}: {m.get('content')}")
        else:
            print(f"  [错误]: 无法获取会话记录 - {res.text}")

        # 3. 模拟买家发送明确需求 -> 触发建单/升级
        print("\n💬 3. 模拟买家发送需求，触发人工接管: '人工客服，我要做10页，周五要，比较急'")
        ts2 = int(time.time())
        payload2 = {
            "type": "customer_message",
            "buyer_id": buyer_id,
            "shop_id": "88888",
            "content": "人工客服，我要做10页，周五要，比较急",
            "timestamp": ts2,
        }
        res = await client.post(f"{BASE_URL}/api/v1/webhook/pdd", json=payload2, headers=get_headers(payload2))
        print(f"  [Webhook 响应]: {res.status_code} - {res.text}")

        print("⏳ 等待 AI 处理 (5 秒)...")
        await asyncio.sleep(5)

        # 4. 检查是否产生了待处理工单/升级
        print("🔍 4. 检查人工干预/升级池...")
        res = await client.get(f"{BASE_URL}/api/dashboard/escalations", headers=auth_header)
        escalations = res.json().get("data", []) if isinstance(res.json(), dict) else res.json()
        print(f"  [升级池]: 当前数量: {len(escalations)}")
        escalation_id = None
        for esc in escalations:
            if esc.get("user_id") == buyer_id or esc.get("buyer_id") == buyer_id:
                escalation_id = esc["id"]
                print(f"    - 找到对应的升级记录 ID: {escalation_id}, 触发词: {esc.get('trigger_keyword')}")

        if escalation_id:
            # 5. 模拟人工接单
            print("\n👨‍💻 5. 人工坐席接单 (Claim)")

            res = await client.post(
                f"{BASE_URL}/admin/api/admin/escalations/{escalation_id}/claim",
                json={"operator_name": "系统测试坐席"},
                headers=auth_header,
            )
            print(f"  [接单响应]: {res.status_code} - {res.text}")

            # 6. 模拟人工处理完成
            print("✅ 6. 人工处理完毕 (Resolve)")
            res = await client.post(
                f"{BASE_URL}/api/dashboard/escalations/{escalation_id}/resolve",
                json={"operator_note": "已接单，加急处理中"},
                headers=auth_header,
            )
            print(f"  [完成响应]: {res.status_code} - {res.text}")

        # 7. 检查系统健康度
        print("\n🏥 7. 检查系统链路健康度...")
        res = await client.get(f"{BASE_URL}/api/dashboard/system-health", headers=auth_header)
        if res.status_code == 200:
            health = res.json()
            print(f"  [整体健康度]: {health.get('overall')}")
            for comp in health.get("components", []):
                print(f"    - {comp['name']}: {comp['status']} | {comp['detail']}")
        else:
            print(f"  [错误]: {res.status_code} - {res.text}")

        print("\n🎉 E2E 测试脚本执行完毕！")


if __name__ == "__main__":
    asyncio.run(simulate_e2e_flow())
