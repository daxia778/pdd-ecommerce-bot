"""
src/core 包初始化 - 导出核心组件快捷引用。
"""

from .escalation_detector import analyze, detect_escalation
from .llm_client import LLMClient, get_llm_client
from .rag_engine import RAGEngine, get_rag_engine
from .session_manager import SessionManager, session_manager

__all__ = [
    "get_llm_client",
    "LLMClient",
    "get_rag_engine",
    "RAGEngine",
    "session_manager",
    "SessionManager",
    "analyze",
    "detect_escalation",
]
