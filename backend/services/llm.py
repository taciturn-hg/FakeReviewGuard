from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.models.sql_models import RawComment, CommentAnalysis, ProductStats
from ml_models.inference.predict import FakeReviewPredictor
from shared.utils.logger import logger

# 初始化模型 (单例模式，避免重复加载)
predictor = FakeReviewPredictor()

class LLMService:
    @staticmethod
    def analyze_single_text(text: str) -> dict:
        """
        分析单条评论文本
        """
        prediction = predictor.predict(text)
        
        # 构造更友好的分析文本
        is_fake_cn = "虚假评论" if prediction["is_fake"] else "真实评论"
        sentiment_val = prediction.get("sentiment_score", 0)
        sentiment_cn = "正面" if sentiment_val > 0.2 else "负面" if sentiment_val < -0.2 else "中性"
        
        return {
            "is_fake": 1 if prediction["is_fake"] else 0,
            "label": prediction["label"], # "FAKE" or "REAL"
            "confidence": round(prediction["confidence"], 4),
            "sentiment_score": round(sentiment_val, 4),
            "analysis": f"模型判定为【{is_fake_cn}】。情感倾向为【{sentiment_cn}】。"
        }

    @staticmethod
    def analyze_task(task_id: int, db: Session) -> bool:
        """
        根据 task_id 获取评论，分批调用模型分析，存入数据库
        返回: 是否分析完成
        """
        try:
            logger.info(f"开始分析任务 TaskID={task_id}")
            
            # 1. 从数据库读取该任务的所有评论
            # 更新查询语句中的表名引用，使用新的01_raw_comment格式
            comments = db.query(RawComment).filter(RawComment.task_id == task_id).all()
            total_comments = len(comments)
            logger.info(f"任务 {task_id} 共有 {total_comments} 条评论待分析")
            
            if total_comments == 0:
                logger.warning(f"任务 {task_id} 没有找到任何评论，跳过分析")
                return True

            batch_size = 10
            
            # 2. 分批处理
            for i in range(0, total_comments, batch_size):
                batch = comments[i : i + batch_size]
                batch_results = []
                
                try:
                    # 2.1 分析当前批次
                    for item in batch:
                        prediction = predictor.predict(item.extract)
                        
                        result_entry = {
                            "raw_comment_id": item.id,
                            "task_id": task_id,
                            "is_fake": 1 if prediction["is_fake"] else 0,
                            "label": prediction["label"],
                            "extract": item.extract[:500],
                            "confidence": round(prediction["confidence"], 4),
                            "sentiment_score": round(prediction["sentiment_score"], 4),
                            "product": item.product,
                            "product_spec": item.product_spec
                        }
                        batch_results.append(result_entry)
                    
                    # 2.2 将 batch_results 存入 analysis_results 表
                    if batch_results:
                        # 2.2.1 批量插入分析结果
                        db.bulk_insert_mappings(CommentAnalysis, batch_results)
                        db.commit()
                    
                    logger.info(f"任务 {task_id}: 已完成批次 {i//batch_size + 1}, 本批数量: {len(batch)}, 进度: {min(i+batch_size, total_comments)}/{total_comments}")
                    
                except Exception as batch_error:
                    logger.error(f"任务 {task_id} 在处理批次 {i//batch_size + 1} 时出错: {batch_error}")
                    db.rollback() # 回滚当前批次
                    # 继续处理下一个批次，还是直接中断？这里选择中断，因为数据库可能已经乱了
                    raise batch_error

            logger.info(f"任务 {task_id} 分析全部完成！")
            return True
            
        except Exception as e:
            logger.error(f"任务 {task_id} 分析失败: {e}")
            return False
