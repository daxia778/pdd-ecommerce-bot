"""
LLM 通道延迟对比基准测试工具
对比 4 种不同的调用方式，帮助选择最优通道：

1. LiteLLM (OpenAI 兼容) → glm-4.7 (免费通用端点)
2. LiteLLM (OpenAI 兼容) → glm-4-flash (免费轻量端点)
3. ZAI 官方 SDK → glm-5 (付费旗舰模型)
4. ZAI 官方 SDK → glm-4-flash (免费模型走SDK通道)

每种通道各发 3 轮相同的 prompt，记录 TTFT 和总耗时，最终输出对比表格。
"""

import asyncio
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── 基本配置 ──────────────────────────────────────────────────
API_KEY = os.environ.get("ZHIPU_API_KEYS", "").split(",")[0].strip()
if not API_KEY:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    API_KEY = os.environ.get("ZHIPU_API_KEYS", "").split(",")[0].strip()

BASE_URL_GENERIC = "https://open.bigmodel.cn/api/paas/v4/"

# 测试 prompt（模拟真实客服场景，简短）
TEST_PROMPT = "我想做一个10页的PPT，用于工作汇报，简约大气风格，你们有什么推荐的档位？"
SYSTEM_PROMPT = "你是云芊艺小店的智小设AI客服，专注PPT设计服务。回复控制在80字以内。"

# ── 通道 1 & 2: LiteLLM (OpenAI 兼容) ─────────────────────────
async def test_litellm(model_name: str, label: str):
    """通过 LiteLLM 调用（当前项目使用的方式）"""
    import litellm
    from litellm import acompletion
    litellm.set_verbose = False
    
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": TEST_PROMPT},
    ]
    
    t_start = time.monotonic()
    ttft_ms = None
    chunks = []
    
    try:
        response = await acompletion(
            model=f"openai/{model_name}",
            messages=messages,
            api_key=API_KEY,
            base_url=BASE_URL_GENERIC,
            temperature=0.7,
            max_tokens=150,
            stream=True,
            timeout=30.0,
            extra_body={"thinking": {"type": "disabled"}},
        )
        
        async for chunk in response:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                if ttft_ms is None:
                    ttft_ms = int((time.monotonic() - t_start) * 1000)
                chunks.append(delta.content)
        
        total_ms = int((time.monotonic() - t_start) * 1000)
        reply = "".join(chunks)
        return {
            "label": label,
            "ttft_ms": ttft_ms or -1,
            "total_ms": total_ms,
            "chars": len(reply),
            "reply_preview": reply[:60],
            "error": None,
        }
    except Exception as e:
        total_ms = int((time.monotonic() - t_start) * 1000)
        return {
            "label": label,
            "ttft_ms": -1,
            "total_ms": total_ms,
            "chars": 0,
            "reply_preview": "",
            "error": str(e)[:80],
        }


# ── 通道 3 & 4: ZAI 官方 SDK ──────────────────────────────────
async def test_zai_sdk(model_name: str, label: str):
    """通过智谱官方 zai-sdk 调用"""
    from zai import ZaiClient
    
    client = ZaiClient(api_key=API_KEY)
    
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": TEST_PROMPT},
    ]
    
    t_start = time.monotonic()
    ttft_ms = None
    chunks = []
    
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0.7,
            max_tokens=150,
            stream=True,
        )
        
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                if ttft_ms is None:
                    ttft_ms = int((time.monotonic() - t_start) * 1000)
                chunks.append(chunk.choices[0].delta.content)
        
        total_ms = int((time.monotonic() - t_start) * 1000)
        reply = "".join(chunks)
        return {
            "label": label,
            "ttft_ms": ttft_ms or -1,
            "total_ms": total_ms,
            "chars": len(reply),
            "reply_preview": reply[:60],
            "error": None,
        }
    except Exception as e:
        total_ms = int((time.monotonic() - t_start) * 1000)
        return {
            "label": label,
            "ttft_ms": -1,
            "total_ms": total_ms,
            "chars": 0,
            "reply_preview": "",
            "error": str(e)[:80],
        }


