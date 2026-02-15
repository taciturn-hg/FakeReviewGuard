import uvicorn
import sys
import os
from pathlib import Path

# 将项目根目录添加到 python path
# 假设当前文件在 backend/main.py
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

# 修改：从 shared.utils.init_db 导入新的初始化函数
from shared.utils.init_db import init_tables_from_sql

# 执行数据库初始化
init_tables_from_sql()

if __name__ == "__main__":
    # 使用字符串导入，避免循环依赖，且利用 reload
    # 注意：reload 需要在项目根目录运行或正确配置 python path
    uvicorn.run(
        "backend.app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        app_dir=str(ROOT_DIR) # 指定 app 所在根目录，确保 reload 正常工作
    )
