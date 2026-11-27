# TSK-20261128-005 JSON 过渡数据退役任务书

| 项 | 内容 |
| --- | --- |
| 日期 | 2026-11-28 |
| 提出人 | zeek.zhao |
| 执行者 | Agent（zeek.zhao 身份） |
| 分支 | feat/excel-retire-json（基于 main） |
| 依据 | DSN-20261128-001 决策 D5；用户 2026-11-28 三项确认：保留快照 / 保留 JSON 加载代码 / 新分支+PR |

## 1. 背景

DSN D5 过渡决策保留的 6 个 `catalogs/*.json` 在 Excel 单一事实来源落地（TSK-20261128-004，PR #1 已合并）后已无数据源职责。本次执行退役。

## 2. 目标

1. 删除 `catalogs/` 下 6 个过渡 JSON（zeek-zhao / community-github / community-gitee / community-gitlab / community-yoctoproject / cpp）。
2. 移除仅服务于 JSON 数据源的校验环节：pre-commit 钩子 `generate-manifests-check`（json 模式）、ci.yml「Generate manifests check」步骤。
3. 文档同步：README 去除「过渡期旧 JSON 保留只读」叙述及对应钩子说明。

## 3. 范围外（不做）

- 不删除 `catalogs/manifests-excel-snapshot.json`（用户决策：保留，作为 PR 审阅用的机器可读视图，excel-sync 继续维护）。
- 不删除 `generate_manifests.py` 的 JSON 加载代码路径（用户决策：保留，留作未来 JSON 批量导入工具）。
- 不改动 `tools/sync_self_repos.py`、`tools/validate_manifests_xlsx.py`、`tools/catalog_to_markdown.py`。
- `docs/implementation.md` 中 TSK-004 验收记录属历史记载，不改写。

## 4. 验收标准

1. `python3 tools/generate_manifests.py --excel --check` 通过。
2. pre-commit 全部钩子（退役后 9 个）通过；CI（push + pull_request）双绿。
3. `grep -rn "过渡" README.md` 无遗留过渡期 JSON 表述。

## 5. 流程

Issue #3（标注分支）→ 本任务书与 PLN 提交 → 退役变更提交 → PR（Closes #3）→ CI 绿后待用户合并。
