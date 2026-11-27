# 落地计划 PLN-20261128-002：生成 Excel 工作簿（TSK-20261128-002）

| 文档属性 | 内容 |
|---|---|
| 编号 | PLN-20261128-002 |
| 版本 | v1.0 |
| 日期 | 2026-11-28 |
| 编制 | AI Agent (zeek.zhao) |
| 审核 | 待用户确认 |
| 状态 | 待确认 |

## 1. 环境结论（已侦察）

远端 Python 3.10.12 + openpyxl 3.1.5 已安装，可直接生成 xlsx；无需装依赖。

## 2. 执行步骤

| # | 步骤 | 说明 |
|---|---|---|
| 1 | 写临时脚本 `/tmp/gen_manifests_xlsx.py` | 工作区外，用完即删 |
| 2 | 脚本：读 6 个 JSON → 生成 4 sheets | 列序按 DSN v0.5 §3（17 列）/§4（4 列）/§5（5 键）/§6（readme 三区） |
| 3 | 读回校验 | sheet 名、列名、行数=120、name+path 唯一、枚举值合法 |
| 4 | 提交推送 `catalogs/manifests.xlsx` | 当前分支，提交身份 zeek.zhao |
| 5 | 删除临时脚本 | `rm /tmp/gen_manifests_xlsx.py` |
| 6 | 用户下载审核 Excel | 通过后另出代码实施任务书 |

## 3. 数据映射规则

| Excel 列 | JSON 来源 |
|---|---|
| name/path/branch/platform/topic/language/groups | 各文件 repositories[] 同名字段（groups 数组→逗号拼接） |
| protocol | zeek-zhao.json 行级 `preferred_protocol`（现状值 `git` 照抄，见 P1）；外部行留空 |
| linkfiles | 行级 linkfiles 数组 → `src:dest;…` 序列化（现状 1 行有值） |
| description/visibility/category/suggested_action | zeek-zhao.json 同名字段照抄；外部行留空 |
| purpose/contents/relations/note | 全部留空（人工知识列，待用户沉淀） |
| remotes 表 | 合并全部文件的 remotes 键（现状 community-github.json 4 平台），proxy 列留空 |
| config 表 | default_protocol=https、self_owner=zeek-zhao、use_proxy_https=FALSE、quickstart 两键（生成器行13-22 硬编码值抄录） |
| readme 表 | A 设计说明（v0.4 触发链路）/B 全字段字典（含人工/自动分工）/C 填写指引 |

格式：首行冻结、列宽按内容自适应（上限 60）、platform 下拉（值=remotes 表平台）、protocol 下拉（https/git）、description/visibility/category/suggested_action 下拉提示不强制（见 P3）。

## 4. 决策点（需用户确认）

| # | 决策点 | 建议 |
|---|---|---|
| P1 | 自有行 `protocol` 列：现状数据全部为 `git`（preferred_protocol），而 DSN §8 自动化策略要求自有行留空继承默认 | **本次按现状照抄 `git`**——本任务是现状快照，照抄不改变现有生成行为；第二阶段自动化上线时再按 §8 收敛为留空 |
| P2 | owners 级配置（preferred_protocol=git、groups=[owner-zeek-zhao]）随 D8 删表丢弃 | 确认丢弃：生成器从不用 owner groups，owner 协议偏好已体现在行级 protocol，丢弃无损 |
| P3 | suggested_action 现状含自由文本（如「待确认：定位待明确」5 条），与设计枚举（保留/观察/淘汰/待评估）不一致 | 下拉设为**提示不强制**（showErrorMessage=False），现状值照抄不标红；枚举收敛由用户后续人工整理 |

## 5. 风险与回滚

| 风险 | 对策 |
|---|---|
| xlsx 二进制 diff 不友好，评审依赖下载打开 | 生成后同时输出文本摘要（sheet/行数/列名/样例行）供快速核对 |
| JSON 与 Excel 过渡期双源不一致 | 本任务不改代码，JSON 仍是现行数据源；Excel 审核通过、代码改造完成后 JSON 按 D5 退役 |
| 生成脚本缺陷产生坏文件 | 读回校验失败即不提交；即使误提交，revert 单提交即可回滚 |
