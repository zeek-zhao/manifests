# LOG-20261128-009 仓库体积/布局/下拉/结构改造执行日志

| 文档编号 | LOG-20261128-009 |
| --- | --- |
| 版本 | v1.0 |
| 日期 | 2026-11-28 |
| 作者 | zeek.zhao（Agent 代笔） |
| 关联 | TSK-20261128-009 / PLN-20261128-009 / REF-20261128-006 / DSN v1.3 |
| 状态 | 已完成 |

## 1. 任务

用户七项指令：①API 统计仓库大小入数据；②列宽紧凑+长文本换行；③修复标签分类下拉（打开文件实际生效）；④表结构调整（1 表头/2 列说明/3 数据）；⑤仓库属性英文化 public/private；⑥评估维度精简（说明理由后执行）；⑦GUIDE 同步。授权沿用既有流程（执行完毕汇报）。

## 2. 执行记录

1. **任务书/计划**：docs/10-task/TSK-20261128-009-repo-size-layout-tuning-v1.0.md + docs/30-plan/PLN-20261128-009-*.md（决策 D-1~D-8，里程碑 M1-M7，风险 R1-R4）。
2. **四工具改造**：
   - generate_manifests.py：REPO_COLUMNS/SNAPSHOT_REPO_ORDER 增「仓库大小(KB)」（插标签分类后，统计公式 N/O 列位不变）；DATA_START_ROW=3 常量；config/remotes/repos 读取起点行 3；size 非数字校验；build_groups 派生组随英文值域（visibility-public/private）；**删除 by-protocol 维度产出**（D-6）。
   - sync_self_repos.py：数据起点行 3（含 obsidian 首行去重判定同步参数化）；visibility 直写 API 英文原值；size 列刷新与新行默认值。
   - validate_manifests_xlsx.py 全文重写：三行结构样式（表头深蓝灰/说明行灰底斜体/数据双色条纹自第 3 行起）；紧凑列宽（内容自适应 CJK 双宽、封顶 28）；长文本列（name/path/groups/linkfiles/description/purpose/contents/relations/suggested_action/note）单元格内换行；下拉枚举全部内联且自第 3 行起；标签分类=内联枚举+TagCategories 命名区域双保险；统计公式 COUNTA-2、COUNTIF public/private、标签 14 类。
   - catalog_to_markdown.py：明细表增「大小(KB)」列。
3. **数据迁移**（/tmp/tsk009_migrate.py 按表头名定位，用后即删）：仓库属性 131 行英文映射；插入 size 列；github/gitee API 抓取 size；三表插入列说明行。
4. **维度精简**：git rm manifests/generated/by-protocol/{https,git}.xml；default.xml 索引同步；README/GUIDE/REF-003 协议维度示例移除。
5. **文档**：GUIDE-001 升 v1.1（18 列修正+三行结构+EN 值域+14 类+大小列）；DSN 升 v1.3（§14 追加）；REF-006 维度评估报告新写；README 维度描述更新。

## 3. 事故与修复

1. **迁移循环起点 bug**：迁移脚本以 DATA_START=3 遍历，但执行时表仍为旧两行制（说明行是后续步骤插入），旧首数据行 weidongshan/esp32_100ask_project（新表第 3 行）被跳过——属性漏转英文、size 漏抓。诊断读回发现后补丁修复（属性已转 public；该仓为 gitee 平台本就无 size）。教训：**迁移脚本内所有遍历必须与其当时的实际表结构一致，或先做结构变更再迁数据**。
2. **gitee size 字段缺失**：gitee API v5 repo 端点响应不含 size 字段（20 次成功调用均为 None），与 D-1 预设不符；按「数据可得性上限留空」处理并记录于 REF-006 §5。
3. **zeek-zhao/orgflow-devops1**：GitHub API 404（上游已删除，note 已有标注），size 留空。
4. **「待整理」标签**：唯一成员 alpu；移除该类后 alpu 标签清空待人工归类（下拉可用），未引入「其他」兜底类。

## 4. 验收

- 131 行仓库属性：public 88 / private 43，无中文残留；esp32 行已修正。
- 仓库大小：90/131 行有值，合计 2,111,449 KB（约 2.01 GB）。
- 表结构：repos/remotes/config 三表均为 1 表头/2 列说明/3 起数据；冻结 A3；说明行随 --normalize 自动重写。
- 下拉：protocol/platform/仓库属性/suggested_action/标签分类 5 个，全部内联枚举、范围 3:1000；TagCategories=统计!$A$15:$A$28（14 类）。
- 生成物：29 个维度 XML（4 platform+7 language+17 topic+1 owner）+default 索引+2 quickstart 示例；`--excel --check` 通过；catalog.md（含大小列）`--check` 通过；快照重导出（中文直出）。
- 维度组核验：by-platform/github.xml 含 visibility-public 48 + visibility-private 43 = 91 行全覆盖。
- pre-commit 9 钩子全绿；CI 结果待合并后补录（run id 见后续提交）。

## 5. 遗留

- alpu 标签待人工归类（下拉点击即选）。
- orgflow-devops1 上游已删，建议后续评估移除或标废弃。
- gitee size 如需补齐需 Gitee 认证接口复查（当前免费接口无字段）。
- groups 手填组与标签分类双轨维持现状（REF-006 §4），持续观察。
