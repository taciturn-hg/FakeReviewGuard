CREATE TABLE comment_analysis (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '分析结果ID',
    raw_comment_id BIGINT NOT NULL COMMENT '关联的原始评论ID',
    task_id BIGINT NOT NULL COMMENT '关联的任务ID',
    extract TEXT COMMENT '评论内容（可冗余存储，便于独立查询）',
    label VARCHAR(50) COMMENT '标签分类（如：好评/差评/中性）',
    is_fake TINYINT(1) DEFAULT 0 COMMENT '是否为虚假评论：0-真实，1-虚假，2-疑似',
    confidence DECIMAL(3,2) COMMENT '可信度，范围0.00-1.00',
    sentiment_score DECIMAL(3,2) COMMENT '情感分数，范围-1.00到1.00，保留2位小数（通过CHECK约束限定）',
    product VARCHAR(200) COMMENT '商品名称（可冗余存储）',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '分析结果入库时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    -- 索引定义：提升外键关联和常用查询性能
    KEY idx_raw_comment_id (raw_comment_id),
    KEY idx_task_id (task_id),
    KEY idx_analysis_time (analysis_time),
    KEY idx_is_fake (is_fake),
    
    -- 外键约束
    CONSTRAINT fk_raw_comment FOREIGN KEY (raw_comment_id) 
        REFERENCES raw_comment(id) ON DELETE CASCADE,
        
    -- 数据约束
    CONSTRAINT chk_is_fake CHECK (is_fake IN (0, 1, 2)),
    CONSTRAINT chk_confidence CHECK (confidence >= 0 AND confidence <= 1),
    CONSTRAINT chk_sentiment CHECK (sentiment_score >= -1 AND sentiment_score <= 1)
    
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='评论分析结果表';
