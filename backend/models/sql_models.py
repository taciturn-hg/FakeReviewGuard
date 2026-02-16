from sqlalchemy import Column, Integer, String, Text, DateTime, CheckConstraint, Index, ForeignKey, Boolean, DECIMAL
from sqlalchemy.orm import relationship
from datetime import datetime
from shared.config.database import Base

class CrawlerTask(Base):
    __tablename__ = "00_crawler_tasks"

    task_id = Column(Integer, primary_key=True, autoincrement=True, comment="任务ID")
    product_url = Column(String(500), nullable=False, comment="商品链接")
    status = Column(Integer, default=0, comment="任务状态: 0-等待中, 1-进行中, 2-已完成, 3-失败")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

class RawComment(Base):
    __tablename__ = "01_raw_comment"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="原始评论ID")
    task_id = Column(Integer, nullable=False, index=True, comment="关联的任务ID")
    original_comment_id = Column(String(255), comment="平台原始评论ID")
    product = Column(Text, nullable=False, comment="商品名称")
    extract = Column(Text, nullable=False, comment="评论内容")
    score = Column(Integer, nullable=False, comment="星级评分（1-5）")
    source = Column(String(50), nullable=False, comment="评论来源（如：京东网页 / 京东APP）")
    comment_time = Column(DateTime, default=datetime.now, comment="评论时间")
    created_at = Column(DateTime, default=datetime.now, comment="数据入库时间")

    # 建立与 CommentAnalysis 的反向关系
    analysis = relationship("CommentAnalysis", back_populates="raw_comment", uselist=False)

    __table_args__ = (
        CheckConstraint('score BETWEEN 1 AND 5', name='check_score_range'),
        Index('idx_task_id', 'task_id'),
    )

class CommentAnalysis(Base):
    __tablename__ = "02_comment_analysis"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="分析结果ID")
    raw_comment_id = Column(Integer, ForeignKey("01_raw_comment.id"), nullable=False, comment="关联的原始评论ID")
    task_id = Column(Integer, nullable=False, comment="关联的任务ID")
    extract = Column(String(500), comment="评论内容摘要")
    label = Column(String(50), comment="标签分类")
    is_fake = Column(Integer, default=0, comment="是否为虚假评论：0-真实，1-虚假，2-疑似")
    confidence = Column(DECIMAL(3, 2), comment="可信度")
    sentiment_score = Column(DECIMAL(3, 2), comment="情感分数")
    product = Column(String(200), comment="商品名称")
    created_at = Column(DateTime, default=datetime.now, comment="分析结果入库时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    # 建立与 RawComment 的关系
    raw_comment = relationship("RawComment", back_populates="analysis")

    __table_args__ = (
        CheckConstraint('is_fake IN (0, 1, 2)', name='chk_is_fake'),
        CheckConstraint('confidence >= 0 AND confidence <= 1', name='chk_confidence'),
        CheckConstraint('sentiment_score >= -1 AND sentiment_score <= 1', name='chk_sentiment'),
        Index('idx_raw_comment_id', 'raw_comment_id'),
        Index('idx_task_id', 'task_id'),
        Index('idx_created_at', 'created_at'),
        Index('idx_is_fake', 'is_fake'),
    )

class ProductStats(Base):
    __tablename__ = "03_product_stats"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="统计结果ID")
    task_id = Column(Integer, nullable=False, index=True, comment="关联的任务ID")
    product = Column(String(200), index=True, comment="商品名称")
    product_url = Column(String(500), comment="商品链接")
    
    total_reviews = Column(Integer, default=0, comment="总评论数")
    positive_reviews_count = Column(Integer, default=0, comment="正面评论数")
    negative_reviews_count = Column(Integer, default=0, comment="负面评论数")
    neutral_reviews_count = Column(Integer, default=0, comment="中性评论数")
    
    positive_ratio = Column(DECIMAL(5, 2), comment="正面评论占比")
    negative_ratio = Column(DECIMAL(5, 2), comment="负面评论占比")
    neutral_ratio = Column(DECIMAL(5, 2), comment="中性评论占比")
    
    fake_count = Column(Integer, default=0, comment="虚假评论数量")
    fake_ratio = Column(DECIMAL(5, 2), comment="虚假评论占比")
    confidence = Column(DECIMAL(3, 2), comment="可信度 (0.00-1.00)")
    
    sentiment_score = Column(DECIMAL(3, 2), comment="平均情感分数")
    
    created_at = Column(DateTime, default=datetime.now, comment="统计时间")
