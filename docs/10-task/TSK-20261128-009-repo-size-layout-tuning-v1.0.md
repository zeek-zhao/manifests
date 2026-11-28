# TSK-20261128-009 仓库大小/紧凑布局/下拉修复/三行结构/英文属性/维度精简

| 文档编号 | TSK-20261128-009 |
| --- | --- |
| 版本 | v1.0 |
| 日期 | 2026-11-28 |
| 编制 | zeek.zhao（Agent 代笔） |
| 审核 | 用户（授权沿用现有流程，执行完毕后汇报） |
| 状态 | 执行中 |
| 分支 | feat/repo-size-layout-tuning（基于 main） |

## 1. 需求（用户七项指令）

1. 通过 API 统计各仓库大小并补充到现有数据；
2. manifests.xlsx 列宽紧凑化 + 长文本列单元格内换行；
3. 修复标签分类下拉可选项（确保实际打开文件生效）；
4. 表结构调整：第 1 行标签名称、第 2 行解释说明、第 3 行起数据；
5. 仓库属性统一英文（public/private）；
6. 评估分组/标签维度意义，说明理由后执行合并/删除；
7. GUIDE 使用说明同步完善。完成后 PR 合并，更新 catalog.md 与日志。

## 2. 技术决策（D-1~D-8）

- D-1 **size 列**：新增「仓库大小(KB)」列，插在「标签分类」之后（col16，不挪 仓库属性/标签分类 的 N/O 列位，统计公式稳定）。数据源：github→`GET /repos/{o}/{r}`（`size`，KB，token 认证）；gitee→`GET /api/v5/repos/{o}/{r}`（公开仓免认证，限速串行）；gitlab.com→公开 API 不含 statistics，留空；yoctoproject→无公开 API，留空。留空行 note 不加（列头说明即可）。sync 自有行后续刷新该列。
- D-2 **三行结构**：repos/remotes/config 三个数据表统一为 1=表头、2=列说明、3=数据。`load_from_excel`/`sync`/`validate`/`normalize`/统计公式（COUNTA 减 2）全部同步；readme/统计 表不动。列说明文案取自现有字段字典。
- D-3 **英文化**：仓库属性值域 `public/private`（Excel 数据、下拉、统计公式、sync API 映射、build_groups 派生组 `visibility-public/private`、REF/GUIDE 文档同步）。sync 直接存 API 原值。
- D-4 **下拉修复**：命名区域在部分 Excel/WPS 版本仍不解析 → normalize 同时生成**内联枚举下拉**（formula1 为逗号串，从统计表分类清单动态生成，单一维护点不变）+ 保留 TagCategories 命名区域，双保险。
- D-5 **列宽**：自适应收紧为 `min(内容宽+2, 28)`；长文本列（description/purpose/contents/relations/suggested_action/note/说明行）固定 28 宽 + `wrap_text=True`；行高不设固定值（打开自动）。
- D-6 **维度精简（先评估后执行）**：删除 `by-protocol` 维度（理由：协议是 remote 配置属性而非选仓维度，default.xml 已含全部；git.xml 仅 6 仓价值低）；「待整理」标签 1 行归位；其余维度（topic 17/language 7/platform 4/owner 1）保留（单例 topic 亦是有效筛选入口）。评估全文落 REF-006。
- D-7 快照列清单同步加 size 字段；catalog.md 明细表加「仓库大小(KB)」列。
- D-8 迁移脚本按表头名定位列操作（吸取 TSK-003 列号硬编码教训），用完即删。

## 3. 验收标准

- Excel 打开：三行结构可见（第 2 行为灰字说明）、标签分类下拉在任何主流版本可选出 15 项、列宽紧凑、长文本换行、仓库属性全为 public/private、size 列有值（github/gitee 全覆盖，gitlab/yoctoproject 留空）。
- 生成器/校验器/同步器/markdown 四工具全绿；`--excel --check`、`catalog.md --check` 通过；CI 双绿；合并后 main CI 绿。
- by-protocol 目录不再生成；统计公式计数正确（131）。
