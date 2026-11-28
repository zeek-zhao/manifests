# LOG-20261128-008 groups/下拉/条纹/拉取指南操作日志

| 项 | 内容 |
| --- | --- |
| 日期 | 2026-11-28 |
| 执行者 | zeek.zhao（Agent 代执行） |
| 关联 | TSK/PLN-20261128-008 |
| 分支 | feat/groups-visibility-guide-rev（PR #7 已合并，分支已删） |

## 1. 侦察与根因

1. **标签分类下拉不显示根因**：`validate --normalize` 生成跨表 DV 直引 `统计!$A$15:$A$29`，Excel/WPS 对跨表数据验证直引兼容性差 → 改命名区域 `TagCategories`（官方兼容路径），统计表仍为单一维护点。
2. **数据行白屏根因**：xlsx 规范中行级 `row_dimensions[].fill` 不被 Excel/WPS 渲染，且旧逻辑仅偶数行着色 → 改逐单元格双色条纹（`#D6DEE7`/`#EBEFF4`），四 sheet 全覆盖，奇偶行均显式着色。
3. web_search 不可用 → 拉取文档按 repo 官方确证机制撰写（单仓 `repo sync <path>`、指定组走维度清单、全部走 default.xml），不杜撰组过滤旗标。

## 2. 变更记录

1. `tools/generate_manifests.py`：`build_groups` 派生追加 `visibility-公开`/`visibility-私有`（读 仓库属性 列，不入 Excel 手填列，空值跳过）。
2. `tools/catalog_to_markdown.py`：明细表 groups 列展示派生组（复用 `gm.build_groups`）。
3. `tools/validate_manifests_xlsx.py`：命名区域+下拉改造；双色条纹 `_style_sheet` 重写；remotes/config/readme 一并入条纹。
4. 文档：GUIDE §5 代码拉取方式（4 认证 × 3 范围，原 §5-7 顺延为 §6-8）；REF-20261128-005 groups 复审报告；DSN 文件升 v1.2 并附变更记录行。
5. 产物重生成：35 个维度清单 XML（全部 project groups 含 visibility 组）、catalog.md（262 行变更）、manifests.xlsx（34926→35192B）。

## 3. 验收记录

1. XML 组核验：35 维度文件全部含 `visibility-{公开|私有}`；行级覆盖 88 公开+43 私有=131（唯一名级 130，obsidian 同名双行双 path 属设计内）。
2. Excel 核验：`TagCategories=统计!$A$15:$A$29`、下拉 f1=TagCategories、四 sheet r2=`D6DEE7`/r3=`EBEFF4` 隔行可见。
3. groups 复审实算（REF-005）：手填空组 11 行（excel-sync 新仓预期）、distinct 19、单例 ops/qemu、非 slug 字符 0、派生后 26 组。
4. pre-commit 9 钩子全绿；`--excel --check`/`catalog.md --check` 过；PR CI 双绿；合并 6a5dcc3 后 main CI 绿；worktree clean。

## 4. 遗留

- `ops`/`qemu` 单例组与 `sample`/`project` 泛化组的归并收敛（REF-005 §3，不阻塞）；
- 11 个新自有仓手填 groups 待人工补组（excel-sync 不生成组）。
