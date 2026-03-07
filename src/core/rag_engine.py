"""
RAG 引擎 - 向量检索与上下文注入。
使用 ChromaDB 作为本地向量数据库。
Embedding: 本地 sentence-transformers 多语言模型（无 API 限速，支持中文）。
LLM 推理: ZhipuAI（仅用于聊天，不用于 Embedding）。

P0-4 修复: 集合名称从 ppt_shop_knowledge 更正为 pdd_shop_knowledge（匹配实际业务）
P1-2 增强: retrieve() 支持相关性阈值过滤，低相关性片段不注入 Prompt
"""

import os
import time

import chromadb
from chromadb.config import Settings as ChromaSettings

from config.settings import settings
from src.utils.logger import logger

# 本地 Embedding 模型（多语言，支持中文，384维）
EMBEDDING_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
# 引入 Rerank 重排序模型提升检索精准度
RERANK_MODEL_NAME = "BAAI/bge-reranker-base"

# P0-4: 修正集合名称，与业务一致
COLLECTION_NAME = "pdd_shop_knowledge"

# 懒加载 - 避免启动时长时间等待
_sentence_model = None
_rerank_model = None


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


def get_rerank_model():
    """获取本地 Rerank 模型（懒加载单例）"""
    global _rerank_model
    if _rerank_model is None:
        try:
            from sentence_transformers import CrossEncoder

            logger.info(f"加载本地 Rerank 模型: {RERANK_MODEL_NAME}")
            _rerank_model = CrossEncoder(RERANK_MODEL_NAME, max_length=512)
            logger.info("✅ 本地 Rerank 模型加载完成")
        except Exception as e:
            logger.error(f"❌ 本地 Rerank 模型加载失败: {e}")
            raise
    return _rerank_model


def get_local_embedding(text: str) -> list[float]:
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
    ) -> list[dict]:
        """
        语义检索（同步）：
        1. 向量粗排：获取 top_k * 3 个片段
        2. Rerank 精排：使用 CrossEncoder 进行语义打分排序
        3. 阈值过滤：剔除低相关性片段
        """
        if self._collection.count() == 0:
            logger.warning("知识库为空，跳过 RAG 检索（请先运行 python scripts/load_knowledge.py）")
            return []

        # P1-2: 使用配置项或传入的阈值
        # 默认阈值对 Rerank 分数（通常较大范围）可能需要调整，这里假设使用 sigmoid 后 0~1 的分数
        threshold = relevance_threshold if relevance_threshold is not None else settings.rag_relevance_threshold

        try:
            query_embedding = get_local_embedding(query)

            # 1. 粗排 (Recall) - 扩大召回基数
            recall_k = min(top_k * 3, self._collection.count())
            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=recall_k,
                include=["documents", "metadatas", "distances"],
                where={"deleted": "false"},  # P2-3: 排查已软删除的数据
            )

            if not results["documents"] or not results["documents"][0]:
                return []

            documents = results["documents"][0]
            metadatas = results["metadatas"][0]

            # 2. 精排 (Rerank)
            try:
                reranker = get_rerank_model()
                # 构造 (query, document) 对进行打分
                pairs = [[query, doc] for doc in documents]
                scores = reranker.predict(pairs)

                # 合并数据并根据 Rerank 分数降序排列
                ranked_results = []
                for doc, meta, score in zip(documents, metadatas, scores):
                    # 将模型原始 logits 映射到 0~1 之间 (如果不是的话可以适当处理，通常 BGE base 可以直接用)
                    # 为了兼容原有的阈值逻辑，我们可以进行归一化或直接使用
                    ranked_results.append(
                        {
                            "content": doc,
                            "source": meta.get("source", "unknown"),
                            "section": meta.get("section", ""),
                            "relevance": float(score),
                        }
                    )

                ranked_results.sort(key=lambda x: x["relevance"], reverse=True)
            except Exception as e:
                # P0-2: 降级为粗排结果时使用 warning 而非 error（非致命）
                logger.warning(f"Rerank 模型降级，退回向量粗排结果（可能是首次下载模型）: {e}")
                # 降级：使用 L2 距离转换为 0~1 相关性分数
                ranked_results = []
                for doc, meta, dist in zip(documents, metadatas, results["distances"][0]):
                    relevance = max(0.0, 1.0 - dist / 2.0)
                    ranked_results.append(
                        {
                            "content": doc,
                            "source": meta.get("source", "unknown"),
                            "section": meta.get("section", ""),
                            "relevance": round(relevance, 3),
                        }
                    )

            # 3. P0-2: 真正按阈值过滤低相关性片段，确保 rag_relevance_threshold 生效
            # BAAI/bge-reranker-base: logits 分数，> 0 通常表示相关（可配置）
            # 向量粗排降级路径: relevance 已归一化到 0~1，阈值直接适用
            final_retrieved = []
            filtered_count = 0

            for item in ranked_results:
                if len(final_retrieved) >= top_k:
                    break

                # P0-2: 实际执行阈值判断（修复前这里没有 if 判断，所有 item 都通过）
                if item["relevance"] >= threshold:
                    final_retrieved.append(item)
                else:
                    filtered_count += 1

            logger.info(
                f"RAG 混合检索 | 查询: {query[:30]}... | "
                f"粗排召回: {recall_k} 条 | 精排命中: {len(final_retrieved)} 条 | "
                f"阈值过滤: {filtered_count} 条 (threshold={threshold:.2f})"
            )
            return final_retrieved

        except Exception as e:
            logger.warning(f"RAG 检索失败，不使用知识库上下文: {e}")
            return []

    def build_context(self, retrieved_docs: list[dict]) -> str:
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

            if metadata is None:
                metadata = {}
            metadata["deleted"] = "false"  # P2-3: 写入软删除标记

            self._collection.add(ids=[doc_id], embeddings=[embedding], documents=[content], metadatas=[metadata])
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
        metadata = {"source": source, "type": "qa_pair", "timestamp": time.time(), "section": "人工实战经验"}
        return self.add_document(combined_content, metadata)

    def get_doc_count(self) -> int:
        """返回知识库中的文档数量"""
        return self._collection.count()

    def get_all_documents(self, include_deleted: bool = False):
        """获取所有知识库文档片段"""
        try:
            where_clause = None if include_deleted else {"deleted": "false"}
            return self._collection.get(where=where_clause)
        except Exception as e:
            logger.error(f"RAG 获取所有文档失败: {e}")
            return None

    def soft_delete_document(self, doc_id: str) -> bool:
        """P2-3: 软删除（更新 metadata.deleted="true"）"""
        try:
            res = self._collection.get(ids=[doc_id], include=["metadatas"])
            if not res or not res.get("ids"):
                logger.warning(f"RAG 软删除失败: 对应 ID 不存在 {doc_id}")
                return False

            metadata = res["metadatas"][0] if res["metadatas"] and res["metadatas"][0] else {}
            metadata["deleted"] = "true"
            self._collection.update(ids=[doc_id], metadatas=[metadata])
            logger.info(f"RAG 已软删除文档 | ID: {doc_id}")
            return True
        except Exception as e:
            logger.error(f"RAG 软删除异常: {doc_id} | {e}")
            return False

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
_rag_engine: RAGEngine | None = None


def get_rag_engine() -> RAGEngine:
    """获取全局 RAG 引擎单例"""
    global _rag_engine
    if _rag_engine is None:
        _rag_engine = RAGEngine()
    return _rag_engine
