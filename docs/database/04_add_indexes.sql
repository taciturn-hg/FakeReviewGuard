-- 为已存在的表补充索引（可重复执行；重复索引名会在 init_db 中被忽略）

ALTER TABLE `02_comment_analysis`
  ADD INDEX `idx_task_id_product_spec` (`task_id`, `product_spec`(191));

