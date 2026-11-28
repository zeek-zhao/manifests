# 任务书 TSK-20261128-001：克隆 manifests 并初始化开发环境

| 文档属性 | 内容 |
|---|---|
| 编号 | TSK-20261128-001 |
| 版本 | v1.0 |
| 日期 | 2026-11-28 |
| 编制 | AI Agent (zeek.zhao) |
| 审核 | 用户（已确认计划） |
| 状态 | 已确认，执行中 |

## 1. 目的

在 `/home/jenkins/zeek_work` 工作区内克隆 `zeek-zhao/manifests`（OWNER=zeek-zhao），完成分支切换与仓库局部提交身份配置，使后续多分支开发就绪。

## 2. 范围

- 仅限当前工作区 `/home/jenkins/zeek_work`，不跨工作区目录；
- 不修改任何全局 git/gh 配置；
- 不涉及业务代码改动。

## 3. 输入与依据

- 会话全局规则：克隆 `gh repo clone zeek-zhao/manifests 到 manifests`；提交身份仅 `zeek.zhao`；配置仅局部；Issue 标注分支；仅在当前分支工作；密钥明文本地文件存放；RTK 上下文压缩。
- 用户确认的四项决策：
  1. 密钥：由 Agent 创建明文文件（工作区 `.secrets/`，仓库外）；
  2. RTK：本地侧生效 + 远端输出精简 + 对话侧压缩；
  3. 当前分支：`feat/catalog-add-15-repos`；
  4. 初始化文档（AGENTS.md + docs 记录）提交并推送当前分支。

## 4. 任务分解（里程碑）

| 里程碑 | 任务 | 验收 |
|---|---|---|
| M1 环境与凭证 | 创建 `.secrets/gh_token`（600）；确认 gh/git 可用 | 权限 600；gh 认证可用 |
| M2 克隆 | `gh repo clone zeek-zhao/manifests manifests`；切到 `feat/catalog-add-15-repos` | 克隆成功；当前分支正确 |
| M3 局部身份 | local 配置 `user.name=zeek.zhao`、`user.email=zeek.zhao@foxmail.com` | `git config --local` 仅含合规身份 |
| M4 文档先行 | 编写 `AGENTS.md` 与本三份 TSK/PLN/LOG 文档并提交 | 文档入库，身份合规 |
| M5 推送与收尾 | 推送 `origin/feat/catalog-add-15-repos`；核验；清理 | 推送成功；无临时文件残留 |

## 5. 验收准则

1. 本地仓库存在于 `/home/jenkins/zeek_work/manifests`；
2. 当前分支为 `feat/catalog-add-15-repos` 且跟踪 origin 同名分支；
3. 局部身份为 `zeek.zhao <zeek.zhao@foxmail.com>`，全局配置未被修改；
4. 本文档集与 AGENTS.md 已提交并推送到当前分支；
5. 未产生遗留临时脚本；密钥未进入仓库。
