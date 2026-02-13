CREATE TABLE crawler_tasks (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '任务ID',
    product_url VARCHAR(700) NOT NULL COMMENT '商品链接',
    target_count INT COMMENT '目标爬取数量',
    actual_count INT DEFAULT 0 COMMENT '实际完成数量',
    error_message TEXT COMMENT '错误详情',
    retry_count TINYINT DEFAULT 0 COMMENT '重试次数',
    status TINYINT DEFAULT 0 COMMENT '任务状态: 0-进行中, 1-完成, 2-失败',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    finished_at DATETIME COMMENT '任务结束时间',
    UNIQUE INDEX idx_url_status (product_url, status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='爬虫任务表';
