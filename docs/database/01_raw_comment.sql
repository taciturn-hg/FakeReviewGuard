CREATE TABLE `01_raw_comment` (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '原始评论ID',
    task_id BIGINT NOT NULL COMMENT '关联的任务ID',
    original_comment_id VARCHAR(255) COMMENT '平台原始评论ID',
    original_product_id VARCHAR(255) COMMENT '平台原始商品ID',
    product TEXT NOT NULL COMMENT '商品名称',
    product_spec TEXT COMMENT '商品规格',
    extract TEXT NOT NULL COMMENT '评论内容',
    score TINYINT NOT NULL COMMENT '星级评分（1-5）', 
    source VARCHAR(50) NOT NULL COMMENT '评论来源（如：京东网页 / 京东APP）',
    comment_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '评论时间',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '数据入库时间',

    -- 依赖任务表
    CONSTRAINT fk_raw_comment_task FOREIGN KEY (task_id)
        REFERENCES `00_crawler_tasks`(task_id) ON DELETE CASCADE,
        
    -- 显式创建外键索引 (避免隐式创建导致不可控)
    INDEX idx_task_id (task_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商品评论原始数据表';
