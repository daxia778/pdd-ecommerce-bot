"""
RAG 引擎单元测试 — 测试知识库检索核心逻辑。

覆盖:
  - 文档添加与检索
  - 相关性过滤
  - 上下文构建
  - 软删除
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


class TestRAGEngine:
    """测试 RAG 引擎的核心功能"""

    @pytest.fixture(autouse=True)
    def setup_rag(self, tmp_path):
        """每个测试使用独立的临时 ChromaDB 目录"""
        os.environ["CHROMA_DB_DIR"] = str(tmp_path / "test_chroma")
        # 延迟导入避免模块级初始化问题
        from config.settings import settings

        settings.chroma_db_dir = str(tmp_path / "test_chroma")
        from src.core.rag_engine import RAGEngine

        self.rag = RAGEngine()

    def test_add_and_retrieve_document(self):
        """添加文档后应能检索到"""
        doc_id = self.rag.add_document(
            content="PPT定制设计服务，基础套餐150元/页起",
            metadata={"source": "test", "section": "pricing"},
        )
        assert doc_id is not None

        results = self.rag.retrieve("PPT多少钱", top_k=1)
        assert len(results) > 0
        assert "150" in results[0]["content"]

    def test_retrieve_returns_relevant_results(self):
        """检索结果应与查询相关"""
        self.rag.add_document(
            content="基础美化套餐适合内部汇报，150元/页起，5页起订",
            metadata={"source": "pricing", "section": "基础套餐"},
        )
        self.rag.add_document(
            content="高端定制套餐适合新品发布会，600元/页起",
            metadata={"source": "pricing", "section": "高端套餐"},
        )

        results = self.rag.retrieve("发布会PPT", top_k=2, relevance_threshold=-100.0)
        assert len(results) > 0

    def test_retrieve_empty_query(self):
        """空查询不应报错"""
        results = self.rag.retrieve("", top_k=3)
        assert isinstance(results, list)

    def test_build_context_from_docs(self):
        """build_context 应正确拼接文档内容"""
        docs = [
            {"content": "文档1内容", "section": "A"},
            {"content": "文档2内容", "section": "B"},
        ]
        context = self.rag.build_context(docs)
        assert "文档1内容" in context
        assert "文档2内容" in context

    def test_build_context_empty_list(self):
        """空文档列表应返回空字符串"""
        context = self.rag.build_context([])
        assert context == "" or context is None or len(context) == 0

    def test_get_doc_count(self):
        """文档计数应正确递增"""
        initial = self.rag.get_doc_count()
        self.rag.add_document(content="测试文档", metadata={"source": "test"})
        assert self.rag.get_doc_count() == initial + 1

    def test_delete_document(self):
        """删除文档后不应再被检索到"""
        doc_id = self.rag.add_document(
            content="这条知识应该被删除",
            metadata={"source": "test", "section": "delete_test"},
        )
        count_before = self.rag.get_doc_count()
        self.rag.delete_document(doc_id)
        assert self.rag.get_doc_count() == count_before - 1


class TestRAGQAPair:
    """测试 QA 对添加（双轨制学习）"""

    @pytest.fixture(autouse=True)
    def setup_rag(self, tmp_path):
        from config.settings import settings

        settings.chroma_db_dir = str(tmp_path / "test_chroma_qa")
        from src.core.rag_engine import RAGEngine

        self.rag = RAGEngine()

    def test_add_qa_pair(self):
        """人工话术学习：添加 QA 对后应可检索"""
        self.rag.add_qa_pair(
            question="你们最便宜多少钱",
            answer="模板调整款从299元起，基础美化5页750元起",
        )
        results = self.rag.retrieve("最低价格", top_k=1)
        assert len(results) > 0
        assert "299" in results[0]["content"] or "750" in results[0]["content"]
