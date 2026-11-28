# LOG-20261128-016 gitee 镜像替换执行日志

| 文档编号 | LOG-20261128-016 |
| --- | --- |
| 版本 | v1.0 |
| 日期 | 2026-11-28 |
| 作者 | zeek.zhao（Agent 代笔） |
| 关联 | TSK-20261128-016 / REF-20261128-009 / PLN-20261128-016 |

## 1. 概述

按用户决策（A+B+C 同意、was666/as-editor 删除）将 18 个 gitee 镜像行替换为 GitHub 原版（platform→github、name 改原版全名），删除 as-editor 行；本地检出 path 全部不变。

## 2. 执行记录

1. 阶段一探测：ls-remote sha 对比 + 同名/org 映射 + Search 兜底（REF-009 §1-§6）。
2. 阶段二迁移脚本一次通过：replaced=18/18、deleted=1/1、0 错误；branch/仓库属性/仓库大小(MB)/language/description 按 GitHub API 刷新；path/groups/topic/知识列未动。
3. 重生成链：stats_report（GH_TOKEN，107/108 有指标）→ normalize（129 repositories, 4 platforms, owners=[zeek-zhao]）→ generate --excel → --check exit 0 → 快照 → catalog.md 272 行（--check 过）。
4. 产物核验：by-platform gitee 28→9、github 90→108、gitlab 8、yoctoproject 4；合计行 SUM(O3:O131)；新增 language slug vue×3、vim-script×1。
5. 文档：REF-009 §9 执行记录、REF-008 gitee 口径注记、TSK-016 状态、本日志。
6. pre-commit 9 钩子全绿。

## 3. 事故与教训

1. **首跑零匹配**：迁移脚本映射键未带 `.git` 后缀，与表内 name（含 .git）不一致 → replaced=0/deleted=0（无写入，表未受影响）。教训：跨系统标识匹配前先核对存储形态（本表 name 列含 `.git` 后缀），断言 replaced>0 而非只看 exit 0。
2. **首行删除后行号偏移**：as-editor 删除（行 23）使后续行号上移，脚本采用「边遍历边删」且删除后不递增行号避免跳行；实际仅 1 行删除无叠加风险。
3. REF-008 口径注记采用首处替换，精度有限（后续文档变更用编辑定位而非整段 replace）。

## 4. 验收结论

| 项 | 结果 |
| --- | --- |
| 替换/删除 | 18 替换 + 1 删除，0 错误 |
| 生成物一致性 | --excel --check exit 0 |
| 校验 | validate OK（129 仓）、catalog.md --check 过、9 钩子绿 |
| 平台分布 | gitee 9 / github 108 / gitlab 8 / yoctoproject 4 |

## 5. 遗留

- D 级 9 行维持 gitee（理由见 REF-009 §6）；AllOpenOS/linux0.11_note 疑似私有，建议人工确认可见性。
- C 级替换基于用户授权（「abc 同意」），其中 imx6ull/stm32mp157 为名称差异仓，若后续发现不同源可按同流程回退。
