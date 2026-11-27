# PLN-20261128-005 JSON 退役落地计划

| 项 | 内容 |
| --- | --- |
| 关联 | TSK-20261128-005 |
| 分支 | feat/excel-retire-json |
| 确认 | 用户 2026-11-28 确认三项决策点（快照保留 / 加载代码保留 / 新分支+PR） |

## 步骤

1. 本分支提交 TSK/PLN-005。
2. `git rm` 6 个过渡 JSON；保留 snapshot。
3. `.pre-commit-config.yaml`：删除钩子 `generate-manifests-check`（json 模式）；`check json` / `pretty format json` 两通用钩子保留（现服务于 snapshot）。
4. `.github/workflows/ci.yml`：删除「Generate manifests check」（JSON 模式）步骤，pre-commit 步骤已含 excel 校验。
5. `README.md`：L14 数据源描述改为「xlsx 单一事实来源 + snapshot 机器可读视图」；L39 删除过渡钩子行。
6. 新增 `docs/LOG-20261128-005-retire-json-log.md`。
7. 本地验收：`--excel --check`、pre-commit 全钩子、grep 无「过渡」遗留。
8. 开 Issue #3（标注分支）→ 推送分支 → PR #2（Closes #3，base main）→ CI 双绿后交用户合并。

## 风险与对策

- 风险：删除 JSON 后若有隐藏消费者（脚本/文档）引用 catalogs/*.json → 已 grep 全库确认仅历史文档提及；validate/excel-sync/markdown 工具均直读 Excel，无影响。
- 风险：钩子数量变化导致 CI 缓存混淆 → 无状态风险，pre-commit --all-files 全量执行。
