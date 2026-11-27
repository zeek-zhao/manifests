# 任务书 TSK-20261128-004：Excel 生成链路代码实施（第二阶段）

| 文档属性 | 内容 |
|---|---|
| 编号 | TSK-20261128-004 |
| 版本 | v1.0 |
| 日期 | 2026-11-28 |
| 编制 | AI Agent (zeek.zhao) |
| 审核 | 已授权（用户 m00353「没问题的话再去写代码」+ m00406「可以…然后继续」；设计 DSN v0.5 D1–D11 已确认） |
| 状态 | 执行中 |

## 1. 目标

按 DSN v0.5 §12 落地 Excel 生成链路：生成器支持 Excel 数据源、自有仓库自动化脚本、双 CI 工作流、enrich 退役、文档同步。现有 ci.yml 与 JSON 数据源过渡期保留（D5）。

## 2. 交付物

| # | 交付物 | 依据 |
|---|---|---|
| 1 | `tools/generate_manifests.py` 增加 `--excel`（直读 xlsx，D1/D2）、`--xlsx PATH`、`--export-json [PATH]`（快照）；§9 校验规则（违规列出行号退出）；remotes 代理规则（§4）；quickstart 从 config 表读取 | §7/§9/§12.2 |
| 2 | `tools/sync_self_repos.py`（GitHub API 更新自有行，§8 全部 6 条策略；`--dry-run`） | §8 |
| 3 | `tools/validate_manifests_xlsx.py`（§9 校验 + `--normalize` 规范化 + `--export-json`） | §11.1 ②③ |
| 4 | `.github/workflows/excel-validate.yml`（dispatch→建 excel/update-<ts> 分支→校验规范化→单提交推送，不合并不删分支） | §11.1 |
| 5 | `.github/workflows/excel-sync.yml`（dispatch→sync→--excel 重建→--check→git diff 判空提交 `[skip ci]`） | §11.2 |
| 6 | `tools/catalog_to_markdown.py` 优先读 Excel（快照兜底） | §13 |
| 7 | `.pre-commit-config.yaml` 增加 Excel 校验钩子 | §13 |
| 8 | `tools/enrich_catalog.py` 退役删除（D6） | D6 |
| 9 | README/design/implementation/quickstart 改写 + AGENTS.md 补 DSN 文档类型 + LOG-20261128-003 | §12.5 |

## 3. 验收标准

1. `generate_manifests.py --excel` 与 JSON 源产出**逐字节一致**（过渡期双源等价性）；
2. `--export-json` 产出快照且不干扰 JSON 源加载（排除规则）；
3. §9 全部校验可复现（构造违规可退出并列出行号）；
4. sync 脚本 `--dry-run` 对现状 50 自有行给出预期动作清单（不落盘）；
5. 两个 workflow YAML 语法有效，提交身份符合仓库规范；
6. pre-commit 全绿，CI 全绿。

## 4. 边界

- 不合并 PR #1；不删 JSON（D5 过渡保留）；临时脚本用完即删；
- 同步脚本首跑将按 §8 清空自有行 protocol（设计行为，记录于 LOG）。
