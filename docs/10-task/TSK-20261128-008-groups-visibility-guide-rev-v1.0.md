# TSK-20261128-008 groups 审查/可见性入组/拉取文档/Excel 修复

| 文档编号 | TSK-20261128-008 |
| --- | --- |
| 版本 | v1.0 |
| 日期 | 2026-11-28 |
| 编制 | zeek.zhao（Agent 代笔） |
| 审核 | 用户（授权沿用现有流程，无需逐步确认） |
| 状态 | 执行中 |
| 分支 | feat/groups-visibility-guide-rev（基于 main） |

## 1. 背景与目标

用户指令四项：①说明 groups 生成规则并多维复审现状；②仓库属性（visibility）纳入 groups 展示；③使用说明补齐代码拉取章节（gh CLI/SSH/HTTPS/本地代理 × 单仓/指定组/全部）；④修复标签分类下拉、数据行加深配色+隔行条纹实际可见。完成后 PR 合并，更新 catalog.md 与日志。

## 2. 交付物

1. `docs/60-reference/REF-20261128-005-groups-system-review-v1.0.md`：groups 规则说明+三维复审报告（分类覆盖率/命名一致性/归属合理性，真实统计数字）。
2. `tools/generate_manifests.py`：build_groups 追加派生组 `visibility-公开`/`visibility-私有`（读 仓库属性 列，空值跳过）。
3. `tools/catalog_to_markdown.py`：明细表 groups 列展示派生后组（手填+platform+topic+visibility）。
4. `tools/validate_manifests_xlsx.py`：下拉改命名区域（TagCategories→统计!$A$15:$A$29）；条纹改双色逐单元格（含奇数行），四 sheet 全覆盖。
5. `docs/00-guide/GUIDE-20261128-001-manifest-usage-guide-v1.0.md`：新增「代码拉取」章节（4 认证 × 3 范围）。
6. DSN 升 v1.2（§7 groups 规则+变更记录）；catalog.md 重生成；LOG-008。

## 3. 技术决策（D-1~D-5）

- D-1 visibility 组为**生成时派生**（不入 Excel groups 手填列），避免与 仓库属性 列双写失同步；命名 `visibility-公开`/`visibility-私有` 与列值一致。
- D-2 下拉修复采用命名区域（Excel/WPS 对跨表 DV 直引兼容性差，命名区域是官方兼容路径）。
- D-3 条纹配色 `#D6DEE7`/`#EBEFF4` 双色低饱和，逐单元格填充（行级 fill 在 xlsx 规范中不生效，此为上版白屏根因之一）。
- D-4 拉取文档只写 repo 工具确证支持的机制：单仓 `repo sync <name|path>`、指定组=维度清单 `repo init -m`、全部=default.xml；不杜撰组过滤旗标（web_search 不可用，按 repo 官方文档常识口径）。
- D-5 复审报告数据由临时脚本实算（脚本用完即删）。

## 4. 验收标准

- 生成的 XML 中每个 project 的 groups 含 `visibility-{公开|私有}`；catalog.md 明细表同步。
- 打开 Excel：下拉可用（命名区域）、四 sheet 数据行双色条纹可见。
- pre-commit 全绿；CI 双绿；合并后 main CI 绿。
