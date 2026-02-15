import time
import threading
import sys
import os
from sqlalchemy import text

# 添加项目根目录到 sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from crawler.spiders.jd_comment_spider import JDCommentSpider
from shared.utils.init_db import init_tables_from_sql
from shared.config.database import get_db
from shared.utils.logger import logger

def simulate_backend_task(product_url):
    """
    模拟后端接收请求并启动爬虫任务
    """
    # 1. 初始化数据库表 (确保 crawler_tasks 表存在)
    logger.info("正在初始化数据库表...")
    init_tables_from_sql()
    
    # 2. 生成任务ID (模拟后端生成或使用爬虫默认)
    task_id = int(time.time())
    logger.info(f"后端生成任务ID: {task_id}")
    
    # 3. 启动爬虫 (在独立线程中运行，模拟异步任务)
    logger.info("启动爬虫线程...")
    spider_thread = threading.Thread(target=run_spider_thread, args=(product_url, task_id))
    spider_thread.start()
    
    # 4. 模拟轮询查状态
    logger.info("开始轮询任务状态...")
    monitor_task_status(task_id)
    
    # 等待爬虫线程结束
    spider_thread.join()
    logger.info("测试结束")

def run_spider_thread(url, task_id):
    """
    爬虫执行线程
    """
    try:
        spider = JDCommentSpider(url, task_id=task_id)
        spider.start()
    except Exception as e:
        logger.error(f"爬虫线程异常: {e}")

def monitor_task_status(task_id):
    """
    模拟轮询查询数据库状态
    """
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        while True:
            # 查询数据库中的任务状态
            result = db.execute(
                text("SELECT status FROM crawler_tasks WHERE task_id = :task_id"),
                {"task_id": task_id}
            ).fetchone()
            
            if result:
                status = result[0]
                status_desc = {
                    0: "等待中",
                    1: "进行中", 
                    2: "已完成", 
                    3: "失败"
                }.get(status, "未知")
                
                logger.info(f"当前任务状态: {status} ({status_desc})")
                
                if status == 2:
                    logger.info("任务已完成！停止轮询。")
                    break
                elif status == 3:
                    logger.error("任务失败！停止轮询。")
                    break
            else:
                logger.warning("未查询到任务记录 (可能尚未插入)")
            
            time.sleep(2)  # 每2秒轮询一次
            
    except Exception as e:
        logger.error(f"轮询异常: {e}")
    finally:
        # 关闭数据库连接
        try:
            next(db_gen)
        except StopIteration:
            pass

if __name__ == "__main__":
    # 测试商品链接
    test_url = 'https://item.jd.com/100012043978.html'
    simulate_backend_task(test_url)
