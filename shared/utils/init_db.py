import sys
import os
from sqlalchemy import text

# 将项目根目录添加到 python path
current_dir = os.path.dirname(os.path.abspath(__file__))
# current_dir 是 shared/utils，回退两层是项目根目录
project_root = os.path.dirname(os.path.dirname(current_dir))

if project_root not in sys.path:
    sys.path.append(project_root)

from shared.config.database import engine

def init_tables_from_sql():
    """
    遍历 docs/sql/ 目录下所有 .sql 文件并执行建表
    """
    sql_dir = os.path.join(project_root, "docs", "sql")
    
    if not os.path.exists(sql_dir):
        print(f"❌ 找不到 SQL 目录: {sql_dir}")
        return

    # 获取所有 .sql 文件并排序（确保执行顺序，比如 01_xxx.sql, 02_xxx.sql）
    sql_files = sorted([f for f in os.listdir(sql_dir) if f.endswith('.sql')])
    
    if not sql_files:
        print(f"⚠️ 目录 {sql_dir} 下没有找到 .sql 文件")
        return

    print(f"📂 发现 {len(sql_files)} 个 SQL 文件，准备执行...")

    # 使用 engine.begin() 自动管理事务 (Start -> Commit/Rollback)
    try:
        with engine.begin() as connection:
            for sql_file in sql_files:
                file_path = os.path.join(sql_dir, sql_file)
                print(f"\n📄 正在执行文件: {sql_file}")
                
                with open(file_path, "r", encoding="utf-8") as f:
                    sql_content = f.read()

                # 分割 SQL 语句
                statements = sql_content.split(';')
                
                for statement in statements:
                    if statement.strip():
                        try:
                            connection.execute(text(statement))
                            # 只打印第一行作为日志
                            first_line = statement.strip().splitlines()[0]
                            print(f"   ✅ 执行: {first_line[:50]}...") 
                        except Exception as e:
                            # 忽略 "表已存在" 警告
                            if "already exists" not in str(e):
                                 print(f"   ⚠️ 警告: {e}")
                                 # 注意：在 begin() 模式下，严重错误会导致整个事务回滚
                                 # 但 "表已存在" 通常是可以接受的非致命错误
                
                print(f"   ✨ 文件 {sql_file} 执行完毕")
        
        print("\n🎉 所有 SQL 文件执行完毕！")
        
    except Exception as e:
        print(f"\n❌ 初始化失败 (已自动回滚): {e}")

if __name__ == "__main__":
    init_tables_from_sql()