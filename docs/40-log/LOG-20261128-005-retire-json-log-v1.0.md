# LOG-20261128-005 JSON 过渡数据退役日志

| 项 | 内容 |
| --- | --- |
| 日期 | 2026-11-28 |
| 执行者 | zeek.zhao（Agent 代执行） |
| 关联 | TSK/PLN-20261128-005 / DSN-20261128-001 决策 D5 |
| 分支 | feat/excel-retire-json（基于 main，PR #4 已合并） |

## 1. 变更记录

1. 删除 `catalogs/` 下 6 个过渡 JSON：zeek-zhao / community-github / community-gitee / community-gitlab / community-yoctoproject / cpp。
2. `.pre-commit-config.yaml`：删除钩子 `generate-manifests-check`（JSON 模式，含 files 过滤行）；`check json` / `pretty format json` 通用钩子保留，现服务于 `manifests-excel-snapshot.json` 格式守护。
3. `.github/workflows/ci.yml`：删除「Generate manifests check」（JSON 模式）步骤；excel 校验由 pre-commit `generate-manifests-excel-check` 覆盖。
4. `README.md`：L14 数据源描述改为「manifests.xlsx 单一事实来源 + manifests-excel-snapshot.json 机器可读快照」；删除过渡钩子说明行。
5. 按用户决策保留：`catalogs/manifests-excel-snapshot.json`（PR 审阅视图）、`generate_manifests.py` JSON 加载代码路径（未来导入工具）、`docs/implementation.md` L90 历史验收记载。

## 2. 验收记录

1. `python3 tools/generate_manifests.py --excel --check`：通过。
2. pre-commit `--all-files`：9 钩子全过。
3. `grep -rn "过渡" README.md`：无遗留。
4. CI：push / pull_request 双绿（push 46055225252 / pull_request 46055236136）。
5. PR #4 合并：本地 --no-ff 合并提交 77d5ea9（身份合规）推送 main，PR 自动标记 MERGED；main CI 绿（run 46056043753）。feat/excel-retire-json 分支保留未删。

## 3. 影响面确认

`tools/sync_self_repos.py`、`tools/validate_manifests_xlsx.py`、`tools/catalog_to_markdown.py`、`excel-sync.yml` 均直读 Excel，不受 JSON 删除影响；`generate_manifests.py` JSON 模式代码保留但仓库内已无 JSON 数据可加载（`--export-json` 快照导出不受影响）。
