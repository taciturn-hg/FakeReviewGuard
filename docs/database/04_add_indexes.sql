-- 为已存在的表补充索引（可重复执行；重复索引名会在 init_db 中被忽略）
-- 注意：外键列 (task_id, raw_comment_id) 的索引已在建表语句中显式创建，此处不再重复，避免冗余。

-- 02_comment_analysis
ALTER TABLE `02_comment_analysis`
  ADD INDEX `idx_created_at` (`created_at`),
  ADD INDEX `idx_is_fake` (`is_fake`),
  ADD INDEX `idx_task_id_product_spec` (`task_id`, `product_spec`(191));

-- 03_product_stats
ALTER TABLE `03_product_stats`
  ADD INDEX `idx_product` (`product`),
  ADD INDEX `idx_created_at` (`created_at`);
