"""
Prompt 加载器 — L2 企业化: 将 Prompt 从代码中解耦，支持热重载。

用法:
    from src.utils.prompt_loader import prompt_loader
    cfg = prompt_loader.get("ppt_consultant")
    system_prompt = cfg["base_system_prompt"].format(rag_context=...)
"""

import os
from pathlib import Path

import yaml

from src.utils.logger import logger

PROMPTS_DIR = Path("data/prompts")


class PromptLoader:
    """YAML Prompt 配置加载器 — 支持热重载（每次读取都检查文件修改时间）"""

    def __init__(self, prompts_dir: Path = PROMPTS_DIR):
        self._dir = prompts_dir
        self._cache: dict[str, dict] = {}
        self._mtimes: dict[str, float] = {}

    def get(self, name: str) -> dict:
        """
        获取指定名称的 Prompt 配置。

        Args:
            name: 配置文件名（不含 .yaml 后缀），如 "ppt_consultant"

        Returns:
            解析后的 YAML 字典

        Raises:
            FileNotFoundError: 配置文件不存在
        """
        path = self._dir / f"{name}.yaml"
        if not path.exists():
            raise FileNotFoundError(f"Prompt 配置文件不存在: {path}")

        # 热重载：检查文件修改时间，仅在文件变更时重新加载
        current_mtime = os.path.getmtime(path)
        cached_mtime = self._mtimes.get(name, 0)

        if name not in self._cache or current_mtime > cached_mtime:
            with open(path, encoding="utf-8") as f:
                self._cache[name] = yaml.safe_load(f)
            self._mtimes[name] = current_mtime
            logger.info(f"Prompt 配置已加载/刷新: {name} (mtime: {current_mtime})")

        return self._cache[name]

    def reload(self, name: str) -> dict:
        """强制重新加载指定配置"""
        self._cache.pop(name, None)
        self._mtimes.pop(name, None)
        return self.get(name)


# 全局单例
prompt_loader = PromptLoader()
