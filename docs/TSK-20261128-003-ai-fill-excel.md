# 任务书 TSK-20261128-003：AI 填充 Excel 知识列

| 文档属性 | 内容 |
|---|---|
| 编号 | TSK-20261128-003 |
| 版本 | v1.0 |
| 日期 | 2026-11-28 |
| 编制 | AI Agent (zeek.zhao) |
| 审核 | 用户已指示执行（「尽量把这个表给我填完 结合ai，然后继续」） |
| 状态 | 执行中 |

## 1. 任务目标

结合 AI 能力将 `catalogs/manifests.xlsx` 中空置的知识列补全：

1. **外部行（70 条）**：补 description（AI 依据公开项目常识+仓库元数据）、purpose、contents、relations；
2. **自有行（50 条）**：补 purpose、contents、relations（description 保留 API 原值，仅当描述为纯名称占位时改写）；

## 2. 填充规则

| 规则 | 说明 |
|---|---|
| 依据 | 已知元数据（name/path/topic/language/groups/category/description/visibility）+ AI 对公开开源项目的通识 |
| 置信 | 对无法确证内容的小众仓库，用语标注「据名称与分组推断」「待核」，不编造细节 |
| 边界 | 不改 branch/platform/topic/language/groups 等结构列；不覆盖自有行已有 description；note 列不动（用户自由列） |
| 语言 | 中文，与现状一致 |

## 3. 验收

1. purpose/contents 两列 120 行零空值（「待核」类条目除外，但必须有推断性文字）；
2. 外部行 description 零空值；
3. relations 尽量建立同组/上下游关系（如 turtlebot3 三件套、博客三环链路、log 组 C/C++ 双线）；
4. 读回校验通过后提交推送，临时脚本用完即删。
