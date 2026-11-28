# REF-20261128-006 清单维度体系评估报告

| 文档编号 | REF-20261128-006 |
| --- | --- |
| 版本 | v1.0 |
| 日期 | 2026-11-28 |
| 作者 | zeek.zhao（Agent 代笔） |
| 状态 | 已发布（TSK-20261128-009 第 6 项交付） |

## 1. 背景

TSK-009 要求审视当前所有分组/标签维度是否都有实际意义，说明理由后再执行修改。评估范围：manifests/generated/ 维度目录、统计表「标签分类」体系、groups 手填组三套机制。数据基线：131 行（自有 61 + 外部 70）。

## 2. 维度评估结论（TSK-009 执行后）

| 维度 | 文件数 | 结论 | 理由 |
|---|---|---|---|
| by-protocol | 2 | **删除（已执行）** | ①协议是 remote 配置属性而非「选哪些仓」的选题维度，repo init 场景不存在按协议取子集的需求；②https.xml 含全部 131 仓与 default.xml 完全重复，git.xml 仅 6 仓（且均为外部仓）价值趋零；③remote 命名 `{platform}_{protocol}` 已内嵌协议信息，按协议过滤可用 `-g` 组合实现 |
| by-platform | 4 | 保留 | 按托管平台隔离拉取是真实场景（镜像/内网可达性差异）；4 文件均 ≥4 仓 |
| by-language | 7 | 保留 | 按语言拉取是高频需求；`mixed`（多语言综合资料）与 `linux`（内核相关）语义可辨识；单例 go/rust/nodejs 是语言维度的自然边界 |
| by-topic | 17 | 保留 | 专项拉取（如 qemu/openharmony 单仓专项）是有效用例；单例也是合法筛选单元 |
| by-owner | 1 | 保留 | 私有仓统一拉取入口（zeek-zhao 名下含 private，认证后可用） |

执行动作：删除 `manifests/generated/by-protocol/`（git rm），生成器移除该维度产出分支（`generate_manifests.py` 保留注释说明），default.xml include 索引与 README/GUIDE/REF-003 中的协议维度示例同步移除。

## 3. 标签分类体系（15 → 14）

- 移除「待整理」：单成员（zeek-zhao/alpu.git），该类本质是临时缓冲而非语义分类；alpu 标签清空，待维护者通过下拉直接归类（下拉已可用）。
- 其余 14 类成员数均 ≥3，无泛化兜底类（明确不加「其他」——兜底类会重新积累未分类条目）。
- 清单单一维护点：统计 sheet 标签区（`TagCategories` 命名区域引用 `统计!$A$15:$A$28`）；下拉同时写入内联枚举串（任何 Excel/WPS 版本点击即选，`--normalize` 时从清单重新生成）。

## 4. groups 手填组与标签分类的双轨关系（维持现状）

REF-005 已指出双轨语义重叠（robot 组 18 vs ROS标签 22、vue 9 vs Web标签 8）。结论：**维持双轨**——groups 服务 `repo sync -g` 精确拉取过滤，标签分类服务清单治理与统计；二者受众不同，强行合并会牺牲其中一侧的可用性。持续观察，若维护成本上升再评估归并。

## 5. 仓库大小数据可得性矩阵（TSK-009 第 1 项）

| 平台 | 接口 | 结果 | 覆盖 |
|---|---|---|---|
| github | `GET /repos/{owner}/{repo}` → `size`（KB，GH_PAT 认证） | 成功 | 90/91（`zeek-zhao/orgflow-devops1` 上游已删除返回 404，留空） |
| gitee | `GET /api/v5/repos/{owner}/{repo}`（免认证） | **无 size 字段** | 0/28（20 次成功调用响应中均无该字段，SSL 超时 6 次、404 2 次亦无补齐途径） |
| gitlab | gitlab.com 公开项目接口 | 无 statistics | 0/8（`statistics` 仅项目维护者可见，公开匿名不可得） |
| yoctoproject | 无公开 API | 不可得 | 0/4 |

汇总：90/131 行有值，合计 2,111,449 KB（约 2.01 GB）；自有行后续由 excel-sync 每次刷新（sync 已实现 size 列写入）；其余平台行留空为数据可得性上限，非遗漏。

## 6. 遗留与建议

1. alpu 标签待人工归类（打开 Excel 点击 O 列单元格即可选择）。
2. `zeek-zhao/orgflow-devops1` 上游已删除，建议后续评估从清单移除或标记废弃（note 已有上游消失标注）。
3. gitee 仓库如需 size，可考虑后续接入 Gitee 认证接口复查字段支持情况（当前免费接口无该字段）。
