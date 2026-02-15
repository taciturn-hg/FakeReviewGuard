from sqlalchemy.orm import Session
from backend.models.sql_models import RawComment, CrawlerTask
import uuid
import threading
import time
from shared.utils.logger import logger
from shared.config.database import SessionLocal

# 全局字典用于存储运行中的爬虫实例
# key: task_id, value: spider_instance
running_spiders = {}

# # 模拟的 Spider 类
# class JDCommentSpider:
#     def __init__(self, task_id, product_url):
#         self.task_id = task_id
#         self.product_url = product_url
#         self.status = 1 # 1: 进行中

#     def get_task_id(self):
#         return self.task_id

#     def get_status(self):
#         return self.status

#     def _update_task_status(self, db, status):
#         """更新数据库任务状态"""
#         try:
#             task = db.query(CrawlerTask).filter(CrawlerTask.task_id == self.task_id).first()
#             if task:
#                 task.status = status
#                 db.commit()
#         except Exception as e:
#             logger.error(f"更新任务状态失败: {e}")

#     def start(self):
#         """
#         模拟爬虫运行逻辑：生成假数据并入库
#         """
#         # 创建新的数据库会话，确保线程安全
#         db = SessionLocal()
#         try:
#             # 更新状态为进行中
#             self._update_task_status(db, 1)
#             logger.info(f"🕷️ 爬虫启动 TaskID={self.task_id}, URL={self.product_url}")
            
#             time.sleep(5) # 模拟网络请求耗时 (5秒)
            
#             # 模拟爬取到的数据
#             fake_comments = [
#                 {"extract": "这东西太棒了，非常好用，推荐大家购买！", "score": 5, "source": "京东APP"},
#                 {"extract": "刚收到货，包装破损，差评。", "score": 1, "source": "京东网页"},
#                 {"extract": "加微信号 abcd 返现 5 元。", "score": 5, "source": "京东APP"},
#                 {"extract": "一般般，习惯性好评。", "score": 3, "source": "京东网页"},
#                 {"extract": "物流很快，第二天就到了。", "score": 5, "source": "京东APP"}
#             ]
            
#             # 入库
#             for comment in fake_comments:
#                 db_comment = RawComment(
#                     task_id=self.task_id,
#                     original_comment_id=str(uuid.uuid4()),
#                     product="模拟商品",
#                     extract=comment["extract"],
#                     score=comment["score"],
#                     source=comment["source"]
#                 )
#                 db.add(db_comment)
            
#             # 更新状态为已完成
#             self._update_task_status(db, 2)
#             db.commit()
            
#             logger.info(f"✅ 爬虫完成 TaskID={self.task_id}, 入库 {len(fake_comments)} 条")
#             self.status = 2 # 完成
            
#         except Exception as e:
#             logger.error(f"❌ 爬虫出错: {e}")
#             db.rollback()
#             self.status = 0 # 失败
#             self._update_task_status(db, 3) # 3: 失败
#         finally:
#             db.close() # 务必关闭 session

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
        spider = JDCommentSpider(task_id=task_id, product_url=url)
        
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
            task = db.query(CrawlerTask).filter(CrawlerTask.task_id == task_id).first()
            if task:
                # 映射数据库状态到前端状态码
                # DB: 0-等待, 1-进行, 2-完成, 3-失败
                # API: 0-失败, 1-进行, 2-完成
                if task.status == 2: return 2
                if task.status == 3: return 0
                return 1 # 等待或进行中都算进行中
        except Exception:
            pass
        finally:
            db.close()
            
        return 0
