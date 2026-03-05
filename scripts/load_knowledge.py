"""
知识库入库脚本 - 将 data/knowledge/ 下的 Markdown 文件向量化并存入 ChromaDB。
使用本地 sentence-transformers 进行 Embedding（无 API 限速）。

运行方式（首次初始化或更新知识库时）：
    python scripts/load_knowledge.py
"""
import asyncio
import os
import sys
import time
from typing import List, Tuple

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


def get_local_embedding(model, text: str) -> List[float]:
    """将文本转为向量（本地，无限速）"""
    embedding = model.encode(text[:512], show_progress_bar=False)
    return embedding.tolist()


def chunk_markdown(content: str, source_file: str) -> List[Tuple[str, dict]]:
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
                    chunks.append((text, {"source": source_file, "section": current_section, "h1": current_h1}))
            current_h1 = line.lstrip("# ").strip()
            current_lines = [line]
            current_section = current_h1
        elif line.startswith("## "):
            if current_lines:
                text = "\n".join(current_lines).strip()
                if len(text) > 30:
                    chunks.append((text, {"source": source_file, "section": current_section, "h1": current_h1}))
            current_section = line.lstrip("# ").strip()
            current_lines = [line]
        else:
            current_lines.append(line)

    if current_lines:
        text = "\n".join(current_lines).strip()
        if len(text) > 30:
            chunks.append((text, {"source": source_file, "section": current_section, "h1": current_h1}))

    return chunks


def load_all_knowledge():
    """扫描知识库目录，向量化所有 .md 文件并存入 ChromaDB"""
    # 加载本地 Embedding 模型
    model = load_embedding_model()

    # 初始化 ChromaDB
    db_path = os.path.abspath(settings.chroma_db_dir)
    os.makedirs(db_path, exist_ok=True)

    client = chromadb.PersistentClient(
        path=db_path,
        settings=ChromaSettings(anonymized_telemetry=False),
    )

    # 清空并重建集合
    try:
        client.delete_collection("ppt_shop_knowledge")
        logger.info("已清空旧知识库，重新入库...")
    except Exception:
        pass

    collection = client.create_collection(
        name="ppt_shop_knowledge",
        metadata={"description": "PPT设计店铺知识库"},
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
        with open(filepath, "r", encoding="utf-8") as f:
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
        if ids:
            collection.add(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)
            logger.info(f"  ✅ {len(ids)} 个片段已存入 ChromaDB")

    elapsed = time.time() - t0
    logger.info(f"\n{'='*50}")
    logger.info(f"🎉 知识库入库完成！")
    logger.info(f"   文件数: {len(md_files)} | 片段数: {total_chunks} | 耗时: {elapsed:.1f}s")
    logger.info(f"   数据库路径: {db_path}")
    logger.info(f"   ChromaDB 总记录: {collection.count()}")
    logger.info(f"{'='*50}")

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
    load_all_knowledge()
