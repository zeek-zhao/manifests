# PLN-20261128-013 全表头下拉与 MB 单位落地计划

| 文档编号 | PLN-20261128-013 |
| --- | --- |
| 版本 | v1.0 |
| 日期 | 2026-11-28 |
| 作者 | zeek.zhao（Agent 代笔） |
| 关联 | TSK-20261128-013 |
| 状态 | 已完成 |

## 里程碑

- **M1 数据迁移**（/tmp 临时脚本，用后即删）：「仓库大小(KB)」列头改「仓库大小(MB)」+ 131 行值 `round(x/1024,1)` + 说明行单位文字同步。
- **M2 四工具改造**：generate（REPO_COLUMNS/SNAPSHOT_REPO_ORDER 列名、load 校验正浮点）；sync（MB 直写、defaults）；stats_report（size_MB 列/图表标题/表头 DV）；catalog_to_markdown（HEADER）。validate 大改：逐列 DV 矩阵（双段 sqref）+ 下拉源 sheet 重建 + 命名区域 + 自检升级 + README_ROWS/COLUMN_DOCS 单位文案。
- **M3 重生成与验证**：迁移→normalize→stats_report→generate→catalog.md→快照；解包断言（每列 DV 含 X1 与 X3:X1000、无 showDropDown、formula1 ≤255 或命名区域定义、第 2 行不在 sqref）；WPS/Excel 双兼容机制复用 TSK-012；三重 --check；pre-commit 9 钩子。
- **M4 交付**：PR → CI → 本地 --no-ff 合并（ls-remote 核验送达后删分支）→ LOG 补录 → 汇报。

## 风险与对策

- R1 内联 255 上限截断下拉不可用：自适应机制强制超限走命名区域；_verify 断言 formula1 长度 ✓
- R2 下拉源 sheet 被 generate/load 误读：load_from_excel 仅读 repos/remotes/config ✓；normalize 四表循环不含 ✓
- R3 动态统计 DV 被 stats 下次重建清除：DV 写入 stats_report 工具内，重建即重配 ✓
- R4 MB 小数导致 generate 校验失败：校验改正浮点（含一位小数）✓
- R5 131 项 name DV 性能：区域引用无性能问题；内联列均 ≤255 ✓
