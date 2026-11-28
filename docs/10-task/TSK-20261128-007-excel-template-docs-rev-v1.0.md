# TSK-20261128-007 Excel 模板改造与文档体系整理任务书

| 项 | 内容 |
| --- | --- |
| 编号/版本 | TSK-20261128-007 / v1.0 |
| 日期 | 2026-11-28 |
| 提出人 | zeek.zhao |
| 执行者 | zeek.zhao（Agent 代执行） |
| 状态 | 已确认（用户授权一次性执行，无需逐步确认） |
| 分支 | feat/excel-template-docs-rev（单 PR 交付） |

## 1. 需求（用户 m00807）

1. **JSON 中文直出**：生成 JSON（当前唯一=manifests-excel-snapshot.json）中的中文直接输出，不使用 \uXXXX 转义，无乱码。
2. **manifests.xlsx 模板化重生成**：
   - 配色整体调暗（深色/低饱和），便于筛选阅读；
   - 新增「仓库属性」列（公开/私有）；新增「标签分类」列（统一标签体系，覆盖全部仓库）；
   - 新增「统计」Sheet，公式引用实现自动更新（总数、公开/私有占比、各标签分类数量）。
3. **文档整理**：使用说明文档；docs/ 目录分类；文档名规范化（编号-类型-主题-版本）并统一重命名。

## 2. 实现决策（复用现有列，避免语义重复）

- 「仓库属性」= 原 visibility 列升级改名，值域改中文 `公开/私有`（sync 从 GitHub API 映射写入）；「标签分类」= 原 category 列升级改名，沿用自有仓库既有 14 分类作为统一体系，扩展覆盖外部 70 行（按 topic/名称/分组推断）。
- 统计表用 Excel 公式（COUNTA/COUNTIF 整列引用）自动更新；「标签分类」下拉直接引用统计表分类清单区域（单一维护点）。
- 快照 `ensure_ascii=False`；pre-commit `pretty-format-json` 加 `--no-ensure-ascii` 对齐。
- 暗色主题（表头 #37474F 白字、条纹行 #ECEFF1）纳入 `validate_manifests_xlsx.py --normalize`，保证可持续再生成。
- 文档重组：docs/ 分 00-guide/10-task/20-design/30-plan/40-log/50-report/60-reference 七类；编号文档加 `-v1.0`；DSN 升 v1.1（附变更记录）；生成物 catalog.md 保留 docs/ 根（工具路径硬编码，GUIDE 中说明例外）；README/AGENTS 同步。

## 3. 数据事故披露与修复（本轮一并处理）

历史事故：TSK-003 知识列填充脚本列号错位（写 12/13/14，实际 purpose/contents/relations=11/12/13），致 11 行 relations 文本污染 visibility 列（col14 混入 10 条知识文本）。修复：值左移回位（12→11、13→12、14→13），visibility 自 b730db4 历史快照恢复并转中文。

## 4. 验收标准

1. 快照 JSON 中文直出且 pre-commit 全绿；2. Excel 131 行：仓库属性全填充∈{公开,私有}、标签分类全填充∈统一体系、统计表公式随数据自动更新、暗色主题生效；3. `--excel --check`/validate/catalog.md 一致；4. 文档目录+命名规范落地，README/AGENTS 链接有效；5. PR 合并后 main CI 绿。
