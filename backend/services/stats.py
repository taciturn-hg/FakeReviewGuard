from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.models.sql_models import CommentAnalysis, ProductStats, CrawlerTask
from shared.utils.logger import logger

class StatsService:
    @staticmethod
    def calculate_stats(task_id: int, db: Session):
        """
        根据 CommentAnalysis 表的结果，计算统计数据并存入 ProductStats
        """
        try:
            # 获取 URL
            product_url = None
            task_info = db.query(CrawlerTask).filter(CrawlerTask.task_id == task_id).first()
            if task_info:
                product_url = task_info.product_url

            # 1. 查询基础数据
            stats = db.query(
                func.count(CommentAnalysis.id).label("total"),
                func.sum(CommentAnalysis.is_fake).label("fake_sum"), 
                func.avg(CommentAnalysis.sentiment_score).label("sentiment_avg")
            ).filter(CommentAnalysis.task_id == task_id).first()
            
            if not stats or stats.total == 0:
                logger.warning(f"任务 {task_id} 没有分析结果，无法统计")
                return None

            # 2. 计算正面/负面/中性评论数
            # 统一逻辑：> 0.2 正面, < -0.2 负面, 否则中性
            positive_count = db.query(CommentAnalysis).filter(
                CommentAnalysis.task_id == task_id, 
                CommentAnalysis.sentiment_score > 0.2
            ).count()
            
            negative_count = db.query(CommentAnalysis).filter(
                CommentAnalysis.task_id == task_id, 
                CommentAnalysis.sentiment_score < -0.2
            ).count()
            
            neutral_count = db.query(CommentAnalysis).filter(
                CommentAnalysis.task_id == task_id, 
                CommentAnalysis.sentiment_score >= -0.2,
                CommentAnalysis.sentiment_score <= 0.2
            ).count()

            # 3. 计算比率
            total = stats.total
            fake_count = int(stats.fake_sum or 0)
            if total > 0:
                fake_ratio = round((fake_count / total) * 100, 2)
                trust_score = max(0, int(100 - fake_ratio))
                
                positive_ratio = round((positive_count / total) * 100, 2)
                negative_ratio = round((negative_count / total) * 100, 2)
                neutral_ratio = round((neutral_count / total) * 100, 2)
            else:
                fake_ratio = 0.0
                trust_score = 0
                positive_ratio = 0.0
                negative_ratio = 0.0
                neutral_ratio = 0.0
                
            sentiment_score = round(float(stats.sentiment_avg or 0), 2)
            
            # 获取商品名称
            first_record = db.query(CommentAnalysis).filter(CommentAnalysis.task_id == task_id).first()
            product_name = first_record.product if first_record else "未知商品"

            # 4. 创建或更新 ProductStats
            existing_stats = db.query(ProductStats).filter(ProductStats.task_id == task_id).first()
            
            if existing_stats:
                # 更新
                existing_stats.total_reviews = total
                existing_stats.fake_count = fake_count
                existing_stats.fake_ratio = fake_ratio
                existing_stats.trust_score = trust_score
                existing_stats.sentiment_score = sentiment_score
                existing_stats.positive_reviews_count = positive_count
                existing_stats.negative_reviews_count = negative_count
                existing_stats.neutral_reviews_count = neutral_count
                
                existing_stats.positive_ratio = positive_ratio
                existing_stats.negative_ratio = negative_ratio
                existing_stats.neutral_ratio = neutral_ratio
                
                if product_url:
                    existing_stats.product_url = product_url
                
                logger.info(f"更新任务 {task_id} 的统计结果")
                db_stats = existing_stats
            else:
                # 新增
                db_stats = ProductStats(
                    task_id=task_id,
                    product=product_name,
                    product_url=product_url,
                    total_reviews=total,
                    fake_count=fake_count,
                    fake_ratio=fake_ratio,
                    trust_score=trust_score,
                    sentiment_score=sentiment_score,
                    positive_reviews_count=positive_count,
                    negative_reviews_count=negative_count,
                    neutral_reviews_count=neutral_count,
                    
                    positive_ratio=positive_ratio,
                    negative_ratio=negative_ratio,
                    neutral_ratio=neutral_ratio
                )
                db.add(db_stats)
                logger.info(f"创建任务 {task_id} 的统计结果")
            
            db.commit()
            db.refresh(db_stats)
            return db_stats
            
        except Exception as e:
            logger.error(f"计算统计结果失败: {e}")
            db.rollback()
            return None