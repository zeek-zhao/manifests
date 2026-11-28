# TSK-20261128-016 gitee 镜像仓识别与替换任务书

| 文档编号 | TSK-20261128-016 |
| --- | --- |
| 版本 | v1.0 |
| 日期 | 2026-11-28 |
| 作者 | zeek.zhao（Agent 代笔） |
| 关联 | TSK-20261128-015 / REF-20261128-008 |
| 状态 | 已完成（阶段一报告 REF-009 + 阶段二替换已执行，LOG-016） |

## 1. 需求（两阶段，用户 m01926）

- **阶段一（本次）**：检查 manifests.xlsx 全部 gitee 平台仓库行，识别「原版实际托管在 GitHub」的镜像仓，为其找到 GitHub 原版地址；**生成报告先行**（镜像行清单/原版地址与判定依据/替换方案），不动数据。
- **阶段二（确认后）**：替换表格链接与 remote（协议 HTTPS），按现有流程验证、重新生成、PR、--no-ff 合并、更新 catalog.md 与日志。

## 2. 判定方法（证据链，避免纯名称杜撰）

1. **行内对照**：gitee 行与 github 行同名（repo 部分）→ 已在表中的 GitHub 行即原版候选（强）。
2. **Git 提交比对（铁证）**：gitee 仓默认分支 HEAD commit sha 与 GitHub 候选默认分支 HEAD sha 一致 → 确证为同一项目（gitee 导入镜像保留 sha）。sha 不一致但 commit message 一致 → 强（镜像滞后）。
3. **辅助**：gitee/GitHub API description、项目常识（spdlog/EasyLogger 等知名项目）。

## 3. 阶段二替换方案（待确认）

- gitee 行的 `platform` 改 `github`，`name` 改 GitHub owner/repo.git；`path` 不变（检出路径不变，本地目录零迁移）；`branch`/`仓库属性`/`仓库大小(MB)`/`language`/`description` 按 GitHub API 刷新；
- 与既有 github 行重复的镜像行**删除**（同项目双行去重，default.xml 单一来源）；独立镜像行改 platform 保留行；
- 生成物（by-platform/by-topic XML、remotes）随 `--excel` 全量重建；快照/catalog.md 同步；LOG-016 记录全部替换与依据。

## 4. 验收标准（阶段二）

- 替换后无失效 remote 引用；`--excel --check`/validate/9 钩子/CI 绿；报告与实际替换一一对应。
