# PLN-20261128-007 落地计划

| # | 步骤 | 操作 | 验证 |
| --- | --- | --- | --- |
| 1 | 工具改造 | generate_manifests.py（REPO_COLUMNS 两列改名+快照 ensure_ascii=False）；sync_self_repos.py（visibility→仓库属性，public/private→公开/私有）；catalog_to_markdown.py（键/表头）；validate_manifests_xlsx.py（暗色主题+统计表重建+下拉引用+中文枚举）；.pre-commit-config.yaml（--no-ensure-ascii） | 单测性运行无语法错 |
| 2 | 数据修复与填充 | /tmp 脚本：错位修复→仓库属性 131 行→标签分类 131 行（体系统一）→validate --normalize（重建统计表/主题）→重生成 manifest/snapshot/catalog.md | 131 行两列无空值且值域合法；--check 一致 |
| 3 | 文档重组 | git mv 七类目录+加版本后缀；DSN 追加 §14 变更记录升 v1.1；新写 GUIDE-001 使用说明；README/AGENTS 更新 | 链接有效；目录符合 §2 决策 |
| 4 | 交付 | pre-commit 全绿→提交推分支→PR→CI 绿→本地 --no-ff 合规合并→删分支→LOG-007 推 main | main CI 绿；worktree clean |

回滚：任何一步失败即停，保留现场报告用户；分支删除可 restore，main 提交可 revert。
