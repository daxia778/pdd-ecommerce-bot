"""
Prompt 加载器 — v3.0 模块化架构: 支持从多个 .md 文件自动组装 System Prompt。

灵感来源：Claude Code / Cursor / Manus 的分层提示词架构设计。
每个 .md 文件是独立的功能模块，main.yaml 定义组装顺序。

用法:
    from src.utils.prompt_loader import prompt_loader
    system_prompt = prompt_loader.assemble_system_prompt(rag_context="...")
    # 或者兼容旧接口:
    cfg = prompt_loader.get("main")
"""

import os
from pathlib import Path

import yaml

from src.utils.logger import logger

PROMPTS_DIR = Path("data/prompts")


class PromptLoader:
    """模块化 Prompt 组装引擎 — 支持热重载（每次读取检查文件修改时间）"""

    def __init__(self, prompts_dir: Path = PROMPTS_DIR):
        self._dir = prompts_dir
        self._cache: dict[str, dict] = {}
        self._mtimes: dict[str, float] = {}
        self._assembled_cache: str | None = None
        self._assembled_mtime: float = 0

    def get(self, name: str) -> dict:
        """
        获取指定名称的 YAML 配置（兼容旧调用方式）。

        Args:
            name: 配置文件名（不含 .yaml 后缀），如 "main" 或 "ppt_consultant"

        Returns:
            解析后的 YAML 字典

        Raises:
            FileNotFoundError: 配置文件不存在
        """
        path = self._dir / f"{name}.yaml"
        if not path.exists():
            raise FileNotFoundError(f"Prompt 配置文件不存在: {path}")

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
        self._assembled_cache = None
        return self.get(name)

    def _read_module(self, relative_path: str) -> str:
        """读取单个 .md 模块文件"""
        full_path = self._dir / relative_path
        if not full_path.exists():
            logger.warning(f"Prompt 模块文件不存在，跳过: {full_path}")
            return ""
        with open(full_path, encoding="utf-8") as f:
            return f.read().strip()

    def _get_max_mtime(self, config: dict) -> float:
        """获取所有模块文件中最新的修改时间"""
        max_mtime = os.path.getmtime(self._dir / "main.yaml")
        for module_path in config.get("assembly_order", []):
            full_path = self._dir / module_path
            if full_path.exists():
                mtime = os.path.getmtime(full_path)
                if mtime > max_mtime:
                    max_mtime = mtime
        return max_mtime

    def assemble_system_prompt(self, rag_context: str = "") -> str:
        """
        按照 main.yaml 中定义的 assembly_order，
        依次读取各模块文件并拼装为最终的 System Prompt。

        支持热重载：任一模块文件变更后，下一次调用自动重新组装。

        Args:
            rag_context: RAG 检索结果（运行时注入）

        Returns:
            完整的 system prompt 字符串
        """
        config = self.get("main")
        current_max_mtime = self._get_max_mtime(config)

        # 热重载检查：如果任一模块文件被修改，清除缓存重新组装
        if self._assembled_cache is not None and current_max_mtime <= self._assembled_mtime and not rag_context:
            return self._assembled_cache

        # 按顺序组装各模块
        parts: list[str] = []
        assembly_order = config.get("assembly_order", [])

        for module_path in assembly_order:
            content = self._read_module(module_path)
            if content:
                parts.append(content)

        # 追加 RAG 动态上下文
        if rag_context:
            rag_template = config.get("rag_context_template", "{rag_context}")
            parts.append(rag_template.format(rag_context=rag_context))

        assembled = "\n\n".join(parts)

        # 缓存（不含 RAG 的静态部分）
        if not rag_context:
            self._assembled_cache = assembled
            self._assembled_mtime = current_max_mtime

        module_count = len(assembly_order)
        total_chars = len(assembled)
        logger.info(
            f"System Prompt 组装完成 | 模块数: {module_count} | "
            f"总字符: {total_chars} | RAG: {'有' if rag_context else '无'}"
        )

        return assembled

    def get_ppt_keywords(self) -> list[str]:
        """获取 PPT 需求识别关键词列表"""
        config = self.get("main")
        return config.get("ppt_keywords", [])

    def get_slot_filling_hint(self) -> str:
        """获取 Slot Filling 追加提示"""
        config = self.get("main")
        return config.get("slot_filling_hint", "")

    def get_intent_prompt(self) -> str:
        """获取意图分类 prompt"""
        return self._read_module("intent_classification/prompt.md")


# 全局单例
prompt_loader = PromptLoader()
