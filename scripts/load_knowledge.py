"""
知识库入库脚本 - 将 data/knowledge/ 下的 Markdown 文件向量化并存入 ChromaDB。
使用本地 sentence-transformers 进行 Embedding（无 API 限速）。

运行方式（首次初始化或更新知识库时）：
    python scripts/load_knowledge.py
"""

import os
import sys
import time

# 添加项目根目录
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chromadb
from chromadb.config import Settings as ChromaSettings

from config.settings import settings
from src.utils.logger import logger

# 确保日志目录
os.makedirs("logs", exist_ok=True)
os.makedirs("data/chroma", exist_ok=True)
os.makedirs("data/sqlite", exist_ok=True)

KNOWLEDGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "knowledge")
EMBEDDING_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"


def load_embedding_model():
    """加载本地 Embedding 模型"""
    from sentence_transformers import SentenceTransformer

    logger.info(f"加载本地 Embedding 模型: {EMBEDDING_MODEL_NAME}")
    logger.info("（首次运行会自动下载 ~120MB 模型文件，请稍候...）")
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    logger.info("✅ 模型加载完成")
    return model


def get_local_embedding(model, text: str) -> list[float]:
    """将文本转为向量（本地，无限速）"""
    embedding = model.encode(text[:512], show_progress_bar=False)
    return embedding.tolist()


def _sliding_window_split(text: str, meta: dict, max_chars: int = 300, step: int = 100) -> list[tuple[str, dict]]:
    """P3-4: 滑动窗口切分超长段落"""
    if len(text) <= max_chars + 100:  # 留 100 字的宽限，不用强行切
        return [(text, meta)]

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        chunk_text = text[start:end]
        # 补充切分标记到 meta
        chunk_meta = meta.copy()
        if start > 0 or end < len(text):
            chunk_meta["is_split"] = True
        chunks.append((chunk_text, chunk_meta))
        start += step
    return chunks


def chunk_markdown(content: str, source_file: str) -> list[tuple[str, dict]]:
    """
    将 Markdown 文件按"## 二级标题"切分为知识片段（Chunk）。
    每个 Chunk 是一个完整的知识点，提升检索精度。
    """
    chunks = []
    lines = content.split("\n")
    current_section = "概述"
    current_h1 = ""
    current_lines = []

    for line in lines:
        if line.startswith("# ") and not line.startswith("## "):
            if current_lines:
                text = "\n".join(current_lines).strip()
                if len(text) > 30:
                    base_meta = {"source": source_file, "section": current_section, "h1": current_h1}
                    chunks.extend(_sliding_window_split(text, base_meta))
            current_h1 = line.lstrip("# ").strip()
            current_lines = [line]
            current_section = current_h1
        elif line.startswith("## "):
            if current_lines:
                text = "\n".join(current_lines).strip()
                if len(text) > 30:
                    base_meta = {"source": source_file, "section": current_section, "h1": current_h1}
                    chunks.extend(_sliding_window_split(text, base_meta))
            current_section = line.lstrip("# ").strip()
            current_lines = [line]
        else:
            current_lines.append(line)

    if current_lines:
        text = "\n".join(current_lines).strip()
        if len(text) > 30:
            base_meta = {"source": source_file, "section": current_section, "h1": current_h1}
            chunks.extend(_sliding_window_split(text, base_meta))

    return chunks


def load_all_knowledge(dry_run: bool = False):
    """扫描知识库目录，向量化所有 .md 文件并存入 ChromaDB"""
    # 加载本地 Embedding 模型
    model = load_embedding_model()

    # 导入统一的集合名称，确保与 RAGEngine 保持一致
    from src.core.rag_engine import COLLECTION_NAME

    logger.info(f"使用集合名称: {COLLECTION_NAME}")

    # 初始化 ChromaDB
    db_path = os.path.abspath(settings.chroma_db_dir)
    os.makedirs(db_path, exist_ok=True)

    client = chromadb.PersistentClient(
        path=db_path,
        settings=ChromaSettings(anonymized_telemetry=False),
    )

    # 清空并重建集合（幂等操作）
    try:
        client.delete_collection(COLLECTION_NAME)
        logger.info(f"已清空旧知识库集合 [{COLLECTION_NAME}]，开始重新入库...")
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"description": "PDD店铺知识库"},
    )

    # 扫描知识库目录
    if not os.path.exists(KNOWLEDGE_DIR):
        logger.error(f"知识库目录不存在: {KNOWLEDGE_DIR}")
        return

    md_files = [f for f in os.listdir(KNOWLEDGE_DIR) if f.endswith(".md")]
    if not md_files:
        logger.warning(f"知识库目录下没有 .md 文件: {KNOWLEDGE_DIR}")
        return

    total_chunks = 0
    t0 = time.time()

    for filename in sorted(md_files):
        filepath = os.path.join(KNOWLEDGE_DIR, filename)
        with open(filepath, encoding="utf-8") as f:
            content = f.read()

        chunks = chunk_markdown(content, filename)
        logger.info(f"处理文件: {filename} | 切分出 {len(chunks)} 个知识片段")

        ids = []
        embeddings = []
        documents = []
        metadatas = []

        for i, (text, meta) in enumerate(chunks):
            doc_id = f"{filename}_{i:03d}"
            embedding = get_local_embedding(model, text)
            ids.append(doc_id)
            embeddings.append(embedding)
            documents.append(text)
            metadatas.append(meta)
            total_chunks += 1
            logger.debug(f"  向量化: {doc_id} | {meta['section'][:40]}")

        # 批量存入 ChromaDB
        if ids and not dry_run:
            collection.add(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)
            logger.info(f"  ✅ {len(ids)} 个片段已存入 ChromaDB")
        elif dry_run:
            logger.info(f"  👀 [Dry Run] {len(ids)} 个片段准备就绪，跳过写入数据库")

    elapsed = time.time() - t0
    logger.info(f"\n{'=' * 50}")
    logger.info("🎉 知识库入库完成！")
    logger.info(f"   文件数: {len(md_files)} | 片段数: {total_chunks} | 耗时: {elapsed:.1f}s")
    logger.info(f"   数据库路径: {db_path}")
    logger.info(f"   ChromaDB 总记录: {collection.count()}")
    logger.info(f"{'=' * 50}")

    # 快速检索验证
    print("\n🔍 快速检索验证...")
    test_queries = ["PPT多少钱", "多久能做好", "下单流程"]
    for q in test_queries:
        emb = get_local_embedding(model, q)
        results = collection.query(query_embeddings=[emb], n_results=1, include=["documents", "metadatas"])
        doc = results["documents"][0][0][:80] if results["documents"][0] else "无结果"
        section = results["metadatas"][0][0].get("section", "") if results["metadatas"][0] else ""
        print(f"  Q: {q!r:20s} → [{section}] {doc}...")


if __name__ == "__main__":
    is_dry_run = "--dry-run" in sys.argv
    if is_dry_run:
        logger.info("=== 启动 Dry Run 模式 (不写入数据库) ===")
    load_all_knowledge(dry_run=is_dry_run)
