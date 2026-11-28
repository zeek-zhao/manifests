# LOG-20261128-013 全表头下拉与 MB 单位执行日志

| 文档编号 | LOG-20261128-013 |
| --- | --- |
| 版本 | v1.0 |
| 日期 | 2026-11-28 |
| 作者 | zeek.zhao（Agent 代笔） |
| 关联 | TSK-20261128-013 / PLN-20261128-013 / GUIDE v1.2 |
| 状态 | 已完成 |

## 1. 交付内容

1. **全表头下拉（用户需求①②）**：`validate --normalize` 的 DV 逻辑重构为逐列自适应矩阵——repos 18 列 + remotes 4 列 + config 3 列 + readme（normalize 管辖四表），每列第 1 行表头均可点选：
   - 结构化列值域：protocol=[https,git]、platform=数据全集、仓库属性=[public,private]、标签分类=TAG_CATEGORIES 14 类、suggested_action=[保留,更新,待确认,废弃]、topic/groups/language/branch=数据全集；
   - 自由文本列（name/path/description/purpose/contents/relations/linkfiles/note 等）与空值域列（note 现为空）配「（自由填写）/（暂无可选项）」占位枚举；
   - 值域超 255 字符（Excel 内联硬上限）自动写「下拉源」辅助 sheet + `DD<n>` 命名区域引用（当前 DD1=仓库大小(MB) 列）；
   - sqref 全部为 `第1行 + 第3行:1000` 双段，**第 2 行说明行零污染**（内容未动）。
2. **仓库大小单位 MB（用户需求③）**：列头 `仓库大小(KB)`→`仓库大小(MB)`；90 行数据 round(KB/1024,1) 迁移；generate 校验改 float 非负；sync 刷新与新行默认值均按 MB；stats_report（size_MB/Top15/图表标题）、catalog_to_markdown、快照列序、GUIDE 文案同步。catalog.md 重生成 274 行。
3. **自检升级**：`_verify_dropdowns` 断言=无 showDropDown 属性 + sqref 全表无第 2 行段 + repos 的 list DV 全部含第 1 行段 + formula1 unescape 后内联 ≤255 或为已定义的 `DD<n>` 引用。

## 2. 验证（实际打开语义层）

- 解包终态：**showDropDown=0 次**（Excel/WPS 双端均显示箭头，TSK-012 机制生效）；26 个 list DV 全部双段 sqref 含第 1 行；第 2 行污染=0；内联超 255=0；DD1 已定义且被引用。
- openpyxl 读回 DV 数==表头列数；`--excel --check`、`validate`、`catalog.md --check` 全过；快照重导出；stats 89/90 github 仓有指标（orgflow-devops1 上游已删 404 常态留空）。

## 2.1 CI 与合并记录

- PR #12 CI 双绿：push run 46130705560 / pull_request run 46130740992
- 合并提交 e72b854 已推送 main（b6cc7c0..e72b854，ls-remote 核验送达后才删分支）；PR #12 状态 MERGED（2026-11-28T09:31:44Z）

## 3. 事故与教训

1. **自检误报 626**：normalize 反复失败于「内联 >255 字符 (626)」，但解包显示全部合规——monkeypatch 抓现场实证：**openpyxl 将非 ASCII 字符写为 `&#NNNNN;` 数字实体**，标签分类内联 raw=626、unescape 后仅 115；`_verify` 子元素组漏做 unescape（属性式组有）导致字节级误判。修复=子元素组补 unescape。教训：XML 层断言必须按**解码后字符数**度量；数值型 NCR 是 openpyxl 对非 ASCII 的标准输出，Excel/WPS 均正确解码，与兼容性无关。
2. **链序复发**：本地重生成时把 stats_report 排在 normalize 之后，openpyxl 往返把 showDropDown 全部写回（26 处）——TSK-012「normalize 最后写入者」规则本地执行同样必须遵守；已按 stats→normalize 重跑并解包终验 0 残留。
3. **管道吞退出码**：`cmd 2>&1 | tail -2` 的管道退出码=tail，`&&` 链在失败后继续执行——关键链改用 `set -o pipefail`。
4. **调试方法沉淀**：monkeypatch 包裹失败函数抓取现场 xml 落盘对比，是定位「报错与事后检查不一致」类问题的有效手段（本次 10 分钟内破案）。
