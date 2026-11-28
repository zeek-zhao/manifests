# 落地计划：manifests 镜像池 ghcr 公开分发

| 项 | 内容 |
|---|---|
| 编号 | PLN-20261128-017-image-pool-ghcr-v1.0 |
| 日期 | 2026-11-28 |
| 编制 | zeek.zhao（AI 协作） |
| 审核 | 用户（同 DSN） |
| 状态 | 执行中 |

## 里程碑与任务

| # | 任务 | 产出 | 状态 |
|---|---|---|---|
| A1 | 任务书+设计文档+本计划落盘 | TSK/DSN/PLN-20261128-017 | ✅ |
| A2 | imgcrypt ctr 容器内编译 | /tmp/imgcrypt-out/ctr | 执行中（后台） |
| A3 | JWE 密钥对生成（~/.secrets 600 + keys/jwe.pub 入仓） | 密钥 | 待 |
| A4 | Demo 端到端（app 组 4 仓） | Demo 记录+LOG | 待 |
| A5 | 工具落盘 pool_build/pool_restore/pool_scan | tools/ | 待 |
| A6 | workflow group-pool.yml 落盘（matrix+大仓独立+空间治理） | .github/workflows/ | 待 |
| A7 | CI 试点 run（dispatch app 组）→ 验证产物 → 报告 RPT | RPT-20261128-017 | 待 |
| A8 | 治理（GUIDE 消费侧指引/AGENTS 链接）+ 分支提交推送 | 提交+推送 | 待 |

## 风险与缓解

见 DSN §11（R1 编译结果、R2 ghcr 兼容性为 A2/A4 的验证重点；若 imgcrypt 编译不可行，回退方案=文件级 age 加密层（v2 方案），升级用户决策）。
