# PLN-20261128-012 表头下拉根因修复落地计划

| 文档编号 | PLN-20261128-012 |
| --- | --- |
| 版本 | v1.0 |
| 日期 | 2026-11-28 |
| 作者 | zeek.zhao（Agent 代笔） |
| 关联 | TSK-20261128-012 |
| 状态 | 已完成 |

## 里程碑

- **M1 实证排查**：rw_download 最新 xlsx → openpyxl 读回 + zip 原始 XML 双源核对 DV 全部属性 → 对照实验证明 openpyxl 3.1.5 强制写出 `showDropDown="0"` → 定性 Excel/WPS 语义分歧。
- **M2 修复**：validate 新增 `_sanitize_dropdowns`（zip 剥属性）+ `_verify_dropdowns`（三断言自检）；excel-sync.yml normalize 后置于 stats_report；GUIDE 补兼容性要点。
- **M3 重生成与全量复查**：normalize→generate→catalog.md；解包断言；快照 diff；图表/行数/值域/TagCategories/orgflow-devops1 残留/维度引用集一致性；发现并清理 by-language/linux.xml stale。
- **M4 交付**：TSK/PLN/LOG-012 → 9 钩子 → PR → CI → 本地 --no-ff 合并（ls-remote 核验送达后删分支）→ LOG 补录。

## 风险与对策

- R1 zip 重写破坏 xlsx（压缩/条目顺序）：按原条目 infolist 顺序 writestr、仅改目标 XML 内容；normalize 自检+`--excel --check` 双重兜底 ✓
- R2 pre-commit 钩子（excel-check/validate-xlsx）在 CI 跑 normalize 会再剥属性：钩子本身调用 normalize/check 不写 xlsx（validate 模式只读、excel-check 只读）✓
- R3 未来新增枚举列忘走 normalize：_verify_dropdowns 仅断言 repos 表 DV；新增列建议复用 enum_columns 循环（代码内聚）✓
