# 落地计划 PLN-20261128-001：克隆 manifests 并初始化开发环境

| 文档属性 | 内容 |
|---|---|
| 编号 | PLN-20261128-001 |
| 版本 | v1.0 |
| 日期 | 2026-11-28 |
| 编制 | AI Agent (zeek.zhao) |
| 审核 | 用户（已确认） |
| 状态 | 已执行 |

## 1. 执行前侦察结论（只读，未做变更）

| 项 | 结论 |
|---|---|
| git | 2.34.1，`/usr/bin/git` |
| gh | v2.103.3 位于 `/home/jenkins/bin/gh`（不在 PATH）；keyring 已登录 `zeek-zhao`（活跃，scopes 含 repo/workflow） |
| 网络 | github.com / api.github.com 均 HTTP 200 |
| 全局 git 身份 | `Jenkins-SWD`（不符合提交身份规则，须以局部配置覆盖，且不动全局） |
| RTK | 远端未安装；npm 无 `@liustack/rtk`（`rtk` 4.4.0 为无关包）；无 cargo |
| 远端分支 | `main`（默认）、`feat/catalog-add-15-repos` |
| 目标目录 | `zeek_work/manifests` 不存在，克隆无覆盖风险 |

## 2. 里程碑与任务（与 TSK-20261128-001 第 4 节一致）

M1 密钥与环境 → M2 克隆与分支切换 → M3 局部身份 → M4 文档先行 → M5 推送与收尾。

## 3. 风险与处置

| # | 风险 | 处置 |
|---|---|---|
| R1 | gh 不在 PATH | 命令内临时 `export PATH=/home/jenkins/bin:$PATH`，不改任何启动文件 |
| R2 | 全局身份不合规 | manifests 内 local 覆盖；提交前自检 |
| R3 | 明文密钥路径原为「待补充」 | 经用户确认由 Agent 创建 `.secrets/gh_token`（600，仓库外） |
| R4 | RTK 远端不可安装（无安装源） | 经用户确认采用「本地侧 RTK + 远端精简输出 + 对话侧压缩」，并如实记录 |
| R5 | 公共仓库推送范围 | 按「仅在当前分支上工作」规则，文档推送目标为 `origin/feat/catalog-add-15-repos`，不动 `main` |

## 4. 用户决策记录（2026-11-28 确认）

1. 密钥来源：Agent 创建明文文件；
2. RTK：本地侧生效 + 远端精简输出；
3. 当前分支：`feat/catalog-add-15-repos`；
4. 初始化文档：提交并推送当前分支。
