"""
NotebookLM Playwright 自动化服务 (完整实现版)

流程：
  1. 使用持久化浏览器上下文（已保存的 Google 登录态）
  2. 打开预配置的笔记本 URL
  3. 通过"粘贴文字"条目将 PPT 主题注入为来源
  4. 点击 Studio 面板中的"演示文稿"按钮触发生成
  5. 轮询等待生成完成（检测"更多选项"按钮出现）
  6. 监听 Playwright 下载事件，点击"下载 PowerPoint (.pptx)"
  7. 保存文件到 data/output/ 并返回本地绝对路径

首次使用前须完成授权：
    python scripts/auth_notebooklm.py

可通过 .env 配置目标笔记本：
    NOTEBOOKLM_NOTEBOOK_URL=https://notebooklm.google.com/notebook/xxxx
"""

import asyncio
import os
import time

try:
    from playwright.async_api import Download, async_playwright
    from playwright.async_api import TimeoutError as PWTimeoutError  # noqa: F401

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    async_playwright = None
    PLAYWRIGHT_AVAILABLE = False

from src.utils.logger import logger

# 生成文件输出目录
OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "output"))


class NotebookLMPlaywrightAutomation:
    def __init__(self):
        self.user_data_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "data", "playwright_context")
        )
        # 目标笔记本 URL，优先读 .env；未配置则用首页（会在首页新建笔记本）
        self.notebook_url = os.environ.get("NOTEBOOKLM_NOTEBOOK_URL", "https://notebooklm.google.com/")

    # ─────────────────────────────────────────────────────────────────────────
    # 主入口
    # ─────────────────────────────────────────────────────────────────────────

    async def generate_ppt(self, topic: str, pages: int, style: str, requirements: str = "") -> str:
        """
        使用持久化上下文自动操作 NotebookLM，生成 PPTX 并返回本地文件路径。
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError("playwright 未安装，请执行:\n  pip install playwright\n  playwright install chromium")

        if not os.path.exists(self.user_data_dir):
            raise RuntimeError(
                f"NotebookLM 未授权！请先运行: python scripts/auth_notebooklm.py\n目录 {self.user_data_dir} 不存在。"
            )

        os.makedirs(OUTPUT_DIR, exist_ok=True)

        logger.info(f"Playwright | 开始生成 PPT | 主题: {topic} | 页数: {pages} | 风格: {style}")

        async with async_playwright() as p:
            browser = await p.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                headless=True,
                accept_downloads=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                ],
            )

            try:
                page = browser.pages[0] if browser.pages else await browser.new_page()
                page.set_default_timeout(90_000)

                # Step 1: 导航
                await self._navigate(page)

                # Step 2: 添加来源
                source_text = self._build_source_text(topic, pages, style, requirements)
                await self._add_pasted_source(page, source_text)

                # Step 3: 点击 Studio「演示文稿」
                await self._click_studio_presentation(page)

                # Step 4: 等待生成完成
                await self._wait_for_presentation_ready(page)

                # Step 5: 下载 PPTX
                file_path = await self._download_pptx(page, topic)

                logger.info(f"Playwright | ✅ PPT 文件已保存: {file_path}")
                return file_path

            except Exception as e:
                logger.error(f"Playwright | ❌ 自动化执行异常: {e}", exc_info=True)
                raise
            finally:
                await browser.close()
                logger.info("Playwright | 浏览器已关闭")

    # ─────────────────────────────────────────────────────────────────────────
    # 内部辅助方法
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _build_source_text(topic: str, pages: int, style: str, requirements: str) -> str:
        """构建注入 NotebookLM 的来源文本，明确说明 PPT 要求"""
        return (
            f"【PPT 生成任务说明】\n"
            f"主题：{topic}\n"
            f"页数：{pages} 页\n"
            f"风格：{style}\n"
            f"具体要求：{requirements or '无'}\n\n"
            f"请基于以上信息生成一份内容充实、逻辑清晰的专业演示文稿。\n"
            f"每页需包含标题和要点内容，风格统一，适合商业汇报使用。"
        )

    async def _navigate(self, page):
        """导航到目标笔记本并验证登录状态"""
        logger.info(f"Playwright | 导航到: {self.notebook_url}")
        await page.goto(self.notebook_url, wait_until="domcontentloaded")
        await asyncio.sleep(3)  # 等待 Angular 应用完全挂载

        # 检测未登录（会重定向到 Google 登录页）
        if "accounts.google.com" in page.url or "signin" in page.url:
            raise RuntimeError("Google 会话已过期，请重新运行: python scripts/auth_notebooklm.py")
        logger.info(f"Playwright | 页面已加载: {page.url}")

    async def _add_pasted_source(self, page, text: str):
        """
        通过「添加来源 → 复制的文字」将 PPT 说明注入笔记本来源列表。
        这样 Studio 生成演示文稿时会基于该来源内容。
        注：界面中的菜单项标签是「复制的文字」（Copied text），非「粘贴文字」。
        """
        logger.info("Playwright | 正在添加来源（复制的文字）...")
        try:
            # 点击「添加来源」按钮（中英文兼容）
            for label in ["添加来源", "Add source", "+ 添加来源"]:
                btn = page.get_by_role("button", name=label).first
                try:
                    await btn.wait_for(state="visible", timeout=5000)
                    await btn.click()
                    logger.info(f"Playwright | 已点击: {label}")
                    break
                except Exception:
                    continue

            await asyncio.sleep(1)

            # 选择「复制的文字」菜单项（live UI 实测确认的真实标签）
            for item_name in ["复制的文字", "粘贴文字", "Copied text", "Paste text"]:
                menu_item = page.get_by_role("menuitem", name=item_name).first
                try:
                    await menu_item.wait_for(state="visible", timeout=4000)
                    await menu_item.click()
                    logger.info(f"Playwright | 已选择来源类型: {item_name}")
                    break
                except Exception:
                    continue

            await asyncio.sleep(1)

            # 找到文本输入区并填写
            # 使用 JavaScript 填充以确保中文字符不会报 Unknown key 错误
            text_input = page.locator("textarea[aria-label='粘贴的文字']").first
            try:
                await text_input.wait_for(state="visible", timeout=8000)
            except Exception:
                # 降级：找任意可见 textarea
                text_input = page.get_by_role("textbox").last
                await text_input.wait_for(state="visible", timeout=8000)

            await text_input.click()

            # 用 JavaScript 填充（解决 CJK 字符 playwright keyboard 限制）
            escaped_text = text.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")
            await page.evaluate(
                f"""
                const el = document.activeElement || document.querySelector('textarea');
                if (el) {{
                    const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                        window.HTMLTextAreaElement.prototype, 'value'
                    ).set;
                    nativeInputValueSetter.call(el, `{escaped_text}`);
                    el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                }}
                """
            )
            logger.info("Playwright | 已填写来源文本内容")
            await asyncio.sleep(0.8)

            # 点击「插入」确认按钮（实测 NotebookLM 用"插入"，非"插入来源"）
            for btn_name in ["插入", "插入来源", "Insert source", "Insert", "添加", "Add"]:
                btn = page.get_by_role("button", name=btn_name).last
                try:
                    await btn.wait_for(state="visible", timeout=3000)
                    await btn.click()
                    logger.info(f"Playwright | 已确认插入: {btn_name}")
                    break
                except Exception:
                    continue

            # 等待来源处理（索引建立约 3-5 秒）
            await asyncio.sleep(5)
            logger.info("Playwright | 来源添加完成")

        except Exception as e:
            logger.warning(f"Playwright | 添加来源失败，尝试直接生成: {e}")

    async def _click_studio_presentation(self, page):
        """
        点击 Studio 面板中的「演示文稿」按钮触发 PPT 生成。
        支持多种选择器和中英文界面。
        """
        logger.info("Playwright | 查找并点击「演示文稿」按钮...")

        # 按 aria-label 选择器尝试（从浏览器检查获取的真实属性）
        aria_selectors = [
            "[aria-label='演示文稿']",
            "[aria-label='Presentation']",
        ]
        for sel in aria_selectors:
            try:
                el = page.locator(sel).first
                await el.wait_for(state="visible", timeout=6000)
                await el.click()
                logger.info(f"Playwright | 已点击演示文稿按钮 (selector: {sel})")
                await asyncio.sleep(2)
                return
            except Exception:
                continue

        # 按文字内容回退
        for text in ["演示文稿", "Presentation"]:
            try:
                el = page.get_by_text(text, exact=True).first
                await el.wait_for(state="visible", timeout=5000)
                await el.click()
                logger.info(f"Playwright | 已点击演示文稿按钮 (text: {text})")
                await asyncio.sleep(2)
                return
            except Exception:
                continue

        raise RuntimeError("未找到「演示文稿」按钮，请检查 NotebookLM 界面是否有 Studio 面板。")

    async def _wait_for_presentation_ready(self, page, max_wait: int = 180):
        """
        轮询等待演示文稿生成完成。
        检测指标：Studio 面板中出现「更多选项」或「播放幻灯片」按钮。
        """
        ready_selectors = [
            "button[aria-label='更多选项']",
            "button[aria-label='More options']",
            "button[aria-label='开始播放幻灯片']",
            "button[aria-label='Play slideshow']",
        ]

        start = time.time()
        poll_interval = 4  # 每 4 秒检查一次

        while time.time() - start < max_wait:
            for sel in ready_selectors:
                try:
                    el = page.locator(sel).last
                    if await el.is_visible():
                        elapsed = int(time.time() - start)
                        logger.info(f"Playwright | ✅ 生成完成 ({elapsed}s) | 检测到: {sel}")
                        await asyncio.sleep(1.5)  # 等待 UI 稳定
                        return
                except Exception:
                    pass

            elapsed = int(time.time() - start)
            logger.info(f"Playwright | ⏳ 等待生成中... ({elapsed}s / {max_wait}s)")
            await asyncio.sleep(poll_interval)

        raise TimeoutError(
            f"NotebookLM 演示文稿生成超时（等待超过 {max_wait} 秒）。可尝试增大 NOTEBOOKLM_GENERATE_TIMEOUT 环境变量。"
        )

    async def _download_pptx(self, page, topic: str) -> str:
        """
        触发「下载 PowerPoint (.pptx)」并保存文件到 OUTPUT_DIR。
        返回下载文件的本地绝对路径。
        """
        # 点击「更多选项」打开下拉菜单
        more_opts_labels = ["更多选项", "More options"]
        for label in more_opts_labels:
            try:
                btn = page.get_by_role("button", name=label).last
                await btn.wait_for(state="visible", timeout=8000)
                await btn.click()
                logger.info(f"Playwright | 已点击「{label}」")
                await asyncio.sleep(0.8)
                break
            except Exception:
                continue

        # 生成安全文件名
        safe_name = "".join(c for c in topic[:25] if c.isalnum() or c in " _-").strip().replace(" ", "_")
        filename = f"ppt_{safe_name}_{int(time.time())}.pptx"
        dest_path = os.path.join(OUTPUT_DIR, filename)

        # 监听下载事件并点击下载菜单项
        download_texts = [
            "下载 PowerPoint (.pptx)",
            "Download PowerPoint (.pptx)",
        ]

        async with page.expect_download(timeout=120_000) as download_info:
            for text in download_texts:
                try:
                    item = page.get_by_text(text).first
                    await item.wait_for(state="visible", timeout=5000)
                    await item.click()
                    logger.info(f"Playwright | 已点击下载选项: {text}")
                    break
                except Exception:
                    continue

        download: Download = await download_info.value
        await download.save_as(dest_path)
        logger.info(f"Playwright | 文件已保存: {dest_path}")
        return dest_path
