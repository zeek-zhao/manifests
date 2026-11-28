# PLN-20261128-009 repo-size-layout-tuning 落地计划

| 文档编号 | PLN-20261128-009 |
| --- | --- |
| 版本 | v1.0 |
| 日期 | 2026-11-28 |
| 编制 | zeek.zhao（Agent 代笔） |
| 状态 | 执行中 |
| 关联 | TSK-20261128-009 |

## 里程碑

M1 侦察（本计划内完成）：核实现状结构——repos/remotes/config 表均 1 行表头；下拉 sqref=O2:O1000 f1=TagCategories；统计公式 B3=COUNTA(repos!$A:$A)-1、B4/B5=COUNTIF(N,公开/私有)；by-protocol 2 文件（git 6 行/https 131 行）。

M2 文档先行：TSK/PLN-009（本提交）。

M3 代码改造（分支 feat/repo-size-layout-tuning）：
- generate_manifests：REPO_COLUMNS+仓库大小(KB)、load_from_excel 三行制（DATA_START=3）+cells 映射、build_groups 英文派生组（动态跟随列值）、export_snapshot；
- sync_self_repos：数据起始行 3、visibility 直存 API 原值、size 列刷新；
- validate_manifests_xlsx：三行制（说明行写入+条纹/DV 从 3 起）、内联枚举下拉+命名区域双保险、统计公式改（COUNTA-2、COUNTIF public/private、文案）、列宽收紧+wrap_text；
- catalog_to_markdown：DETAIL_COLUMNS+size 列。

M4 Excel 迁移（/tmp 脚本按表头名定位）：三表插说明行（row2 insert）、公开/私有→public/private（含统计公式值）、插 size 列 col16、131 行填 size（github 91 token 认证/gitee 28 免认证串行/gitlab 8 与 yocto 4 留空）、「待整理」1 行归位、normalize 重刷。

M5 维度精简：删 by-protocol 生成分支（generate_manifests INCLUDE/维度循环）+ 迁移脚本删除旧 by-protocol 产物；REF-006 评估报告（含保留/删除理由）。

M6 文档：GUIDE 同步（三行结构/size 列/英文化/下拉说明/维度精简）；README 目录说明行；DSN v1.3 变更记录。

M7 流程：全量校验（9 钩子/--check×2）→ push → PR → CI 双绿 → 本地 --no-ff 合规合并 → LOG-009 → 汇报（含 size 统计与维度精简理由）。

## 风险与对策

- R1 三行结构破坏 sync 首行判定（obsidian 双行去重逻辑 row 范围）→ 起始行参数化 DATA_START=3，dry-run 复核 60→预期动作数。
- R2 说明行插入后 COUNTA 基数变化 → 统计公式同步改，用生成后读回断言 B3=131。
- R3 gitee 免认证限速 → 串行 sleep 0.6s，失败重试 1 次仍失败留空并记录。
- R4 删除 by-protocol 后 --check 对旧产物误报 → 迁移脚本同步删除 manifests/generated/by-protocol 目录。
