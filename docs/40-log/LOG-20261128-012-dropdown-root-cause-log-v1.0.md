# LOG-20261128-012 表头下拉框根因修复执行日志

| 文档编号 | LOG-20261128-012 |
| --- | --- |
| 版本 | v1.0 |
| 日期 | 2026-11-28 |
| 作者 | zeek.zhao（Agent 代笔） |
| 关联 | TSK-20261128-012 |
| 状态 | 已完成 |

## 1. 排查过程

1. 前两轮修复仅核对了「sqref 是否含第 1 行」（TSK-011 已修对）与「内联枚举串合法性」，均在 XML 层面成立——但用户端仍无下拉，说明真因在这些检查覆盖不到的属性上。
2. 本轮按要求用 Excel 检查工具实际打开文件：rw_download 至本地镜像后，openpyxl 读回 + zip 原始 XML 双源核对，逐项检查 DV 数量（5，无重复）、sqref（O1:O1000 等）、formula1（115 字符、引号包裹、14 项无逗号冲突）、allowBlank、showDropDown。
3. 发现 `showDropDown="0"` 被显式写出；对照实验证明 openpyxl 3.1.5 无论参数如何均强制写出该属性（参数省略/显式 False/读回往返，三种场景保存后 XML 均含 `showDropDown="0"`）。
4. 定性：Excel 反相语义（0=显示箭头）掩盖了问题；WPS 等按字面义（0=不显示）→ 用户端无下拉。TSK-009 引入该属性、TSK-011 修复未触及，属于**跨实现兼容性陷阱**。

## 2. 修复与验证

- `_sanitize_dropdowns`：保存后 zip 重写剥除全部工作表的 `showDropDown` 属性；`_verify_dropdowns`：自检三断言（无属性/自第 1 行起/内联串合法），失败即抛错——normalize 自此自带回归防护。
- excel-sync.yml 插入 normalize 步骤于 stats_report 之后（往返实验证明 openpyxl load→save 会把属性写回，normalize 必须最后写）。
- 本地重生成：normalize（自检过）→ generate → catalog.md（274 行）→ 解包断言 5 个 DV 均无 `showDropDown`、sqref 含第 1 行。
- 全量复查：`--excel --check`/`validate`/`catalog.md --check` 过；快照字节不变；4 图表保留；readme 30 格（15 行）；TagCategories 统计!$A$15:$A$28 14 类；动态统计 132 行、属性列值域纯 public/private；orgflow-devops1 零残留；维度文件 29 个与 default.xml 引用集完全一致。

## 2.1 CI 与合并记录

- PR #11 CI 双绿：push run 46127708126 / pull_request run 46127746563
- 合并提交 e052796 已推送 main（1126f13..e052796，ls-remote 核验送达后才删分支）；PR #11 状态 MERGED（2026-11-28T08:53:06Z）

## 3. 复查发现与清理（遗漏清单）

1. `manifests/generated/by-language/linux.xml`：TSK-010 将 5 个误填 linux 的 language 修正后，该文件无成员且不被 default.xml 引用——stale 残留，已 `git rm`（generate 不自动删除 stale 产物属已知设计，清理依赖任务书动作，GUIDE/LOG 已提示）。
2. 其余无遗漏（R 清单全过）。

## 4. 教训

1. **跨 Excel/WPS 属性语义分歧必须以「属性省略」为兼容写法**；openpyxl 强制写出的属性只能 zip 后处理解决。
2. **xlsx 的最后写入者决定 DV 属性状态**——任何 openpyxl 往返都会重写 DV 属性；normalize 后置是流程性防线（已固化进 excel-sync 编排与 GUIDE）。
3. GUI 不可达时，「XML 合法」≠「用户可见可用」：验证要以目标客户端的实际渲染语义为准（本例靠属性语义分歧分析破案）。
