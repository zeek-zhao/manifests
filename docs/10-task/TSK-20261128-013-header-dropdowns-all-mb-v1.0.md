# TSK-20261128-013 全表头下拉与大小单位统一任务书

| 文档编号 | TSK-20261128-013 |
| --- | --- |
| 版本 | v1.0 |
| 日期 | 2026-11-28 |
| 作者 | zeek.zhao（Agent 代笔） |
| 关联 | TSK-20261128-012（showDropDown 兼容机制）/ GUIDE v1.2 |
| 状态 | 已完成 |

## 1. 需求

1. **全表头下拉**：manifests.xlsx 第 1 行**每一列**表头均具备可点选下拉（沿用内联枚举串 DV 逻辑；规避 showDropDown 跨客户端问题——normalize zip 剥属性机制保持）。值域基于现有维度值自动生成。
2. **第 2 行排除**：下拉仅覆盖第 1 行表头与第 3 行起数据区；第 2 行说明行不纳入下拉范围（sqref 双段：`X1` + `X3:X1000`），内容不动。
3. **大小单位统一 MB**：「仓库大小(KB)」列改为「仓库大小(MB)」，值按 1024 折算保留 1 位小数；生成器/同步/统计/图表/快照/catalog.md/文档同步。

## 2. 关键设计决策

- **D-1 内联 255 字符上限**：Excel DV formula1 内联串硬上限 255 字符。值域序列化后 ≤255 的列用内联（branch/protocol/platform/topic/language/groups/仓库属性/标签分类/linkfiles 等）；超限列（name/path/description/purpose/contents/relations/note/仓库大小(MB)/suggested_action 视长度）自动改走**「下拉源」辅助 sheet**（normalize 按数据全集重建）+ 命名区域引用（`RepoNames` 等）。命名区域跨表 DV 在 Excel/WPS 均受支持（TSK-008 已引入 TagCategories 先例，无兼容反馈；TSK-012 证明历史问题仅 showDropDown 属性）。
- **D-2 DV 覆盖矩阵**：repos 18 列 + remotes 4 列 + config 3 列 + readme 2 列全配（normalize 管理）；「动态统计」sheet 表头由 stats_report 配 DV（内联短枚举+命名区域引用），因该 sheet 由工具全量重建、normalize 不触碰；「统计」sheet 为区块型版面无标准表头，不适用（记录于 LOG）。
- **D-3 自适应机制**：`_apply_formatting` 重构为逐列遍历：值域=数据全集去重（排除说明行），`len('"' + ",".join(values) + '"') <= 255` 则内联，否则写下拉源 sheet 列 + DefinedName + DV 引用。
- **D-4 MB 折算**：`round(kb/1024, 1)`；load 校验放宽为正浮点；sync 直写 `round(api_size/1024, 1)`；stats_report 列名 size_MB、图表标题同步。
- **D-5 自检扩展**：`_verify_dropdowns` 断言升级：四表每列 DV 覆盖第 1 行、第 2 行不在 sqref、无 showDropDown、formula1 合法（内联 ≤255 或命名区域已定义）。

## 3. 交付物

validate_manifests_xlsx.py（DV 矩阵+下拉源 sheet+自检）、generate_manifests.py（列名/校验）、sync_self_repos.py（MB 直写）、stats_report.py（MB+表头 DV）、catalog_to_markdown.py（表头）、GUIDE/README 单位与机制更新、TSK/PLN/LOG-20261128-013、Excel 迁移+全量重生成。
