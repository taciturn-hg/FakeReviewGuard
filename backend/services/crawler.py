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
    def check_task_status(task_id: int):
        """
        查询任务状态
        :return: 0-失败/报错, 1-进行中, 2-已完成
        """
        # 优先查内存中的活跃爬虫
        spider = running_spiders.get(task_id)
        if spider:
            return spider.get_status()
            
        # 内存查不到，查数据库 (可能因为重启丢失了内存状态)
        # 注意：这里我们无法直接访问 db session，因为这个方法是静态的且没有传 db
        # 简易方案：临时创建一个 session
        db = SessionLocal()
        try:
            # 查询数据库中的任务状态
            task = db.query(CrawlerTask).filter(CrawlerTask.task_id == task_id).first()
            if task:
                # 映射数据库状态到前端状态码
                # DB: 0-等待, 1-进行, 2-完成, 3-失败, 4-等待登录
                # API: 0-失败, 1-进行, 2-完成, 4-等待登录
                if task.status == 2: return 2
                if task.status == 3: return 0
                if task.status == 4: return 4
                return 1 # 等待或进行中都算进行中
        except Exception:
            pass
        finally:
            db.close()
            
        return 0
