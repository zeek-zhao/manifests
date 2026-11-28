# 任务书：manifests 镜像池 ghcr 公开分发（image-pool-ghcr）

| 项 | 内容 |
|---|---|
| 编号 | TSK-20261128-017-image-pool-ghcr-v1.0 |
| 日期 | 2026-11-28 |
| 编制 | zeek.zhao（AI 协作） |
| 审核 | 用户（方案 v1→v2→v3 三轮审核，2026-11-28 决策点确认） |
| 状态 | 已批准，实施中 |

## 1. 任务来源

用户对 manifests 清单仓库提出正式适配：以 CI 流水线将清单内 129 个仓库按 topic 组打包为公开 Docker 镜像发布 ghcr.io，实现国内可加速拉取的全量镜像池；私有仓库内容必须以镜像层加密保护。

## 2. 任务范围

1. 落盘设计文档 DSN-20261128-017（v1.0，含已确认决策点）；
2. 本地端到端 Demo（样本组=app：2 private + 2 public）：加密→构建→公开推送→下载→解密→还原→一致性校验；
3. CI 流水线 `group-pool.yml`：按组 matrix 构建、原子 fetch+加密、>500MB 大仓独立镜像（不下载即可跳过）、并发空间治理；
4. 配套工具：pool_build.py / pool_restore.py / pool_scan.py；
5. 验证报告与操作日志（LOG-20261128-017）。

## 3. 已确认决策点（用户 2026-11-28）

| # | 决策 | 结论 |
|---|---|---|
| D1 | registry | **仅 ghcr.io**；ACR 配置留文档不启用 |
| D2 | 加密 | imgcrypt（OCI 镜像层加密）+ **JWE 单密钥对** |
| D3 | >500MB 大仓 | **每仓独立镜像**（apollo 3.3GB、qtkaifajingyan 622MB，均 public 无需加密），按需拉取，不拉即不下 |
| D4 | clone 形态 | **--mirror**（还原可用 git 仓库） |
| D5 | 凭据 | 直接使用 repo secrets 中 GH_PAT |
| D6 | Demo 样本组 | app（4 仓，最小可行） |

## 4. 约束

- 红线：private 仓库层不加密不得进公开镜像（CI 硬门禁）；
- 凭证不入库，私钥仅存宿主 `~/.secrets/`（600）与 repo secrets；
- 大规模操作全部在 CI，本地只做 Demo 级小实验；临时脚本用完即删；
- 分支：从 main 拉出 `image-pool-ghcr`，完成后按快照方式合并（与方案线惯例一致）。
