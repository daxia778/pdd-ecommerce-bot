"""
精准付费/免费模型对比测试 v2
- 同时解析 content 和 reasoning_content
- glm-4.7/glm-5 显式关闭思维链
"""

import asyncio
import json
import os
import sys
import time

import httpx

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

API_KEY = os.environ.get("ZHIPU_API_KEYS", "").split(",")[0].strip()
BASE_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
PROMPT = "我想做一个10页的PPT，用于工作汇报，简约大气风格，你们有什么推荐的档位？"
SYS = "你是云芊艺小店的智小设AI客服，专注PPT设计服务。回复控制在80字以内。"

TESTS = [
    # (label, model, extra_body)
    ("① glm-4.7 免费·关闭思维链", "glm-4.7", {"thinking": {"type": "disabled"}}),
    ("② glm-4.7 免费·开启思维链", "glm-4.7", {}),
    ("③ glm-4-air 付费·轻量", "glm-4-air", {}),
    ("④ glm-4-flash 免费·极速", "glm-4-flash", {}),
    ("⑤ glm-5 付费旗舰·关闭思维链", "glm-5", {"thinking": {"type": "disabled"}}),
    ("⑥ glm-5 付费旗舰·开启思维链", "glm-5", {}),
]

ROUNDS = 2


async def test_once(label, model, extra_body):
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}
    payload = {
        "model": model,
        "messages": [{"role": "system", "content": SYS}, {"role": "user", "content": PROMPT}],
        "temperature": 0.7,
        "max_tokens": 150,
        "stream": True,
    }
    if extra_body:
        payload.update(extra_body)

    t0 = time.monotonic()
    ttft = None
    content_chunks = []
    reasoning_chunks = []
    error = None

    try:
        async with httpx.AsyncClient(timeout=30.0) as c, c.stream("POST", BASE_URL, json=payload, headers=headers) as r:
            if r.status_code != 200:
                body = await r.aread()
                error = f"HTTP {r.status_code}: {body.decode()[:100]}"
            else:
                async for line in r.aiter_lines():
                    line = line.strip()
                    if not line.startswith("data:"):
                        continue
                    d = line[5:].strip()
                    if d == "[DONE]":
                        break
                    try:
                        obj = json.loads(d)
                        delta = obj.get("choices", [{}])[0].get("delta", {})
                        ct = delta.get("content", "")
                        rc = delta.get("reasoning_content", "")
                        if ct or rc:
                            if ttft is None:
                                ttft = int((time.monotonic() - t0) * 1000)
                            if ct:
                                content_chunks.append(ct)
                            if rc:
                                reasoning_chunks.append(rc)
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        error = str(e)[:100]

    total = int((time.monotonic() - t0) * 1000)
    content_text = "".join(content_chunks)
    reasoning_text = "".join(reasoning_chunks)

    # 首个正文 content 的时间（如果有 reasoning 先到，另算）
    return {
        "label": label,
        "ttft_ms": ttft or -1,
        "total_ms": total,
        "content_chars": len(content_text),
        "reasoning_chars": len(reasoning_text),
        "reply": content_text[:80] or reasoning_text[:80],
        "has_reasoning": len(reasoning_text) > 0,
        "error": error,
    }


async def main():
    print("\n" + "=" * 100)
    print("🏁 精准模型对比 v2（含思维链开/关对照实验）")
    print(f"   端点: {BASE_URL}")
    print(f"   Key: ***{API_KEY[-8:]}  |  每组 {ROUNDS} 轮")
    print("=" * 100)

    summary = {}

    for label, model, extra in TESTS:
        print(f"\n{'─'*90}")
        print(f"📡 {label}")
        print(f"{'─'*90}")

        results = []
        for r in range(1, ROUNDS + 1):
            print(f"  ▶ R{r}...", end=" ", flush=True)
            res = await test_once(label, model, extra)
            if res["error"]:
                print(f"❌ {res['error']}")
            else:
                reasoning_tag = f" 🧠思维链={res['reasoning_chars']}字" if res["has_reasoning"] else ""
                print(
                    f"✅ TTFT={res['ttft_ms']}ms  总耗时={res['total_ms']}ms  "
                    f"正文={res['content_chars']}字{reasoning_tag}"
                )
                if r == 1:
                    print(f"     📝 {res['reply']}")
            results.append(res)
            await asyncio.sleep(0.5)
        summary[label] = results

    # 汇总
    print("\n\n" + "=" * 110)
    print("📊 汇总对比")
    print("=" * 110)
    print(f"{'组别':<40} {'平均TTFT':>10} {'平均总耗':>10} {'正文字数':>10} {'思维链字数':>10} {'成功率':>8}")
    print("─" * 110)
    for label, results in summary.items():
        ok = [r for r in results if r["error"] is None and r["ttft_ms"] > 0]
        if ok:
            at = sum(r["ttft_ms"] for r in ok) // len(ok)
            tt = sum(r["total_ms"] for r in ok) // len(ok)
            cc = sum(r["content_chars"] for r in ok) // len(ok)
            rc = sum(r["reasoning_chars"] for r in ok) // len(ok)
            sr = f"{len(ok)}/{len(results)}"
        else:
            at = tt = cc = rc = -1
            sr = f"0/{len(results)}"
        print(f"{label:<40} {at:>8}ms {tt:>8}ms {cc:>8} {rc:>8} {sr:>8}")

    print("─" * 110)
    print("\n🔑 关键结论:")
    print("   - 思维链开/关对 TTFT 的影响 = 延迟的主要组成")
    print("   - 正文字数为0 = 模型把所有 token 花在了思维链推理上")
    print("   - glm-4-air/flash 无思维链模式 → 直接输出正文 → TTFT 最低")
    print()


if __name__ == "__main__":
    asyncio.run(main())
