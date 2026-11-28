# TSK-20261128-006 后续收尾任务书

| 项 | 内容 |
| --- | --- |
| 日期 | 2026-11-28 |
| 提出人 | zeek.zhao |
| 执行者 | zeek.zhao（Agent 代执行） |
| 前置 | TSK-004/005 完成，PR #1/#4 已合并，GH_PAT Secret 已配置（用户 m00761「同意 继续」授权） |
| 分支 | 文档与运维操作直接落 main（先例：LOG-004/005）；衍生数据变更走 PR |

## 1. 任务范围

1. **T1 旧分支清理**：删除已完成使命的远端+本地分支 `feat/catalog-add-15-repos`（PR #1 已合并）、`feat/excel-retire-json`（PR #4 已合并）。提交已全部在 main 历史中，删除不丢数据。
2. **T2 excel-sync 实跑**：人工触发 `excel-sync.yml`（workflow_dispatch），首次验证 GH_PAT 凭证 + §8 六策略 + 确定性重建闭环。预期变更即 TSK-004 dry-run 所列 60 项动作：51 行 protocol 清空（K6）、obsidian branch→main、3 行 description=API 值、orgflow-devops1 上游消失 note、**11 个新仓库追加**（ROS-Academy-for-Beginners/ai-book/ai-docker/ai-mcp/ai-server/ai-tools/backup/jenkins-Shared-Library1/ros_21_tutorials/tabharbor/wf4-selftest）。产出直接提交 main（`chore(manifest): regenerate from excel [skip ci]`）。
3. **T3 新行知识列补全**（T2 衍生）：sync 追加的 11 行 purpose/contents/relations 为空，按 TSK-003 填充规则（基于 API description + 名称推断，私有仓库标注「据名称与分组推断/待核」）在分支 `feat/excel-fill-11` 上填充并重生成，走 PR 合并。

## 2. 风险与说明

- **manifest 大幅重排**：K6 清空自有行 protocol 后，50 个自有仓库由 git 桶迁入 https 桶——这是 DSN-001 §8 明确设计行为（protocol 列交由自动化维护），非回归。
- **T2 直接落 main**：DSN §11 设计即如此（sync 工作流直接提交 main、带 [skip ci]），变更可在 main diff 审阅。
- **回滚方案**：main 历史可 revert 对应提交；分支删除可在 GitHub 界面 restore。

## 3. 验收标准

1. 两个旧分支远端+本地均不存在，PR #1/#4 记录完好。
2. sync 实跑绿且产生 regenerate 提交；11 新行存在于 Excel；`--excel --check` 一致。
3. 11 行知识列无空值；pre-commit 全绿；PR 合并后 main CI 绿。
