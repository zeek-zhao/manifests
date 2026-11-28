# PLN-20261128-008 groups-visibility-guide-rev 落地计划

| 文档编号 | PLN-20261128-008 |
| --- | --- |
| 版本 | v1.0 |
| 日期 | 2026-11-28 |
| 编制 | zeek.zhao（Agent 代笔） |
| 状态 | 执行中 |
| 关联 | TSK-20261128-008 |

## 里程碑与任务

M1 侦察（已完成）
- validate 脚本定位两处根因：跨表 DV 直引 `统计!$A$15:$A$29`（兼容性差）；条纹仅偶数行单色、奇数行无填充。
- groups 现状实测：手填组 distinct=19、单例组 2、Top=robot18/linux16/sample16/project13/vue9。
- web_search 不可用 → 拉取文档按 repo 官方机制口径（D-4）。

M2 文档先行：TSK/PLN-008 落盘（本提交）。

M3 代码改造：generate_manifests.build_groups(+visibility 派生组)、catalog_to_markdown(groups 展示)、validate(命名区域+双色条纹四 sheet)。

M4 数据与产物：重生成 manifests/、catalog.md、normalize；复审脚本实算统计 → REF-005 → 删脚本。

M5 文档：GUIDE 拉取章节；DSN v1.2 变更记录。

M6 流程：分支 feat/groups-visibility-guide-rev → pre-commit 9 钩子 → push → PR（CI 双绿）→ 本地 --no-ff 合规合并 → LOG-008 → 汇报。

## 风险与对策

- R1 命名区域 API 在 openpyxl 3.1.5 的写法差异 → 实测 `wb.defined_names["TagCategories"]=DefinedName(...)`（3.1 为 dict 语义）。
- R2 build_groups 签名变更影响调用方 → 仅 build_project_entry 一处调用，同步改。
- R3 XML 全量变更（groups 属性）→ --check 与快照校验兜底；快照 groups 列取手填值不受派生影响，理论不变，导出后 diff 验证。
