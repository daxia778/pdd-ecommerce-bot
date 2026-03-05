import os
import asyncio
from playwright.async_api import async_playwright
from src.utils.logger import logger

class NotebookLMPlaywrightAutomation:
    def __init__(self):
        self.user_data_dir = os.path.abspath(os.path.join(
            os.path.dirname(__file__), "..", "..", "data", "playwright_context"
        ))
        
    async def generate_ppt(self, topic: str, pages: int, style: str, requirements: str = "") -> str:
        """
        使用持久化上下文自动操作 NotebookLM
        """
        if not os.path.exists(self.user_data_dir):
            raise RuntimeError(
                f"NotebookLM 未授权！请先在本地运行: python scripts/auth_notebooklm.py 完成登录。目录 {self.user_data_dir} 不存在。"
            )
            
        logger.info(f"Playwright | 初始化无头浏览器生成 PPT: {topic}")
        
        async with async_playwright() as p:
            # 线上运行时通常为 headless=True，如需排错可临时改回 False
            browser = await p.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                headless=True, 
                args=["--disable-blink-features=AutomationControlled"]
            )
            
            try:
                page = browser.pages[0] if browser.pages else await browser.new_page()
                # 调整页面超时设置，等待 NotebookLM 这种重度应用
                page.set_default_timeout(60000)
                
                await page.goto("https://notebooklm.google.com/")
                
                # --------- 注意 ---------
                # NotebookLM 目前官方并未原生支持类似 "直接生成 PPT 文档并导出" 的单一按钮操作。
                # 它的本质是基于已上传的知识源（Sources）生成摘要、Study Guide 和大纲。
                # 要实现“生成 PPT”：
                # 方案 A: 你的 NotebookLM 账号中已经预建好了一个通用的“文档仓库机器人”或者特定笔记本。
                # 方案 B: 必须先创建新笔记本 -> 上传参考资料 -> 在对话栏中要求 AI 按指定页数生成大纲 -> 提取文本 -> 借助其他工具转换。
                
                # 鉴于 NotebookLM 的限制，如果您的会员功能里存在某些尚未公测的特权，请补充页面逻辑。
                # 这里的代码模板假设：
                # 1. 有一个通用的聊天框 (textarea)
                # 2. 我们输入结构化的 Prompt
                # 3. 我们等待回答区域出现结果，然后抓取文本
                
                # 构建给 NotebookLM 的 Prompt
                prompt_text = (
                    f"请帮我生成一份关于《{topic}》的 PPT 大纲及每页详细内容。\n"
                    f"总要求共 {pages} 页左右。\n"
                    f"整体风格请偏向：{style}。\n"
                    f"具体要求如下：{requirements}\n"
                    f"请直接给出具体的标题和详细内容，不需要多余的寒暄。"
                )
                
                logger.info(f"Playwright | 正在向 NotebookLM 提交需求...")
                # 下面的选择器 (Selector) 极有可能因为 Google 随时更新前端代码而失效。
                # 请在本地实际调试时，通过浏览器的开发者工具 (F12) 重新获取准确的标签或 aria-label。
                
                # 找到输入框 (假设 aria-label="Ask NotebookLM" 或者直接找 textarea)
                # 等待主界面加载完毕
                await page.wait_for_selector("textarea", state="visible")
                await page.fill("textarea", prompt_text)
                await page.press("textarea", "Enter")
                
                logger.info("Playwright | 需求已提交，等待 AI 生成响应内容...")
                
                # 等待 NotebookLM 的思考和生成过程（这部分可能很长，特别是几十页的 PPT 内容）
                # 这里假设最新生成的回复在特定的标识区块内。实际选择器需要对应当时的前端结构。
                # 这个等待逻辑通常是：等待某个“生成中”的 spinner 消失，或者等待新的对话气泡出现并且其中的文本不再发生变化。
                
                await asyncio.sleep(15) # 基础硬等待，因为流式输出比较难抓取消失节点
                
                # 获取最后一次回复的文本块
                # (注意: 这里使用了非常泛化的选择器，实际中可能类似 '.chat-message:last-child p' 等)
                try:
                    # 尝试找 Google 常见的回复区块
                    bot_responses = await page.locator("div[role='log'] >> text").all_inner_texts() 
                    if bot_responses:
                        result_text = bot_responses[-1]
                    else:
                        result_text = "未能在页面提取到特定内容，请检查选择器。"
                except Exception as e:
                    logger.warning(f"Playwright 提取文本失败: {e}")
                    result_text = "提取文本失败"
                    
                logger.info("Playwright | AI 内容生成完毕。")
                
                # NotebookLM 目前不支持直接下载 .pptx 文件。
                # 因此我们能取到的大概率是排版好的 Markdown / 文本。
                # 如果要“交付 PPT”，可能还需要接入 python-pptx 或类似服务将文本转文件。
                # 此处暂时将生成的纯文本保存并返回伪文件路径。
                 
                mock_file_name = f"gen_ppt_{topic[:5]}.md"
                with open(mock_file_name, "w", encoding="utf-8") as f:
                    f.write(result_text)
                    
                return mock_file_name
                
            except Exception as e:
                logger.error(f"Playwright 执行过程中出现异常: {e}")
                raise e
            finally:
                await browser.close()
                logger.info("Playwright | 浏览器上下文已关闭，任务结束。")
