import sys
import os
from pathlib import Path

# 将项目根目录添加到 python path
# 假设当前文件在 backend/init_db.py
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
sys.path.append(str(project_root))

from shared.utils.init_db import init_tables_from_sql

if __name__ == "__main__":
    print("开始初始化数据库...")
    init_tables_from_sql()
    print("数据库初始化完成。")
