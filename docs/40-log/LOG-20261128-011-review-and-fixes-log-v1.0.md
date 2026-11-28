# LOG-20261128-011 复查与修复执行日志

| 文档编号 | LOG-20261128-011 |
| --- | --- |
| 版本 | v1.0 |
| 日期 | 2026-11-28 |
| 作者 | zeek.zhao（Agent 代笔） |
| 关联 | TSK-20261128-011 / PLN-20261128-011 |
| 状态 | 已完成 |

## 1. 复查结论（R1–R8）

见 TSK-20261128-011 §2。关键根因：**下拉框失效并非内联枚举串问题**——XML 中 5 个 DV（E/N/Q/D/O 列）均存在、formula1 合法、`showDropDown="0"`（OOXML 语义=显示箭头）正常，真正原因是 **sqref 范围为第 3 行起**，不含用户点击的第 1 行表头。

## 2. 修复明细

1. validate_manifests_xlsx.py：DV 两处 `dv.add` 改为 `{letter}1:{letter}1000`；新增 `README_ROWS`（15 条）与 `_refresh_readme()`，normalize 时重写 readme sheet（A.流程/B.结构/B.字典/C.指引，与三行结构、public/private 值域、仓库大小列、动态统计 sheet、双轨分工、excel-sync 删行行为同步）。
2. sync_self_repos.py：主循环改倒序 `range(max_row, 2, -1)`；上游消失分支由「note 追加」改为 `ws.delete_rows(r)`（认证列表唯一真源）；GONE_NOTE 常量删除；docstring 同步。
3. 数据：orgflow-devops1 行（repos L118）删除；orgflow-devops 的 relations 由「…orgflow-devops1 为其副本（待去重）…」修正为「orgflow-jenkins 为其 Jenkins API 层；devops 杂项待并入」。
4. 重生成：normalize → stats_report（130 行、89/90 github 仓有指标）→ generate --excel → catalog.md（274 行）→ 快照导出；4 个维度文件（by-platform/github、by-topic/devops、by-language/python、by-owner/zeek-zhao）随重建不再含 orgflow-devops1。

## 3. 验证

- XML 解包：5 个 DV sqref = E1/N1/Q1/D1/O1 + `:1000`，全部含第 1 行 ✓
- readme sheet 15 行新文案 ✓；动态统计 4 图表保留、132 行（130 数据）✓
- orgflow-devops1 零残留（manifests/、catalog.md、快照数据行；知识列描述已修正）✓
- `--excel --check` / `validate` / `catalog.md --check` 全过 ✓；pre-commit 9 钩子全绿 ✓；CI 双绿：push run 46126440189 / pull_request run 46126485089；合并提交 7dcc6c8 已推送 main（b13dc5d..7dcc6c8，ls-remote 核验送达）。

## 4. 事故与教训

1. **stats_report 匿名调用触发 403 限流**：重生成链首次运行未 export GH_TOKEN，匿名 60/h 限额在 32/90 仓时耗尽；补 token 后重跑 89/90 正常。教训：stats_report 与 sync 同样依赖 GH_TOKEN/GITHUB_TOKEN，重生成链执行时必须携带（excel-sync workflow 已内置 secrets.GH_PAT，不受影响）。
2. **grep 残留误报**：快照中出现 orgflow-devops1 命中实为 orgflow-devops 知识列 relations 的描述文字（非数据行），顺带修正——复查「字符串残留」时需区分数据行与知识列文本。
3. alpu 维持现状（language=c/c++，标签空、groups/topic=linux），无动作（用户指令）。
