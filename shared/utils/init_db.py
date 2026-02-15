import sys
import os
from pathlib import Path
from sqlalchemy import text

# 将项目根目录添加到 python path
current_dir = Path(__file__).resolve().parent
# current_dir 是 shared/utils，回退两层是项目根目录
project_root = current_dir.parent.parent

if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from shared.config.database import engine
from shared.utils.logger import logger

def init_tables_from_sql():
    """
    遍历 docs/database/ 目录下所有 .sql 文件并执行建表
    """
    sql_dir = project_root / "docs" / "database"
    
    if not os.path.exists(sql_dir):
        logger.error(f"找不到 SQL 目录: {sql_dir}")
        return

    # 获取所有 .sql 文件并排序（确保执行顺序，比如 01_xxx.sql, 02_xxx.sql）
    sql_files = sorted([f for f in sql_dir.iterdir() if f.suffix == '.sql'])
    
    if not sql_files:
        logger.warning(f"目录 {sql_dir} 下没有找到 .sql 文件")
        return

    logger.info(f"发现 {len(sql_files)} 个 SQL 文件，准备执行...")

    # 使用 engine.begin() 自动管理事务 (Start -> Commit/Rollback)
    try:
        with engine.begin() as connection:
            for sql_file in sql_files:
                file_path = os.path.join(sql_dir, sql_file)
                logger.info(f"正在执行文件: {sql_file}")
                
                with open(sql_file, "r", encoding="utf-8") as f:
                    sql_content = f.read()

                # 分割 SQL 语句
                statements = sql_content.split(';')
                
                for statement in statements:
                    if statement.strip():
                        try:
                            connection.execute(text(statement))
                            # 只打印第一行作为日志
                            first_line = statement.strip().splitlines()[0]
                            logger.info(f"   执行: {first_line[:50]}...") 
                        except Exception as e:
                            # 严格模式：只忽略 "表已存在" 警告，其他所有错误立即抛出以触发回滚
                            if "already exists" in str(e) or "Duplicate column name" in str(e):
                                 logger.warning(f"   跳过 (已存在): {str(e).splitlines()[0]}")
                            else:
                                 logger.error(f"   致命错误: {e}")
                                 raise e # 抛出异常，触发 engine.begin() 的自动回滚机制
                
                logger.info(f"   文件 {sql_file} 执行完毕")
        
        logger.info("所有 SQL 文件执行完毕！")
        
    except Exception as e:
        logger.error(f"初始化失败 (已自动回滚): {e}")

if __name__ == "__main__":
    init_tables_from_sql()