# TSK-20261128-011 复查与修复（下拉框/同步删行/遗留清理）任务书

| 文档编号 | TSK-20261128-011 |
| --- | --- |
| 版本 | v1.0 |
| 日期 | 2026-11-28 |
| 作者 | zeek.zhao（Agent 代笔） |
| 关联 | TSK-20261128-009 / TSK-20261128-010 / DSN v1.4 / REF-20261128-006 |
| 状态 | 已完成 |

## 1. 背景

用户要求对 TSK-010 调整后的仓库做一轮复查与修复：①复查 Excel/by-topic/catalog.md/日志并列清单确认；②修复 manifests.xlsx 表头下拉框（第 1 行标签分类列实际可点选）；③动态同步与 GitHub 仓库列表完全一致（上游删→行删、新增→行增）；④遗留清理（alpu 按 c/c++ 现状保留、orgflow-devops1 移除）。

## 2. 复查清单（已确认：全部修复）

| # | 项 | 结论 |
| --- | --- | --- |
| R1 | by-topic 文件 vs default.xml 引用 | 一致（28 include 全匹配；诊断首跑正则漏前缀属误报） |
| R2 | 表头下拉框 | 根因=DV sqref 自第 3 行起不含第 1 行；XML/内联枚举串本身合法 |
| R3 | 同步删行能力 | sync_self_repos.py 无 delete_rows，上游消失仅追加 note |
| R4 | orgflow-devops1 残留 | Excel 行 + 4 维度文件 + 动态统计行 |
| R5 | alpu | language=c/c++ 现状保留（用户指令），groups/topic=linux 正常 |
| R6 | readme sheet 文案 | 停留在 TSK-002 时代，未随三行结构/英文值域/动态统计更新 |
| R7 | catalog.md / LOG | 无缺失，随 R4 重生成 |
| R8 | 动态统计 sheet 与 normalize 兼容 | normalize 四表循环不含该 sheet，无覆盖风险（实测 4 图表保留） |

## 3. 交付物

1. validate_manifests_xlsx.py：5 个枚举下拉范围改为 `第1行:1000`（表头可点选）；新增 `_refresh_readme()`，normalize 时重刷 readme sheet 文案（README_ROWS 15 条）。
2. sync_self_repos.py：上游消失→删除整行（认证 /user/repos 列表为唯一真源；主循环改倒序遍历防行号位移；obsidian 同名首行语义保持；gitee/gitlab/yocto 行在 K5 分支跳过不受影响）。
3. Excel：orgflow-devops1 行删除（含动态统计随 stats_report 重建）；orgflow-devops 知识列 relations 过时文字修正。
4. 文档：GUIDE v1.2（下拉第 1 行可点选 + 删行行为）、REF-003（sync 策略更新）、LOG-20261128-011；manifests 产物/快照/catalog.md 全量重生成。

## 4. 验收标准

- XML 解包确认 5 个 DV sqref 均含第 1 行
- orgflow-devops1 在 manifests/、catalog.md、快照数据行中零残留（知识列描述文字同步修正）
- `--excel --check`、`validate`、`catalog.md --check` 通过；动态统计 4 图表保留
- pre-commit 9 钩子全绿；PR CI 绿
