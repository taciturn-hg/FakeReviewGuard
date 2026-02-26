from sqlalchemy.orm import Session
from backend.models.sql_models import CrawlerTask
import threading
from shared.utils.logger import logger
from shared.config.database import SessionLocal
# 引入真实爬虫
from crawler.spiders.jd_comment_spider import JDCommentSpider

# 全局字典用于存储运行中的爬虫实例
# key: task_id, value: spider_instance
running_spiders = {}

class CrawlerService:
    @staticmethod
    def start_crawl_task(url: str, db: Session) -> int:
        """
        异步启动爬虫任务
        :return: task_id
        """
        # 1. 创建任务记录，获取 task_id
        task = CrawlerTask(product_url=url, status=0)
        db.add(task)
        db.commit()
        db.refresh(task)
        
        task_id = task.task_id
        logger.info(f"创建新任务 TaskID={task_id}")
        
        # 2. 初始化爬虫实例
        # 真实 JDCommentSpider 的参数顺序是 (product_url, db=None, task_id=None)
        # 注意：如果不传 db，爬虫内部会尝试自己连接，或者我们在这里传入一个新的 session
        # 为了线程安全，最好让爬虫自己管理 session 或者传入一个新的 session
        # 这里我们传入 task_id 和 url
        spider = JDCommentSpider(product_url=url, task_id=task_id)
        
        # 3. 存储实例引用 (以便后续查询状态)
        running_spiders[task_id] = spider
        
        # 4. 异步启动爬取 (使用线程)
        thread = threading.Thread(target=spider.start)
        thread.daemon = True # 设置为守护线程
        thread.start()
        
        return task_id

    @staticmethod
    def _map_db_status_to_api_status(db_status: int) -> int:
        """
        将数据库状态码映射为 API 状态码
        DB Status:
            0: 等待中
            1: 进行中
            2: 已完成
            3: 失败
            4: 等待登录
            5: 已停止
        
        API Status (前端约定):
            0: 失败/报错
            1: 进行中
            2: 已完成
            3: 分析完成
            4: 等待登录
        """
        if db_status == 2: return 2  # 完成
        if db_status == 3: return 0  # 失败
        if db_status == 4: return 4  # 等待登录
        if db_status == 5: return 0  # 停止视为失败/结束
        return 1  # 0(等待) 和 1(进行) 都映射为进行中

    @staticmethod
    def check_task_status(task_id: int):
        """
        查询任务状态
        :return: API 状态码
        """
        # 优先查内存中的活跃爬虫
        spider = running_spiders.get(task_id)
        if spider:
            # 内存中的 spider.status 通常也是 DB 状态码 (因为 spider 会更新 DB)
            # 但为了安全起见，这里也应用映射
            return CrawlerService._map_db_status_to_api_status(spider.get_status())
            
        # 内存查不到，查数据库 (可能因为重启丢失了内存状态)
        db = SessionLocal()
        try:
            # 查询数据库中的任务状态
            task = db.query(CrawlerTask).filter(CrawlerTask.task_id == task_id).first()
            if task:
                return CrawlerService._map_db_status_to_api_status(task.status)
        except Exception:
            pass
        finally:
            db.close()
            
        return 0
