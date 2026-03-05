"""
RAG 引擎 - 向量检索与上下文注入。
使用 ChromaDB 作为本地向量数据库。
Embedding: 本地 sentence-transformers 多语言模型（无 API 限速，支持中文）。
LLM 推理: ZhipuAI（仅用于聊天，不用于 Embedding）。

P0-4 修复: 集合名称从 ppt_shop_knowledge 更正为 pdd_shop_knowledge（匹配实际业务）
P1-2 增强: retrieve() 支持相关性阈值过滤，低相关性片段不注入 Prompt
"""
import os
from typing import List, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings

from config.settings import settings
from src.utils.logger import logger

# 本地 Embedding 模型（多语言，支持中文，384维）
# 首次运行会自动下载 ~120MB 模型文件
EMBEDDING_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"

# P0-4: 修正集合名称，与业务一致
COLLECTION_NAME = "pdd_shop_knowledge"

# 懒加载 - 避免启动时长时间等待
_sentence_model = None


def get_sentence_model():
    """获取本地 Embedding 模型（懒加载单例）"""
    global _sentence_model
    if _sentence_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"加载本地 Embedding 模型: {EMBEDDING_MODEL_NAME}")
            _sentence_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
            logger.info("✅ 本地 Embedding 模型加载完成")
        except Exception as e:
            logger.error(f"❌ 本地 Embedding 模型加载失败: {e}")
            raise
    return _sentence_model


def get_local_embedding(text: str) -> List[float]:
    """使用本地 sentence-transformers 将文本转为向量（同步）"""
    model = get_sentence_model()
    embedding = model.encode(text[:512], show_progress_bar=False)
    return embedding.tolist()


class RAGEngine:
    """
    RAG 检索引擎。
    - 本地 sentence-transformers 向量化（无限速）
    - ChromaDB 持久化存储
    - 语义相似度检索
    - P1-2: 相关性阈值过滤（默认 0.3，低于此分数的片段丢弃）
    - 结果组装为 LLM Prompt 上下文
    """

    def __init__(self):
        # 初始化 ChromaDB 客户端（本地持久化）
        db_path = os.path.abspath(settings.chroma_db_dir)
        os.makedirs(db_path, exist_ok=True)

        self._client = chromadb.PersistentClient(
            path=db_path,
            settings=ChromaSettings(anonymized_telemetry=False),
        )

        # P0-4: 使用正确的集合名称
        self._collection = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"description": "PDD店铺知识库"},
        )

        doc_count = self._collection.count()
        logger.info(f"RAGEngine 初始化 | 集合: {COLLECTION_NAME} | 知识库文档数: {doc_count}")

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
        relevance_threshold: float = None,
    ) -> List[dict]:
        """
        语义检索（同步）：将查询文本向量化后，在知识库中检索最相关的片段。

        Args:
            query: 查询文本
            top_k: 最多返回片段数
            relevance_threshold: P1-2 相关性阈值（0~1），低于此值的片段被过滤。
                                  None 时使用 settings.rag_relevance_threshold

        Returns:
            List of {"content": str, "source": str, "section": str, "relevance": float}
        """
        if self._collection.count() == 0:
            logger.warning("知识库为空，跳过 RAG 检索（请先运行 python scripts/load_knowledge.py）")
            return []

        # P1-2: 使用配置项或传入的阈值
        threshold = relevance_threshold if relevance_threshold is not None else settings.rag_relevance_threshold

        try:
            query_embedding = get_local_embedding(query)

            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=min(top_k, self._collection.count()),
                include=["documents", "metadatas", "distances"],
            )

            retrieved = []
            filtered_count = 0
            for doc, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            ):
                # 转换 L2 距离为相关性分数（0~1）
                relevance = max(0.0, 1.0 - dist / 2.0)

                # P1-2: 相关性阈值过滤
                if relevance < threshold:
                    filtered_count += 1
                    continue

                retrieved.append({
                    "content": doc,
                    "source": meta.get("source", "unknown"),
                    "section": meta.get("section", ""),
                    "relevance": round(relevance, 3),
                })

            logger.debug(
                f"RAG 检索 | 查询: {query[:30]}... | "
                f"命中: {len(retrieved)} 条 | 阈值过滤: {filtered_count} 条 | 阈值: {threshold}"
            )
            return retrieved

        except Exception as e:
            logger.warning(f"RAG 检索失败，不使用知识库上下文: {e}")
            return []

    def build_context(self, retrieved_docs: List[dict]) -> str:
        """将检索结果组装为 Prompt 上下文字符串"""
        if not retrieved_docs:
            return ""

        context_parts = ["【知识库参考信息】\n"]
        for i, doc in enumerate(retrieved_docs, 1):
            section_info = f"（{doc['section']}）" if doc["section"] else ""
            context_parts.append(f"【参考{i}】{section_info}\n{doc['content']}\n")

        return "\n".join(context_parts)

    def add_document(self, content: str, metadata: dict):
        """将单条文档手动存入向量库"""
        try:
            doc_id = f"doc_{int(time.time() * 1000)}"
            embedding = get_local_embedding(content)
            
            self._collection.add(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[content],
                metadatas=[metadata]
            )
            logger.info(f"RAG 动态学习 | 已存入新知识: {content[:30]}... | ID: {doc_id}")
            return doc_id
        except Exception as e:
            logger.error(f"RAG 存入知识失败: {e}")
            return None

    def add_qa_pair(self, question: str, answer: str, source: str = "human_sync"):
        """
        专门用于同步人工客服的优秀回复。
        将问题和答案组合存储，以便下次类似问题能检索到完整回复。
        """
        combined_content = f"问：{question}\n答：{answer}"
        metadata = {
            "source": source,
            "type": "qa_pair",
            "timestamp": time.time(),
            "section": "人工实战经验"
        }
        return self.add_document(combined_content, metadata)

    def get_doc_count(self) -> int:
        """返回知识库中的文档数量"""
        return self._collection.count()

    def get_all_documents(self):
        """获取所有知识库文档片段"""
        try:
            return self._collection.get()
        except Exception as e:
            logger.error(f"RAG 获取所有文档失败: {e}")
            return None
            
    def delete_document(self, doc_id: str) -> bool:
        """删除指定 ID 的知识片段"""
        try:
            self._collection.delete(ids=[doc_id])
            logger.info(f"RAG 已删除文档 | ID: {doc_id}")
            return True
        except Exception as e:
            logger.error(f"RAG 删除文档失败: {doc_id} | {e}")
            return False


# 全局单例（懒加载）
_rag_engine: Optional[RAGEngine] = None


def get_rag_engine() -> RAGEngine:
    """获取全局 RAG 引擎单例"""
    global _rag_engine
    if _rag_engine is None:
        _rag_engine = RAGEngine()
    return _rag_engine
