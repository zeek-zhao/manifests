# 落地计划 PLN-20261128-003：AI 填充执行步骤（TSK-20261128-003）

| 文档属性 | 内容 |
|---|---|
| 编号 | PLN-20261128-003 |
| 版本 | v1.0 |
| 日期 | 2026-11-28 |
| 编制 | AI Agent (zeek.zhao) |
| 状态 | 执行中 |

## 步骤

1. 导出全量 120 行清单至 /tmp（供 AI 通读）；
2. 临时脚本 `/tmp/fill_ai_columns.py`：内置 AI 生成内容字典（键=name+path），openpyxl 原位填充 description(外部)/purpose/contents/relations；
3. 读回校验：空值统计、列宽自适应、抽样打印；
4. 提交推送（docs TSK/PLN-003 + manifests.xlsx 同批）；
5. 删除 /tmp 临时文件。

## 风险

| 风险 | 对策 |
|---|---|
| AI 对小众仓库（如 ZZX_RUN、base-sample）不了解 | 用「据名称与分组推断/待核」措辞，不编造 |
| 脚本过大远端写入超时 | 分段 write+append（b3 教训） |
| 误改结构列 | 脚本仅写 4 个目标列，键不存在时跳过并计数 |
