# LOG-20261128-014 表头筛选（AutoFilter）执行日志

| 文档编号 | LOG-20261128-014 |
| --- | --- |
| 版本 | v1.0 |
| 日期 | 2026-11-28 |
| 作者 | zeek.zhao（Agent 代笔） |
| 关联 | TSK-20261128-014 / PLN-20261128-014 |
| 状态 | 已完成 |

## 1. 交付

1. **表头筛选**：repos(A1:R132)/remotes(A1:D6)/config(A1:C7)/readme(A1:B15) 由 normalize 设置 AutoFilter；动态统计(A1:H131) 由 stats_report 设置。点击表头箭头=筛选菜单（列内去重值+勾选过滤行），Excel/WPS 原生行为。
2. **DV 收缩**：26 个 DV（repos 18/remotes 3/config 3/readme 2）sqref 全部改为 `X3:X1000` 单段；第 1 行不再挂 DV（消除 DV 箭头与筛选箭头的位置冲突）；第 2 行依旧排除。
3. **x14 幽灵 DV 清理**：`_sanitize` 剥除含 x14:dataValidations 的 extLst 块；`_verify` 新增「无 x14 残留」断言。
4. **自检升级**：openpyxl 层断言 DV sqref 无第 1/2 行段 + AF 存在；zip 层断言 AF 1-4 必备 A1 锚定、DV 段格式 X3:X1000。

## 2. 验证

- zip 终验 PASS：sheet1-5 AF 齐、DVn=18/3/3/2/0、非法段=[]、x14=False、showDropDown=False。
- `--excel --check` / `validate` / `catalog.md --check` 全过；catalog.md 274 行不变；快照字节不变；manifests/ 零变化——**数据零漂移**（纯交互层变更）。
- stats 89/90 github 仓有指标（orgflow-devops1 404 常态留空）。

## 3. 事故与教训

1. **x14 幽灵 DV**（本轮新发现）：normalize 清空标准 DV 重建后 `_verify` 仍报「sqref=A1」——实证旧 DV 的 **x14 扩展副本**（extLst）被 openpyxl 往返保留，`ws.data_validations` 清理不触及 extLst。修复=sanitize 剥块+verify 断言。教训：openpyxl 对 DV 的写出存在「标准 dataValidation + extLst x14 副本」两条路径，清理必须两者兼顾；zip 层正则需区分两者（`<dataValidation\b` 不匹配 `<x14:dataValidation`，而全文 `sqref=` 匹配会误伤）。
2. **`--output manifests` 嵌套目录**：generate 的 plan 键自带 `manifests/` 前缀，`--output` 应使用默认仓库根；误传导致写入 `manifests/manifests/` 并使 `--check` 全文件不匹配（输出目录自身 vs 磁盘目录）。修复=删除垃圾目录、按默认用法重跑。教训：check 「全文件不匹配」先怀疑输出根目录错位，而非数据漂移。
3. AutoFilter 筛选菜单会包含第 2 行说明文本（客户端以第 1 行为表头、其余皆数据）——固有限制，GUIDE 注记。
