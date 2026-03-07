import os
import sys

import uvicorn

# 确保能找到项目模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("🚀 正在启动 PDD AI 生产流水线服务器...")
    print("🔗 启动后请访问: http://localhost:8100/")

    # 强制创建必要目录
    os.makedirs("logs", exist_ok=True)
    os.makedirs("data/sqlite", exist_ok=True)
    os.makedirs("data/chroma", exist_ok=True)
    os.makedirs("templates", exist_ok=True)
    os.makedirs("static", exist_ok=True)

    try:
        uvicorn.run("main:app", host="0.0.0.0", port=8100, reload=False, log_level="info")
    except Exception as e:
        print(f"❌ 服务器崩溃: {e}")
        with open("logs/crash.log", "a") as f:
            f.write(f"\nCRASH: {str(e)}\n")
