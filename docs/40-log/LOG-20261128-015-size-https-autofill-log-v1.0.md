# LOG-20261128-015 全量大小与协议移除执行日志

| 文档编号 | LOG-20261128-015 |
| --- | --- |
| 版本 | v1.0 |
| 日期 | 2026-11-28 |
| 作者 | zeek.zhao（Agent 代笔） |
| 关联 | TSK-20261128-015 / PLN-20261128-015 |
| 状态 | 已完成 |

## 1. 交付

1. **协议列删除与 HTTPS 统一**：repos 表 18→17 列；仓库属性移至第 5 列（原协议位）；生成器 remote 一律 `{platform}_https`（_remotes.xml 的 4 个 *_git remote 定义移除；quickstart 示例仓 zeek-zhao/docker-sample 由 github_git→github_https；obsidian markdown 分支行同步切换）；快照 protocol 键 0 残留；config 表 default_protocol 键删除（生成器统一 https，不再读该键）。
2. **全量仓库大小**：github 90 行 89 有值（orgflow-devops1 上游已删 404 常态留空）；gitee/gitlab/yoctoproject 40 行平台无公开 size API，留空——平台可得性矩阵与浅/深拷贝建议见 REF-20261128-008。
3. **合计行**：repos 表末尾第 133 行「合计」+ `=SUM(O3:O132)`（加粗）；`--normalize` 幂等重建；generate/sync 按哨兵跳过（sync 新行插入合计之前）；validate/stats 不受影响。
4. **列宽三级**：长文本列 26 封顶（wrap）/普通列 18/窄值列按内容（仓库属性 10、language 12、topic 13、branch/platform 14），说明行文本不参与列宽计算，整表总宽 384→332 字符单位。
5. **excel-autofill 工作流**：tools/autofill_repos.py（github 行空字段 API 填充：branch/platform/description/仓库属性/仓库大小/language 映射，--repo/--dry-run，知识列永不自动填）+ .github/workflows/excel-autofill.yml（dispatch+入参，autofill→normalize→generate→check→差异提交）。
6. 文档：GUIDE（17 列表/合计行/autofill §3.1/FAQ 协议问答改写）、README 工具行、REF-008 新立。

## 2. 验证

- zip 解包：17 列表头无 protocol、仓库属性 DV 在 E 列、合计行公式正确、AF=A1:Q133、DV 全部 X3:X1000、无 showDropDown/x14。
- 列宽抽查 PASS（仓库属性 10/长文本 26/说明行不撑宽）。
- stats 89/90（GH_TOKEN）；--excel --check / validate / catalog.md --check / pre-commit 9 钩子全绿；快照重导出（130 仓、无 protocol）。

## 3. 事故与教训

1. **stats_report 本地跑漏 GH_TOKEN**：匿名限额耗尽 90 连 403，动态统计 sheet 指标被清空写入（0/90）——重跑带 token 恢复 89/90。教训：stats_report 在无 token 时应拒绝清空数据（fail-safe），至少 `--dry-run` 默认；工作流侧有 secrets.GH_PAT 不受影响。
2. **列宽三级首版 WRAP 分支复用被 18 截断的底数**：长文本列反被压到 18——修复为分支独立计算（WRAP 用原始 cjk+2 参与截断）。教训：分级逻辑各分支应从原始值独立推导，不得链式复用已截断中间量。
3. 说明行（row2）文本曾把窄列（仓库属性等）撑宽到 18——_tight_widths 跳过 row2 后窄列回归内容宽度（10）。

## 4. CI 与合并记录

- PR #14 CI 双绿：push run 46137846870 / pull_request run 46137894949
- 合并提交 06340f1 已推送 main（f76ad18..06340f1，ls-remote 核验送达后才删分支）；PR #14 状态 MERGED（2026-11-28T11:03:13Z）
