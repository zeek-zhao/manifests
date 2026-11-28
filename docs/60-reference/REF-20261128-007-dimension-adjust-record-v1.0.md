# REF-20261128-007 维度调整执行记录（TSK-010）

| 文档编号 | REF-20261128-007 |
| --- | --- |
| 版本 | v1.0 |
| 日期 | 2026-11-28 |
| 作者 | zeek.zhao（Agent 代笔） |
| 关联 | TSK-20261128-010 / REF-20261128-005 §4 / REF-20261128-006 / GUIDE v1.2 §2/§4.1 |

## 1. 方案确认与执行对照（用户第一步确认表 #1–#9 全部采纳）

| # | 确认内容 | 执行结果 |
| --- | --- | --- |
| 1 | 删 `sample` 组，2 个非示例成员改归 ai | ✅ groups+topic 双列清词；ai-knowledge→ai、jenkins-shared-library→devops（按标签判定） |
| 2 | 删 `project` 组，成员不补 | ✅ 双列清词（groups 13 行 / topic 9 行） |
| 3 | 删 `c++` 组（与 language c-cpp 重复） | ✅ 双列清词 7 行 |
| 4 | 删 `qemu`/`ops` 单例组 | ✅ 双列清词 |
| 5 | 11 个空组仓补组 | ✅ groups+topic 双列补：ros_21_tutorials、ROS-Academy-for-Beginners→robot；ai-book/ai-docker/ai-mcp/ai-server/ai-tools→ai；tabharbor→app；jenkins-Shared-Library1→devops；backup、wf4-selftest→tools |
| 6 | language 按 GitHub API 实测回填 16 行 | ✅ cmake×2（ROS-Academy、ros_21_tutorials）、groovy×1（jenkins-Shared-Library1）、python×3（manifests、ai-book、ai-docker）、shell×5（nas-server、PromWatch、jenkins、ai-workflow、ai-server）、nodejs×2（ai-tools、tabharbor）、powershell×1（ai-mcp）、mixed×2（backup、wf4-selftest，API 无主语言）；linux 误填清零 |
| 7 | rust/go 单例与 mixed 保留 | ✅ 未动 |
| 8 | 标签 14 类不合并 | ✅ 未动，下拉值域不变 |
| 9 | 双轨分工文档化 | ✅ GUIDE v1.2 §2 + 本文档 §2；REF-005 §4 注记 |

## 2. 机制澄清：topic 与 groups 是两列（执行中确认）

初版方案将「手填组」与「维度文件」视为同一来源；执行核验发现 repos 表实为**两列分工**：

- **`topic`（生成列，第 6 列）**：by-topic 维度清单文件的数据源（`generate_manifests.py` 行 401 `slugify(repo["topic"])`），并经 `build_groups` 派生进 manifest project 的 groups 属性；
- **`groups`（手填列，第 8 列）**：groups 属性的手填部分，不直接驱动维度文件。

因此确认表的所有「删组/补组」动作均**双列同步执行**（topic 列 45 行、groups 列 50 行调整），确保维度文件与 manifest groups 属性一致收敛。

## 3. 净效果

- by-topic 维度文件：19 → **14**（删 sample/project/cpp/qemu/ops；另清理历史遗留无引用的 common.xml/todo.xml，共 git rm 7 个 stale 文件）；
- by-language 维度文件：7 → **11**（新增 cmake/groovy/powershell/shell）；
- language 列：0 空值、0 `linux` 误填；groups 列 35 行留空为删除冗余组后的**设计行为**（仓库仍由标签/语言/平台维度覆盖）；
- 双轨重叠组：11/19 → 0（与标签 100% 同义的组全部移除，保留 robot/linux/vue/log/rk/qt/tools/blog/app/devops/esp/openharmony/raspberrypi/ai 中与语言或平台维度不重复者）。

## 4. 动态统计与图表（确认项第二步 #4）

- `tools/stats_report.py`：GitHub API 实时拉取 stars/forks/size/pushed_at（89/90 github 仓库有值，唯一缺指标 orgflow-devops1 上游已删除 404），写入「动态统计」sheet（131 行全列，非 github 平台留空）；
- 4 张 openpyxl 原生图表：标签分类分布条形图（14 类）、平台分布饼图、size Top15 条形图、public/private 饼图；辅助区 `COUNTIF` 公式随数据区自动更新；
- 已接入 excel-sync 工作流（sync→stats→generate→check→按差异提交）。

## 5. 数据可得性边界（沿用 REF-006 §5）

| 平台 | stars/forks/pushed_at | size |
| --- | --- | --- |
| github | ✅ API | ✅ API（TSK-009 已入库） |
| gitee | ❌ 无等价公开接口 | ❌ API v5 repo 端点无 size 字段 |
| gitlab / yoctoproject | ❌ | ❌ |
