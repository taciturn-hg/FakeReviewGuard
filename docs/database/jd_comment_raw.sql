CREATE TABLE jd_comment_raw (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '原始评论ID',
    task_id BIGINT NOT NULL COMMENT '关联的任务ID',
    product VARCHAR(255) NOT NULL COMMENT '商品名称',
    extract TEXT NOT NULL COMMENT '评论内容',
    score TINYINT NOT NULL COMMENT '京东星级评分（1-5）',
    source VARCHAR(50) NOT NULL COMMENT '评论来源（如：京东网页 / 京东APP）',
    time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '评论时间',
    INDEX idx_task_id (task_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='京东商品评论原始数据表';
