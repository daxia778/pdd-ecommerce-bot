"""
独立测试脚本 - 直接测试 ZhipuAI API 连通性，不需要启动 FastAPI。
运行方式：python test_llm.py
"""
import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.llm_client import get_llm_client
from src.utils.logger import logger

# 创建日志目录
os.makedirs("logs", exist_ok=True)


async def test_basic_chat():
    """测试 1: 基础对话"""
    print("\n" + "=" * 50)
    print("📡 测试 1: 基础对话")
    print("=" * 50)

    llm = get_llm_client()
    messages = [{"role": "user", "content": "你好，请用一句话介绍你自己。"}]

    reply = await llm.chat(messages=messages)
    print(f"✅ AI 回复: {reply}")
    return True


async def test_customer_service():
    """测试 2: 客服角色扮演"""
    print("\n" + "=" * 50)
    print("🛒 测试 2: 客服角色对话")
    print("=" * 50)

    system_prompt = "你是拼多多店铺的专业客服，请用简洁友好的语气回复客户问题。"
    llm = get_llm_client()

    messages = [
        {"role": "user", "content": "我的订单什么时候发货？"},
    ]

    reply = await llm.chat(messages=messages, system_prompt=system_prompt)
    print(f"✅ 客服回复: {reply}")
    return True


async def test_multi_turn():
    """测试 3: 多轮对话（模拟会话历史）"""
    print("\n" + "=" * 50)
    print("💬 测试 3: 多轮对话")
    print("=" * 50)

    llm = get_llm_client()
    history = []

    conversations = [
        "我买的耳机有一只没有声音",
        "我收货已经 3 天了",
    ]

    for user_msg in conversations:
        history.append({"role": "user", "content": user_msg})
        print(f"👤 客户: {user_msg}")

        reply = await llm.chat(
            messages=history,
            system_prompt="你是拼多多店铺客服，帮助处理售后问题。",
        )
        history.append({"role": "assistant", "content": reply})
        print(f"🤖 客服: {reply}\n")

    return True


async def main():
    print("=" * 50)
    print("🔬 ZhipuAI API 连通性测试")
    print("=" * 50)

    tests = [
        ("基础对话", test_basic_chat),
        ("客服角色", test_customer_service),
        ("多轮对话", test_multi_turn),
    ]

    passed = 0
    for name, test_fn in tests:
        try:
            await test_fn()
            passed += 1
        except Exception as e:
            print(f"❌ 测试 [{name}] 失败: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 50)
    print(f"📊 测试结果: {passed}/{len(tests)} 通过")
    print("=" * 50)

    if passed == len(tests):
        print("🎉 所有测试通过！ZhipuAI API 连接正常，可以启动主服务。")
        print("   运行命令: python main.py")
    else:
        print("⚠️  部分测试失败，请检查:")
        print("   1. ZHIPU_API_KEYS 是否配置正确")
        print("   2. 网络是否可以访问 open.bigmodel.cn")
        print("   3. 如需代理，在 .env 中配置 HTTPS_PROXY")


if __name__ == "__main__":
    asyncio.run(main())