# ── 通道 5: 原生 httpx 直连 (无框架开销) ──────────────────────
async def test_httpx_raw(model_name: str, label: str):
    """绕过所有框架，直接用 httpx 发送请求"""
    import httpx
    import json
    
    url = f"{BASE_URL_GENERIC}chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    }
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": TEST_PROMPT},
        ],
        "temperature": 0.7,
        "max_tokens": 150,
        "stream": True,
    }
    
    t_start = time.monotonic()
    ttft_ms = None
    chunks = []
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as resp:
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data_str = line[6:].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        delta = data.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            if ttft_ms is None:
                                ttft_ms = int((time.monotonic() - t_start) * 1000)
                            chunks.append(content)
                    except json.JSONDecodeError:
                        continue
        
        total_ms = int((time.monotonic() - t_start) * 1000)
        reply = "".join(chunks)
        return {
            "label": label,
            "ttft_ms": ttft_ms or -1,
            "total_ms": total_ms,
            "chars": len(reply),
            "reply_preview": reply[:60],
            "error": None,
        }
    except Exception as e:
        total_ms = int((time.monotonic() - t_start) * 1000)
        return {
            "label": label,
            "ttft_ms": -1,
            "total_ms": total_ms,
            "chars": 0,
            "reply_preview": "",
            "error": str(e)[:80],
        }


# ── 主测试流程 ─────────────────────────────────────────────────
CHANNELS = [
    ("LiteLLM → glm-4.7 (免费/通用)", lambda: test_litellm("glm-4.7", "LiteLLM→glm-4.7")),
    ("LiteLLM → glm-4-flash (免费/轻量)", lambda: test_litellm("glm-4-flash", "LiteLLM→glm-4-flash")),
    ("ZAI-SDK → glm-5 (付费/旗舰)", lambda: test_zai_sdk("glm-5", "ZAI-SDK→glm-5")),
    ("ZAI-SDK → glm-4-flash (免费/SDK通道)", lambda: test_zai_sdk("glm-4-flash", "ZAI-SDK→glm-4-flash")),
    ("httpx原生 → glm-4.7 (免费/零框架)", lambda: test_httpx_raw("glm-4.7", "httpx→glm-4.7")),
]

ROUNDS = 3  # 每个通道测试 3 轮


async def main():
    print("\n" + "=" * 90)
    print("🏁 LLM 多通道延迟对比基准测试")
    print(f"   测试 Prompt: \"{TEST_PROMPT}\"")
    print(f"   API Key: ***{API_KEY[-8:]}")
    print(f"   每通道 {ROUNDS} 轮")
    print("=" * 90)
    
    all_results = {}  # label -> list of results
    
    for ch_name, ch_fn in CHANNELS:
        print(f"\n{'─'*70}")
        print(f"📡 通道: {ch_name}")
        print(f"{'─'*70}")
        
        results = []
        for r in range(1, ROUNDS + 1):
            print(f"  ▶ 第 {r}/{ROUNDS} 轮...", end=" ", flush=True)
            result = await ch_fn()
            
            if result["error"]:
                print(f"❌ 失败: {result['error']}")
            else:
                print(f"✅ TTFT={result['ttft_ms']}ms  总耗时={result['total_ms']}ms  字数={result['chars']}")
            
            results.append(result)
            await asyncio.sleep(0.3)  # 避免限流
        
        all_results[ch_name] = results
    
    # ── 汇总对比表 ──────────────────────────────────────────────
    print("\n\n" + "=" * 90)
    print("📊 多通道延迟对比汇总")
    print("=" * 90)
    print(f"{'通道':<35} {'平均TTFT':>10} {'最低TTFT':>10} {'最高TTFT':>10} {'平均总耗时':>12} {'成功率':>8}")
    print("─" * 90)
    
    for ch_name, results in all_results.items():
        ok_results = [r for r in results if r["error"] is None]
        failed = len(results) - len(ok_results)
        
        if ok_results:
            avg_ttft = sum(r["ttft_ms"] for r in ok_results) // len(ok_results)
            min_ttft = min(r["ttft_ms"] for r in ok_results)
            max_ttft = max(r["ttft_ms"] for r in ok_results)
            avg_total = sum(r["total_ms"] for r in ok_results) // len(ok_results)
            success_rate = f"{len(ok_results)}/{len(results)}"
        else:
            avg_ttft = min_ttft = max_ttft = avg_total = -1
            success_rate = f"0/{len(results)}"
        
        print(f"{ch_name:<35} {avg_ttft:>8}ms {min_ttft:>8}ms {max_ttft:>8}ms {avg_total:>10}ms {success_rate:>8}")
    
    print("─" * 90)
    print("\n💡 结论建议：")
    print("   - TTFT 最低的通道 = 用户体感最快")
    print("   - 成功率 100% 的通道 = 最稳定")
    print("   - 付费通道(glm-5)通常享有更高优先级队列和更低延迟")
    print()


if __name__ == "__main__":
    asyncio.run(main())
