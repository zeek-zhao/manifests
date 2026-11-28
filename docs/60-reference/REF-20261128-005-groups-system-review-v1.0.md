# REF-20261128-005 groups 体系说明与复审报告

| 文档编号 | REF-20261128-005 |
| --- | --- |
| 版本 | v1.0 |
| 日期 | 2026-11-28 |
| 编制 | zeek.zhao（Agent 代笔） |
| 状态 | 已发布（数据截至 131 行清单，TSK-20261128-008） |

## 1. groups 生成规则

**双轨制**：Excel `groups` 列（手填，slug 风格）是同步维度的种子；`标签分类` 列（中文，15 分类）是知识管理分类，二者职责不同、不互相写入。

生成 manifest 时，每个 project 的 `groups` 属性 = 手填组 ∪ 派生组（去重保序）：

1. **手填组**：Excel groups 列原样（如 `robot,linux`）；
2. **平台组**：`gitee/github/gitlab/yoctoproject`（= platform 列）；
3. **主题组**：topic 列值（slug 用于维度目录名，组内保留原值）；
4. **可见性组**（TSK-008 v1.2 起）：`visibility-公开` / `visibility-私有`，生成时从 仓库属性 列派生，**不入手填列**（避免双写失同步）；空值跳过。

维度文件（by-protocol/platform/language/topic/owner，35 个）按各列 slug 拆分，default.xml 为 include 索引。

## 2. 复审结果（131 行实算）

### 2.1 分类覆盖率 ✅
- 手填 groups 空行 11（均为 excel-sync 自动追加的新自有仓，属预期，待人工补组）；
- 派生组覆盖率 **100%**：每行至少含 平台+主题+visibility 三组；平台分布 gitee 28 / github 91 / gitlab 8 / yoctoproject 4；
- visibility 组：公开 88 / 私有 43，行级全覆盖（唯一名级 130=88+42，obsidian 同名双行双 path）。

### 2.2 命名一致性 ✅（小瑕疵）
- 手填 19 组全部符合 slug 规范 `[a-z0-9+_-]+`（含 `c++`），无大小写/空格/中文混入；
- 单例组 2 个：`ops`、`qemu`（碎片化，建议归并至 tools 或对应领域组）；
- 派生组命名空间清晰（平台裸名 + `visibility-` 前缀），与手填组无冲突；派生后 distinct 组 26（19 手填 + 4 平台 + 1 visibility×2 + 主题并入）。

### 2.3 归属合理性 ⚠️（双轨语义重叠）
- `robot` 组 18 vs 标签分类「ROS与机器人」22：差 4 行未打 robot 组（组是同步维度、标签是知识分类，边界语义重叠）；
- `vue` 组 9 vs 「Web与前端」8：多 1 行（某 vue 项目按用途归入独立产品与应用）；
- `sample`(16)/`project`(13) 泛化组占比高，检索区分度低，建议后续收敛（列入待办，不阻塞）；
- 其余组（linux/rk/log/qt/tools/c++ 等）与平台、主题归属抽查无错挂。

## 3. 结论与建议

1. 双轨制维持不变；新增仓库时组名尽量与标签分类语义对齐（如 ROS 类仓库补 `robot` 组）；
2. `ops`/`qemu` 单例组与 sample/project 泛化组的归并收敛列为后续任务；
3. visibility 组已全量落 XML 与 catalog.md，可直接作为自研脚本按 公开/私有 过滤的稳定锚点。
