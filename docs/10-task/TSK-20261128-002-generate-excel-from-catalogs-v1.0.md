# 任务书 TSK-20261128-002：根据工程现状生成 Excel 工作簿

| 文档属性 | 内容 |
|---|---|
| 编号 | TSK-20261128-002 |
| 版本 | v1.0 |
| 日期 | 2026-11-28 |
| 编制 | AI Agent (zeek.zhao) |
| 审核 | 待用户确认计划 |
| 状态 | 待确认（依据 DSN-20261128-001 v0.5 定稿设计） |

## 1. 任务目标

依据设计文档 DSN-20261128-001 **v0.5**（已定稿），将当前工程现状数据（`catalogs/*.json`）落成真实 Excel 工作簿 `catalogs/manifests.xlsx`，供用户下载审核。**Excel 审核通过后另行启动代码实施任务书**（生成器改造、自动化脚本、CI 工作流均不在本任务范围）。

## 2. 范围

- **做**：生成 4-sheet 工作簿（repos / remotes / config / readme），数据来源=现有 6 个 catalog JSON（120 条仓库记录、4 平台 remotes、1 owner 配置）；格式含冻结首行、列宽、下拉校验；提交推送 `catalogs/manifests.xlsx` 至当前分支。
- **不做**：不改任何代码（`generate_manifests.py` 继续读 JSON）；不删 JSON（D5 过渡保留）；不实施 sync/CI（第二阶段）；purpose/contents/relations 三个新描述列留空待用户人工沉淀。

## 3. 数据现状（侦察结论）

| 文件 | 仓库条目 | 备注 |
|---|---|---|
| community-gitee.json | 26 | 基础 7 字段 |
| community-github.json | 26 | 含 remotes（4 平台） |
| community-gitlab.json | 8 | 基础 7 字段 |
| community-yoctoproject.json | 4 | 基础 7 字段 |
| cpp.json | 6 | 基础 7 字段 |
| zeek-zhao.json | 50 | 自有仓库，含 category/visibility/description/preferred_protocol/suggested_action；owners={zeek-zhao:{preferred_protocol:git,groups:[owner-zeek-zhao]}}；1 行含 linkfiles |

生成器 quickstart 硬编码值（抄入 config 表）：`https→bazelbuild/examples.git`、`zeek-zhao→zeek-zhao/docker-sample.git(git)`。

## 4. 验收标准

1. 工作簿含 4 个 sheet，列名与 DSN v0.5 §3/§4/§5 完全一致；
2. repos 表 120 行数据与 JSON 记录一一对应，name+path 无重复；
3. remotes 表 4 平台、config 表 5 键、readme 三区齐全；
4. 用户下载打开可正常编辑（下拉可用、冻结首行、列宽合理）。

## 5. 边界与规则

临时脚本置于 `/tmp`（工作区外），用完即删；仅当前分支；提交身份规范；不改代码。
