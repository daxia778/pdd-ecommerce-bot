"""
运行此脚本进行 NotebookLM 的一次性登录授权。
它将打开一个带界面的 Chromium 浏览器，您需要手动登录您的 Google 账号并进入 NotebookLM 页面。
登录完成后，脚本会自动保存对应的 Context（Cookie/LocalStorage 等），后续的自动生成服务将复用此凭证。
"""
import os
import asyncio
from playwright.async_api import async_playwright
from src.utils.logger import logger

# Context 保存路径
USER_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "playwright_context"))

async def auth_notebooklm():
    os.makedirs(USER_DATA_DIR, exist_ok=True)
    logger.info(f"保存授权信息的目录: {USER_DATA_DIR}")
    
    async with async_playwright() as p:
        # 使用 launch_persistent_context 启动，这样用户的登录状态才会固化到 USER_DATA_DIR
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False,  # 必须显示界面以便用户人工操作登录
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = browser.pages[0] if browser.pages else await browser.new_page()
        
        logger.info("正在打开 NotebookLM，请在弹出的浏览器中完成您的 Google 账密登录...")
        await page.goto("https://notebooklm.google.com/")
        
        print("="*60)
        print("等待手动登录完成...")
        print("请在浏览器中登录 Google 账号，并确保您可以正常看到您的 NotebookLM 笔记本列表。")
        print("登录操作完成并能看到笔记本页面后，请在这里按回车键！")
        print("="*60)
        
        # 阻塞等待用户在控制台按回车
        await asyncio.to_thread(input, "按回车键结束并保存授权状态: ")
        
        logger.info("用户确认已登录，正在保存并关闭浏览器上下文...")
        await browser.close()
        logger.info(f"✅ NotebookLM 授权信息已成功固化至: {USER_DATA_DIR}")
        logger.info("后续的自动化生成任务可以直接复用该状态。")

if __name__ == "__main__":
    asyncio.run(auth_notebooklm())
