CREATE TABLE `03_product_stats` (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '统计结果ID',
    task_id BIGINT NOT NULL COMMENT '关联的任务ID',
    product VARCHAR(200) COMMENT '商品名称',
    product_spec TEXT COMMENT '商品规格',
    product_url VARCHAR(500) COMMENT '商品链接',
    
    total_reviews INT DEFAULT 0 COMMENT '总评论数',
    positive_reviews_count INT DEFAULT 0 COMMENT '正面评论数',
    negative_reviews_count INT DEFAULT 0 COMMENT '负面评论数',
    neutral_reviews_count INT DEFAULT 0 COMMENT '中性评论数',
    
    positive_ratio DECIMAL(5,2) COMMENT '正面评论占比 (0-100%)',
    negative_ratio DECIMAL(5,2) COMMENT '负面评论占比 (0-100%)',
    neutral_ratio DECIMAL(5,2) COMMENT '中性评论占比 (0-100%)',
    
    fake_count INT DEFAULT 0 COMMENT '虚假评论数量',
    fake_ratio DECIMAL(5,2) COMMENT '虚假评论占比 (0-100%)',
    confidence DECIMAL(3,2) COMMENT '可信度 (0.00-1.00)',
    
    sentiment_score DECIMAL(3,2) COMMENT '平均情感分数 (-1.00 到 1.00)',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '统计时间',
    
    -- 索引
    KEY idx_task_id (task_id),
    KEY idx_product (product),
    KEY idx_created_at (created_at),

    -- 外键约束
    FOREIGN KEY (task_id) REFERENCES 00_crawler_tasks(task_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商品评论分析统计结果表';
