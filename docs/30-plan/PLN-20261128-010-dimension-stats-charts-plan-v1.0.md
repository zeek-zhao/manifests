# PLN-20261128-010 维度精简与统计动态化实施计划

| 文档编号 | PLN-20261128-010 |
| --- | --- |
| 版本 | v1.0 |
| 日期 | 2026-11-28 |
| 作者 | zeek.zhao（Agent 代笔） |
| 关联 | TSK-20261128-010 |

## 里程碑与任务

| 里程碑 | 任务 | 产出 |
| --- | --- | --- |
| M1 | 分支 feat/dimension-stats-charts（基于 main 483349b） | 分支就绪 |
| M2 | 数据调整脚本（/tmp 按表头名定位，行 3 起数据区）：groups 删 5 组+补 11 仓；language API 回填 16 行；第 2 行说明行与标签下拉不触碰 | xlsx 数据就绪 |
| M3 | tools/stats_report.py：API 拉取→动态统计 sheet（含说明行/表头样式）→辅助区→4 图表 | 新 sheet+图表 |
| M4 | normalize（validate --normalize，动态统计 sheet 排除在外）→generate --excel（删 by-topic 5 文件）→catalog.md | 产物一致 |
| M5 | 文档：REF-007 调整记录、GUIDE v1.2、DSN v1.4 §14、README 工具/workflow 更新、LOG-010；excel-sync.yml 接入 stats_report | 文档齐备 |
| M6 | pre-commit 9 钩子→提交推送→PR→CI 双绿 | PR #9 |
| M7 | 本地 --no-ff 合并→删分支→main CI→LOG 补录 run id→汇报 | 闭环 |

## 风险与对策

| 风险 | 对策 |
| --- | --- |
| API 限速 | token 认证 5000/h；串行 sleep 0.15s |
| stats_report 图表与 normalize 冲突 | normalize 仅处理 repos/remotes/config/readme/统计 五表；动态统计 sheet 由 stats_report 全权负责并幂等重建 |
| language 新 slug 大量出现 | 汇报新增语言清单；允许单例文件 |
| 迁移脚本表结构错位（TSK-009 教训） | 脚本按表头名定位+遍历前 assert 表结构（第 2 行 A2==（列说明）） |
