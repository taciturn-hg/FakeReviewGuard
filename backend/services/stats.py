from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.models.sql_models import CommentAnalysis, ProductStats, CrawlerTask
from shared.utils.logger import logger

class StatsService:
    @staticmethod
    def calculate_stats(task_id: int, db: Session):
        """
        根据 CommentAnalysis 表的结果，计算统计数据并存入 ProductStats
        分别计算：
        1. 总体统计 (product_spec = None)
        2. 各个规格的统计 (product_spec = '具体的规格')
        """
        try:
            # 获取 URL
            product_url = None
            task_info = db.query(CrawlerTask).filter(CrawlerTask.task_id == task_id).first()
            if task_info:
                product_url = task_info.product_url

            # 获取商品名称 (取第一条有值的)
            first_record = db.query(CommentAnalysis).filter(CommentAnalysis.task_id == task_id).first()
            product_name = first_record.product if first_record else "未知商品"

            # 1. 获取所有不重复的规格（不包含 NULL/空字符串）
            # 使用 GROUP BY 更利于走 (task_id, product_spec) 联合索引，避免 DISTINCT 触发额外的 filesort
            specs_query = (
                db.query(CommentAnalysis.product_spec)
                .filter(
                    CommentAnalysis.task_id == task_id,
                    CommentAnalysis.product_spec.isnot(None),
                    CommentAnalysis.product_spec != "",
                )
                .group_by(CommentAnalysis.product_spec)
                .all()
            )
            
            # 清理旧数据：删除该任务ID下的所有统计数据，重新计算
            # 注意：删除操作与后续插入必须在同一事务中，避免中途失败导致数据被清空却未写入新统计
            db.query(ProductStats).filter(ProductStats.task_id == task_id).delete()

            created_stats = []

            # --- 1. 计算总体统计 (Overall) ---
            overall_stat = StatsService._calculate_single_group(db, task_id, None, is_overall=True)
            if overall_stat:
                overall_stat.product = product_name
                overall_stat.product_url = product_url
                db.add(overall_stat)
                created_stats.append(overall_stat)

            # --- 2. 计算各规格统计 ---
            # 提取具体的规格字符串列表
            spec_list = [s[0] for s in specs_query if s[0]]
            
            for spec in spec_list:
                spec_stat = StatsService._calculate_single_group(db, task_id, spec, is_overall=False)
                if spec_stat:
                    spec_stat.product = product_name
                    spec_stat.product_url = product_url
                    db.add(spec_stat)
                    created_stats.append(spec_stat)

            db.commit()
            
            # 返回总体统计数据用于 API 响应 (如果有的话)
            # 如果没有总体数据，返回列表中的第一个
            for stat in created_stats:
                db.refresh(stat)
                
            return created_stats[0] if created_stats else None
            
        except Exception as e:
            logger.error(f"计算统计结果失败: {e}")
            db.rollback()
            return None

    @staticmethod
    def _calculate_single_group(db: Session, task_id: int, spec: str, is_overall: bool):
        """
        内部辅助方法：计算单个分组的统计数据
        :param spec: 规格名称。如果 is_overall 为 True，则忽略此参数计算全部。
        """
        # 构建基础查询
        base_query = db.query(CommentAnalysis).filter(CommentAnalysis.task_id == task_id)
        
        # 如果不是总体统计，则增加规格过滤
        if not is_overall:
            base_query = base_query.filter(CommentAnalysis.product_spec == spec)

        # 1. 查询基础聚合数据
        stats = base_query.with_entities(
            func.count(CommentAnalysis.id).label("total"),
            func.sum(CommentAnalysis.is_fake).label("fake_sum"), 
            func.avg(CommentAnalysis.sentiment_score).label("sentiment_avg"),
            func.avg(CommentAnalysis.confidence).label("confidence_avg")
        ).first()
        
        if not stats or stats.total == 0:
            return None

        # 2. 计算正面/负面/中性评论数
        # 复用 base_query 的过滤条件
        positive_count = base_query.filter(CommentAnalysis.sentiment_score > 0.2).count()
        negative_count = base_query.filter(CommentAnalysis.sentiment_score < -0.2).count()
        neutral_count = base_query.filter(
            CommentAnalysis.sentiment_score >= -0.2,
            CommentAnalysis.sentiment_score <= 0.2
        ).count()

        # 3. 计算比率
        total = stats.total or 0
        fake_count = int(stats.fake_sum or 0)
        confidence_val = float(stats.confidence_avg or 0)
        
        fake_ratio = 0.0
        confidence = 0.0
        positive_ratio = 0.0
        negative_ratio = 0.0
        neutral_ratio = 0.0
        
        if total > 0:
            fake_ratio = round((fake_count / total) * 100, 2)
            confidence = round(confidence_val, 2)
            positive_ratio = round((positive_count / total) * 100, 2)
            negative_ratio = round((negative_count / total) * 100, 2)
            neutral_ratio = round((neutral_count / total) * 100, 2)
            
        sentiment_score = round(float(stats.sentiment_avg or 0), 2)

        # 4. 创建 ProductStats 对象
        # 如果是总体统计，product_spec 存为 None (或者 'ALL'，这里用 None 保持数据库语义)
        # 如果是规格统计，product_spec 存为具体的 spec
        db_spec_value = None if is_overall else spec

        return ProductStats(
            task_id=task_id,
            product_spec=db_spec_value,
            total_reviews=total,
            fake_count=fake_count,
            fake_ratio=fake_ratio,
            confidence=confidence,
            sentiment_score=sentiment_score,
            positive_reviews_count=positive_count,
            negative_reviews_count=negative_count,
            neutral_reviews_count=neutral_count,
            positive_ratio=positive_ratio,
            negative_ratio=negative_ratio,
            neutral_ratio=neutral_ratio
        )
