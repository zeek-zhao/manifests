# TSK-20261128-012 表头下拉框根因修复与全量复查任务书

| 文档编号 | TSK-20261128-012 |
| --- | --- |
| 版本 | v1.0 |
| 日期 | 2026-11-28 |
| 作者 | zeek.zhao（Agent 代笔） |
| 关联 | TSK-20261128-011（前两轮修复未根治）/ GUIDE v1.2 |
| 状态 | 已完成 |

## 1. 背景

用户报告表头下拉框问题仍存在（TSK-011 修复无效），要求使用 Excel 检查工具实际打开文件排查真因，修复后重新生成并验证，同时全量复查文件与维度文件、catalog.md、日志。

## 2. 根因（本轮实证）

双源检查（openpyxl 读回 + zip 原始 XML）证实：sqref 已含第 1 行、内联枚举串合法（115 字符、双引号包裹、无重复 DV、无逗号/引号冲突）。**真因**：

```xml
<dataValidation sqref="O1:O1000" showDropDown="0" ... type="list">
```

openpyxl 3.1.5 **无论是否传 `showDropDown` 参数都会强制写出该属性**（对照实验：新建 DV 参数省略/显式 False，保存后 XML 均含 `showDropDown="0"`）。该属性语义分歧：

- **Excel**：反转语义，`0`=显示下拉箭头（Excel 用户未见异常）
- **WPS 等**：按标准字面义，`0`=不显示下拉 → **无下拉框**

唯一双兼容写法是**整体省略该属性**（两端缺省均为显示）——openpyxl 参数层面做不到，必须 zip 后处理。

## 3. 修复

1. `validate_manifests_xlsx.py --normalize`：保存后新增 `_sanitize_dropdowns()`（zip 重写剥除所有工作表的 `showDropDown="0|1"`）与 `_verify_dropdowns()`（自检断言：属性不存在 / repos 的 list DV 全部自第 1 行起 / 内联串双引号包裹；任一失败抛 ValueError）。
2. `excel-sync.yml`：normalize 步骤插到 stats_report 之后、generate 之前——**normalize 必须是工作簿最后一个写入者**（sync/stats_report 的 openpyxl 往返会把该属性写回，往返实验已证实）。
3. 遗留清理：`git rm manifests/generated/by-language/linux.xml`（TSK-010 修正 language 后该文件无成员，磁盘 stale 且不被 default.xml 引用）。
4. GUIDE v1.2 补兼容性要点与「normalize 最后写入者」规则。

## 4. 验收标准

- 提交内 xlsx 解包：5 个 DV 均无 `showDropDown` 属性、sqref 含第 1 行、formula1 合法
- normalize 内置自检通过；`--excel --check` / `validate` / `catalog.md --check` 通过
- 维度文件集与 default.xml 引用集一致（29 文件）；快照字节不变；4 图表保留
- pre-commit 9 钩子绿；PR CI 绿
