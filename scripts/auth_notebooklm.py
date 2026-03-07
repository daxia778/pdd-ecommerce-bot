"""
NotebookLM 登录授权辅助脚本

首次使用时，执行：
    python scripts/auth_notebooklm.py

该脚本会弹出一个可见的浏览器窗口，你在里面完成 Google 账号登录后，
关闭脚本，登录状态将保存到 data/playwright_context/ 目录。
之后自动化脚本可以复用该会话，无需再次登录。
"""

import asyncio
import os
import sys

# 把项目根目录加到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

USER_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "playwright_context"))


async def main():
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("❌ 请先安装 playwright:\n   pip install playwright\n   playwright install chromium")
        return

    os.makedirs(USER_DATA_DIR, exist_ok=True)
    print(f"📂 认证上下文将保存至: {USER_DATA_DIR}")
    print("🌐 正在打开浏览器... 请完成 Google 登录后，回到此终端按 Enter 键保存并退出。")

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--start-maximized",
            ],
            viewport=None,
            channel="chrome",  # 使用本机 Chrome（如果没有就去掉此行）
        )

        page = context.pages[0] if context.pages else await context.new_page()
        await page.goto("https://notebooklm.google.com/")

        print("\n>>> 浏览器已打开 NotebookLM，请完成登录。")
        print(">>> 登录完成后，回到此终端，按 Enter 键保存会话并退出。")
        input()

        await context.close()
        print("✅ 登录状态已保存！以后自动化运行将直接使用此会话，无需重新登录。")


if __name__ == "__main__":
    asyncio.run(main())
