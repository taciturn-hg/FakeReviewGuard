CREATE TABLE comment_analysis (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '分析结果ID',
    raw_comment_id BIGINT NOT NULL COMMENT '关联的原始评论ID',
    task_id BIGINT NOT NULL COMMENT '关联的任务ID',
    extract TEXT COMMENT '评论内容（可冗余存储，便于独立查询）',
    label VARCHAR(50) COMMENT '标签分类（如：好评/差评/中性）',
    is_fake TINYINT(1) DEFAULT 0 COMMENT '是否为虚假评论：0-真实，1-虚假，2-疑似',
    confidence DECIMAL(5,4) COMMENT '可信度，范围0-1',
    sentiment_score DECIMAL(3,2) COMMENT '情感分数，范围-1到1',
    product VARCHAR(200) COMMENT '商品名称（可冗余存储）',
    analysis_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '分析时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    -- 外键约束
    CONSTRAINT fk_raw_comment FOREIGN KEY (raw_comment_id) 
        REFERENCES raw_comment(id) ON DELETE CASCADE,
    CONSTRAINT fk_task_id FOREIGN KEY (task_id) 
        REFERENCES raw_comment(task_id),
        
    -- 数据约束
    CONSTRAINT chk_is_fake CHECK (is_fake IN (0, 1, 2)),
    CONSTRAINT chk_confidence CHECK (confidence >= 0 AND confidence <= 1),
    CONSTRAINT chk_sentiment CHECK (sentiment_score >= -1 AND sentiment_score <= 1)
    
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='评论分析结果表';
