CREATE TABLE `02_comment_analysis` (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '分析结果ID',
    raw_comment_id BIGINT NOT NULL COMMENT '关联的原始评论ID',
    task_id BIGINT NOT NULL COMMENT '关联的任务ID',
    extract VARCHAR(500) COMMENT '评论内容摘要（建议仅存前200字符；完整内容请通过 JOIN raw_comment 获取）',
    label VARCHAR(50) COMMENT '标签分类（如：好评/差评/中性）',
    is_fake TINYINT(1) DEFAULT 0 COMMENT '是否为虚假评论：0-真实，1-虚假，2-疑似',
    confidence DECIMAL(3,2) COMMENT '可信度，范围0.00-1.00',
    sentiment_score DECIMAL(3,2) COMMENT '情感分数，范围-1.00到1.00，保留2位小数（通过CHECK约束限定）',
    product VARCHAR(200) COMMENT '商品名称（可冗余存储）',
    product_spec TEXT COMMENT '商品规格',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '分析结果入库时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    -- 外键约束
    CONSTRAINT fk_raw_comment FOREIGN KEY (raw_comment_id) 
        REFERENCES `01_raw_comment`(id) ON DELETE RESTRICT,
    CONSTRAINT fk_comment_task FOREIGN KEY (task_id)
        REFERENCES `00_crawler_tasks`(task_id) ON DELETE CASCADE,
        
    -- 数据约束
    CONSTRAINT chk_is_fake CHECK (is_fake IN (0, 1, 2)),
    CONSTRAINT chk_confidence CHECK (confidence >= 0 AND confidence <= 1),
    CONSTRAINT chk_sentiment CHECK (sentiment_score >= -1 AND sentiment_score <= 1),
    
    -- 显式创建索引
    INDEX idx_raw_comment_id (raw_comment_id),
    INDEX idx_task_id (task_id)
    
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='评论分析结果表';
