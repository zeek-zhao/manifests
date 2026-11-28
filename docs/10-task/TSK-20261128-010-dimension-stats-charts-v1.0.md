# TSK-20261128-010 维度精简执行与统计动态化

| 文档编号 | TSK-20261128-010 |
| --- | --- |
| 版本 | v1.0 |
| 日期 | 2026-11-28 |
| 作者 | zeek.zhao（Agent 代笔） |
| 状态 | 已确认，执行中 |
| 关联 | TSK-20261128-009 / REF-20261128-005 / REF-20261128-006 / DSN v1.3 |

## 1. 背景

用户方案轮（第一步）已确认：dimension 交叉分析显示 19 个手填 groups 中 11 个与标签分类 100% 同义，3 个泛化组语义重复/缺失，language 列存在误填（linux）与缺失（11 个 excel-sync 新仓）；统计需改为 API 动态获取并生成图表。

## 2. 已确认决策（用户「全部采纳」）

| # | 决策 |
| --- | --- |
| D-1 | 删除 groups：`sample`（2 个非示例成员改归 ai）、`project`（不补）、`c++`（与 language c-cpp 重复）、`qemu`、`ops`（单例） |
| D-2 | 空 groups 11 仓补组：ros_21_tutorials+ROS-Academy-for-Beginners→robot；ai-book/ai-docker/ai-mcp/ai-server/ai-tools→ai；tabharbor→app；jenkins-Shared-Library1→devops；backup+wf4-selftest→tools |
| D-3 | language 按 GitHub API `language` 字段实测回填 16 行（linux 误填 5 + 空 11）；映射 C++→c/c++、JavaScript/TypeScript→nodejs、其余小写化、API null→mixed |
| D-4 | rust/go 单例语言文件与 mixed 保留 |
| D-5 | 标签分类 14 类不合并；下拉维持内联枚举；repos 第 2 行说明行本次不改动 |
| D-6 | 双轨分工文档化：groups/topic=manifest 拉取维度（技术栈/生态），标签分类=管理统计维度（业务属性），写入 GUIDE 与 REF-005（升 v1.1） |
| D-7 | 新增 tools/stats_report.py：GitHub API 实时拉取 stars/forks/size/pushed_at → 写入新 sheet「动态统计」（131 行全列，非 github 平台指标留空，列 name/platform/标签分类/stars/forks/size_KB/pushed_at）→ openpyxl 原生图表嵌入：标签分布条形图、platform 饼图、size Top15 条形图、public/private 饼图；辅助数据区置于同 sheet H 列起 |
| D-8 | stats_report 接入 excel-sync workflow（dispatch 时刷新动态统计与图表） |
| D-9 | topic 维度净效果 19→14 文件；重新生成全部产物与 catalog.md |

## 3. 交付物

1. tools/stats_report.py（新）
2. catalogs/manifests.xlsx（groups/language 调整 + 动态统计 sheet + 4 图表）
3. manifests/generated/by-topic 删 5 文件、其余产物重生成；catalog.md
4. docs/10-task/TSK-010、30-plan/PLN-010、60-reference/REF-20261128-007-dimension-adjust-record-v1.0.md、GUIDE v1.2、DSN v1.4（§14）、README、LOG-20261128-010
5. .github/workflows/excel-sync.yml 接入 stats_report

## 4. 验收标准

- groups 列无被删组残留；空 groups=35 行为删除冗余组后的设计留空（仓库仍由标签/语言/平台维度覆盖）
- 动态统计 sheet 数据 131 行；4 图表可在 Excel/WPS 正常渲染；标签下拉仍可点选
- `--excel --check`、validate、catalog.md `--check`、pre-commit 9 钩子全绿
- CI 双绿后本地 --no-ff 合并（身份合规），LOG 补录 run id

## 5. 风险

| 风险 | 对策 |
| --- | --- |
| API language 返回大量新 slug 产生碎维度文件 | 允许（D-4 已确认单例维度保留），汇报时列明新增语言清单 |
| 动态统计 sheet 被 validate/generate 误处理 | generate 只读 repos/remotes/config；validate 不校验动态统计 sheet |
| 图表引用跨 sheet 区域在 WPS 兼容性 | 图表数据源引用同 sheet 辅助区，避免跨表 |
