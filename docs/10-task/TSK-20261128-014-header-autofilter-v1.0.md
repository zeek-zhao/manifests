# TSK-20261128-014 表头筛选（AutoFilter）与 x14 残留清理任务书

| 文档编号 | TSK-20261128-014 |
| --- | --- |
| 版本 | v1.0 |
| 日期 | 2026-11-28 |
| 作者 | zeek.zhao（Agent 代笔） |
| 关联 | TSK-20261128-013 / GUIDE v1.2 |
| 状态 | 已完成 |

## 1. 需求

用户澄清表头箭头诉求为**筛选交互**（AutoFilter）：自动列出列内全部去重值、点选后**隐藏不匹配行**——而非此前的 DV 填值下拉（TSK-013 把 DV 加到了第 1 行，行为不符合本意）。要求实际打开文件验证筛选可用，并全量复查。

## 2. 方案（已确认执行）

1. **表头交互切换为 AutoFilter**：repos/remotes/config/readme 四表由 normalize 设置 `auto_filter.ref=A1:<末列><末行>`；动态统计 sheet 由 stats_report 同步设置（A1:H131）。筛选菜单值列表由 Excel/WPS 客户端自动从列内去重生成，无需预定义。
2. **DV 收缩到数据区**：全部 DV sqref 从「第 1 行+第 3 行起」改为**仅第 3 行起**（X3:X1000）——表头单元格不再挂 DV，消除「DV 箭头遮挡筛选箭头」的交互冲突；数据行填值下拉保留。
3. **第 2 行说明行**：继续排除在 DV 之外；其文本会出现在筛选菜单值列表中（AutoFilter 以第 1 行为表头、第 2 行起皆视为数据，无法排除单行——已在 GUIDE 注记，属客户端固有限制）。
4. **x14 幽灵 DV 清理**（本轮复查发现的新问题）：openpyxl 清除标准 DV 后，旧 DV 的 **x14 扩展副本（extLst）残留**在 sheet XML 中，会以幽灵下拉箭头形式重现；`_sanitize` 扩展为顺带剥除含 `x14:dataValidations` 的 extLst 块，`_verify` 断言无残留。
5. 全量复查+重生成+验证+PR+合并（既有流程）。

## 3. 验收标准

- 五表 autoFilter 存在且 A1 锚定；26 个 DV 全部为 `X3:X1000` 单段，无第 1/2 行段
- 无 showDropDown、无 x14:dataValidation 残留
- 数据零漂移：manifests/、快照、catalog.md 与 main 一致（本轮为纯交互层变更）
- normalize 自检/`--excel --check`/`validate`/`catalog.md --check` 全过；pre-commit 9 钩子绿
