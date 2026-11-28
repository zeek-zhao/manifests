# LOG-20261128-010 维度精简与统计动态化执行日志

| 文档编号 | LOG-20261128-010 |
| --- | --- |
| 版本 | v1.0 |
| 日期 | 2026-11-28 |
| 作者 | zeek.zhao（Agent 代笔） |
| 关联 | TSK-20261128-010 / PLN-20261128-010 / REF-20261128-007 |
| 状态 | 已完成 |

## 1. 任务

用户两步指令：第一步输出维度调整建议表（topic/language/groups 交叉审视）待确认；第二步确认后执行 Excel 调整与重新生成，统计改 API 动态获取并生成图表。用户已确认「全部采纳」。

## 2. 执行记录

1. **第一步方案**：交叉分析 131 行数据（groups×标签×topic×language），产出 9 项建议表，用户全部采纳；
2. **文档先行**：TSK-20261128-010（决策 D-1~D-9）+ PLN-20261128-010（M1~M7）；
3. **数据调整**（临时脚本，用后即删）：
   - groups 列 50 行调整：删 sample/project/c++/qemu/ops 五组、11 仓补组、2 个非示例成员改归（ai-knowledge→ai、jenkins-shared-library→devops）；
   - topic 列 45 行同步调整（执行中确认 topic 生成列才是 by-topic 维度文件与 groups 派生属性的真正数据源，详见 REF-007 §2）；
   - language 列 16 行 GitHub API 实测回填（linux 误填清零，新增 cmake/groovy/powershell/shell 维度）；
4. **统计动态化**：tools/stats_report.py 新增——GitHub API 拉 91 个 github 仓 stars/forks/size/pushed_at（89 有值，orgflow-devops1 上游已删 404 留空），「动态统计」sheet 131 行全列（非 github 平台留空），4 张原生图表（标签分布条形/平台饼/size Top15 条形/public-private 饼）+ 辅助区 COUNTIF 公式；接入 excel-sync 工作流；
5. **产物重生成**：normalize → generate --excel → 快照重导出 → catalog.md（276 行）→ 全量 --check；
6. **stale 清理**：git rm by-topic/{sample,project,cpp,qemu,ops,common,todo}.xml（前 5 为本次删除组，common/todo 为历史遗留无引用文件）；
7. **文档**：GUIDE v1.2（6 Sheet 结构、动态统计 §4.1、双轨分工）、DSN v1.4（§14）、README 工具行、REF-005 §4 注记、REF-007 执行记录、LOG-010。

## 3. 事故与修复

1. **API 404**：GitHub API URL 误带 `.git` 后缀致 16 次调用全 404；修正为剥离后缀后全部成功。教训：API 调用与仓库名字段的 `.git` 约定需显式转换（sync_self_repos 既有实现已正确处理）。
2. **迁移脚本列源错判**：首轮删组仅改 groups 手填列，by-topic 文件未变化——核验发现维度文件源于 `topic` 生成列（方案阶段将两列混为一谈）。补丁双列同步执行后收敛。教训：**改动维度前必须核对生成器的真实数据源列**（REF-007 §2 已固化该机制说明）。
3. **stale 维度文件**：生成器只写当前维度文件、不清理历史产物，`common.xml`/`todo.xml` 为更早期遗留（无 default.xml 引用）；本轮统一按「default.xml 引用集 vs 磁盘文件集」差集清理。

## 4. 验收

- topic 列/groups 列无被删组残留；11 新仓双列补齐；language 无空值无 linux；
- 「动态统计」sheet 133 行（含表头/说明行）、4 图表、辅助区公式正确（COUNTIF 引用数据区）；
- `--excel --check`、`validate`、`catalog.md --check`、pre-commit 9 钩子全绿；
- CI 结果与合并记录待合并后补录。

## 5. 遗留

- alpu 标签仍待人工归类（下拉可用）；
- orgflow-devops1 上游已删，建议后续任务评估移除该行；
- groups 留空 35 行为设计行为，后续如需恢复某仓 topic 维度拉取，在 topic/groups 列补词即可。
