# LOG-20261128-007 Excel 模板化与文档重组操作日志

| 项 | 内容 |
| --- | --- |
| 日期 | 2026-11-28 |
| 执行者 | zeek.zhao（Agent 代执行） |
| 关联 | TSK/PLN-20261128-007 |
| 分支 | feat/excel-template-docs-rev（基于 main，PR 已合并） |

## 1. 任务概要

按用户指令完成三项改造：①生成 JSON 中文直出；②manifests.xlsx 模板化（暗色配色、「仓库属性」「标签分类」列、自动统计 sheet）；③文档整理（使用说明、目录分类、ISO 命名统一重命名）。

## 2. 执行记录

1. **代码改造**：`generate_manifests.py`（列清单与 repo dict 键改名 visibility→仓库属性、category→标签分类；快照 `ensure_ascii=False`）、`sync_self_repos.py`（API visibility 映射中文 公开/私有）、`catalog_to_markdown.py`（分类表列名与排序键）、`validate_manifests_xlsx.py`（暗色主题 `_style_sheet`、统计 sheet `_rebuild_stats`、标签下拉引用统计区域）、`.pre-commit-config.yaml`（`pretty-format-json --no-ensure-ascii`）。
2. **数据修复**：发现 TSK-003 知识列填充脚本列号错位（写 col12/13/14，实际应为 11/12/13），11 个新自有仓库的 relations 文本污染了 visibility 列；本轮将 col12/13/14 左移回位（修复 11 行），ai-book 等行读回核验正确。
3. **数据填充**：仓库属性 131 行全覆盖（自有 60 行取自 b730db4 历史快照 API 数据映射中文；71 行 fallback 公开=70 外部行+alpu，外部行历史 JSON 无 visibility 字段、alpu 为 gitee 仓 sync 跳过无 API 数据）；标签分类 131 行全覆盖（50 自有行沿用原 category、81 行规则/显式映射）。
4. **模板与统计**：表头改名后 `--normalize` 注入暗色主题（表头 #37474F 白字、条纹 #ECEFF1）与统计 sheet（总数/公开私有/占比/平台分布/15 分类 COUNTIF 公式；标签下拉引用 `统计!$A$15:$A$29` 单一维护点）。
5. **验收**：131 行仓库属性=公开 88/私有 43；15 分类全覆盖（学习与示例 24/ROS 与机器人 22/嵌入式与驱动 17/C++ 工具与桌面 12/Yocto 与嵌入式构建 8/DevOps 与 CI/CD 8/Web 与前端 8/AI 应用与工具 8/元工具与工程流程 5/博客与知识发布 4/运维与监控 4/独立产品与应用 4/笔记与知识库 3/企业级项目 3/待整理 1）；pre-commit 9 钩子全绿；快照 0 个 `\u` 转义（中文直出）；`--excel --check` 与 `catalog.md --check`（276 行）通过。
6. **文档重组**（git mv，历史可溯）：新建七类目录；quickstart→`00-guide/GUIDE-20261128-002-quickstart-v1.0.md`；TSK/PLN/LOG 各 6 份加 `-v1.0` 归入对应目录；DSN 升 `v1.1` 归 `20-design/`；RPT 归 `50-report/`；pre-commit/design/implementation/manifest-keywords 四份参考改为 `60-reference/REF-20261128-001..004-*-v1.0.md`；`docs/catalog.md` 保留根（工具路径硬编码）。新增 `00-guide/GUIDE-20261128-001-manifest-usage-guide-v1.0.md` 使用说明；DSN 追加 §14 变更记录表；README（目录说明/JSON 中文直出/参考文档链接）与 AGENTS.md §6（七类目录+版本化命名规则）同步更新。
7. **流程**：分支 feat/excel-template-docs-rev → PR（CI 绿）→ 本地 `--no-ff` 合规合并推 main → 分支删除。

## 3. 事故与教训

1. **历史数据错位（TSK-003 埋雷，本轮发现并修复）**：fill_11 脚本按视觉列号写单元格，未对照 REPO_COLUMNS 实际列序，导致 knowledge 列右偏一列。教训：脚本写 Excel 必须以表头名定位列（`row[HEADER.index(col)]`），不得硬编码列号。
2. **validate 首跑报「repos 表缺少列」**：数据脚本只改了值未改表头。教训：列改名须同时改表头与全部数据消费方（本仓为 4 个工具）。
3. **README edit 目标写反一次**：把 catalogs 描述行误换成钩子说明文本，发现后立即恢复并顺带增强（19 列+统计 sheet 描述）。教训：edit 的 old_string/new_string 顺序执行前先自查。

## 4. 遗留

无阻塞遗留。统计 sheet 新增分类时需同步扩下拉引用区间（`--normalize` 可自动重建）。
