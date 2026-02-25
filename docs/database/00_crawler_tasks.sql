CREATE TABLE `00_crawler_tasks` (
    task_id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '任务ID (对应业务中的 task_id)',
    product_url VARCHAR(500) NOT NULL COMMENT '商品链接',
    `status` TINYINT DEFAULT 0 COMMENT '任务状态: 0-等待中, 1-进行中, 2-已完成, 3-失败, 4-等待手动操作(如登录), 5-已停止',
    `resume_signal` TINYINT DEFAULT 0 COMMENT '恢复信号: 0-暂停/无动作, 1-恢复执行 (用于登录后的手动恢复), 2-停止爬虫',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='爬虫任务记录表';
