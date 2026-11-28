# TSK-20261128-015 全量仓库大小与协议列移除任务书

| 文档编号 | TSK-20261128-015 |
| --- | --- |
| 版本 | v1.0 |
| 日期 | 2026-11-28 |
| 作者 | zeek.zhao（Agent 代笔） |
| 关联 | TSK-20261128-014 / GUIDE v1.2 |
| 状态 | 已完成 |

## 1. 需求（用户 m01926）

1. **全部仓库大小（MB）**：为所有仓库获取仓库大小，用于判断浅拷贝/深拷贝；协议一律只用 HTTPS——删除「协议」列，「仓库属性」列移到原「协议」位置。
2. **列宽优化**：窄字段列（仓库属性等）调窄，整表尽量一页可视。
3. **汇总统计**：表格末尾统计所有仓库大小总和。
4. **新增仓库自动填充工作流**：引入新仓库时自动抓取并填全可自动获取字段（大小、属性等）。

## 2. 设计决策

- **D-1 协议列删除与 HTTPS 统一**：REPO_COLUMNS 移除 protocol（18→17 列）；生成器 remote 名一律 `{platform}_https`（含 quickstart 示例仓），`get_effective_protocol`/owner 级协议配置退役；受影响外部仓 6 行（原 protocol=git）行为变化已获用户明示（"协议一律只用 HTTPS"）。仓库属性列移至第 5 列（原协议位），列序变为 name/path/branch/platform/**仓库属性**/topic/language/groups/linkfiles/description/purpose/contents/relations/标签分类/仓库大小(MB)/suggested_action/note。
- **D-2 全量大小**：github 91 仓 90 有值（orgflow-devops1 上游已删 404，常态留空）；gitee api v5 repo 端点无 size 字段、gitlab.com 公开 API 不返回 statistics、yoctoproject cgit 无 HTTP API——40 行外部仓留空并在 REF-008 记录平台可得性矩阵（浅拷贝判断：github 全覆盖，gitee 仓为教程/文档类小仓可默认浅拷贝）。
- **D-3 汇总行**：repos 表末数据行+1 写「合计」行（name 列=合计、仓库大小(MB) 列=SUM 公式、加粗）；四工具（generate/sync/validate/stats）按 `name=="合计"` 哨兵跳过；sync 新仓插入到合计行之前。
- **D-4 列宽分级**：长文本列（wrap 集合）封顶 26；普通列封顶 18；窄值列（branch/platform/仓库属性/标签分类/仓库大小(MB)/suggested_action）按内容+2 无下限放大。
- **D-5 统计公式列位动态化**：_rebuild_stats 的 COUNTIF 列字母由表头 index 动态计算（仓库属性 E、标签分类 N），避免再犯列位硬编码事故。
- **D-6 自动填充工作流**：tools/autofill_repos.py——对 github 平台行的空字段（branch/platform/description/仓库属性/仓库大小/language）逐行调 GitHub API 填充，`--repo owner/repo.git` 可只处理单行，`--dry-run` 预览；标签分类/purpose 等知识列仍人工（工作流输出建议不自动写知识列）。新 workflow `.github/workflows/excel-autofill.yml`（workflow_dispatch + repo 入参）：autofill→normalize→generate→--check→有变更自动提交；GH_ACTIONS 环境无 LLM 凭证，采用规则+API 自动化并如实标注（非 LLM 推断）。

## 3. 验收标准

- 协议列不存在；仓库属性位于第 5 列；全表 17 列
- 仓库大小(MB) 列 github 仓全覆盖（除上游已删 1 行）；repos 表末尾有合计行（SUM 公式）
- zip 层验证：无协议 DV、仓库属性 DV 在 E 列、合计行存在且公式正确、AF 范围正确
- normalize/generate --check/validate/catalog.md --check/9 钩子全绿；PR→CI→--no-ff 合并→LOG-015
