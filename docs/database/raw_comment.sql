CREATE TABLE raw_comment (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '原始评论ID',
    task_id BIGINT NOT NULL COMMENT '关联的任务ID',
    original_comment_id VARCHAR(255) COMMENT '平台原始评论ID',
    product TEXT NOT NULL COMMENT '商品名称',
    `extract` TEXT NOT NULL COMMENT '评论内容',
    score TINYINT NOT NULL COMMENT '星级评分（1-5）', 
    source VARCHAR(50) NOT NULL COMMENT '评论来源（如：京东网页 / 京东APP）',
    comment_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '评论时间',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '数据入库时间',
    INDEX idx_task_id (task_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商品评论原始数据表';
