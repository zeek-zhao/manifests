# PLN-20261128-014 表头筛选落地计划

| 文档编号 | PLN-20261128-014 |
| --- | --- |
| 版本 | v1.0 |
| 日期 | 2026-11-28 |
| 作者 | zeek.zhao（Agent 代笔） |
| 关联 | TSK-20261128-014 |
| 状态 | 已完成 |

## 里程碑

- **M1 实施**：validate `_apply_column_dv` 去 X1 段；`_apply_formatting` 四表 auto_filter；openpyxl 层自检改「无第 1/2 行段+AF 必须存在」；stats_report 动态统计加 AF；`_sanitize` 剥 x14 extLst；`_verify` 断言反转（DV 无第 1 行段、AF 1-4 必备 A1 锚定、无 x14）。
- **M2 重生成与验证**：stats→normalize→generate→catalog.md→快照；zip 层终验（AF/DV 段/x14/showDropDown 四项）；数据零漂移确认。
- **M3 交付**：TSK/PLN/LOG-014 + GUIDE 表头交互段改写 → 9 钩子 → PR → CI → --no-ff 合并（ls-remote 核验）→ LOG 补录。

## 风险与对策

- R1 筛选菜单混入第 2 行说明文本：客户端固有限制（AutoFilter 无法跳过单行），GUIDE 注记 ✓
- R2 openpyxl 往返 x14 残留复发（sync/stats 后 normalize 前的中间态）：sanitize 在 normalize 末尾统一清理，normalize 仍是最后写入者 ✓
- R3 `--output manifests` 误用产生嵌套目录（本轮踩坑）：generate 输出路径=仓库根（plan 键含 manifests/ 前缀），LOG-014 记录正确用法 ✓
