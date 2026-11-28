# REF-20261128-008 仓库大小数据可得性矩阵与浅/深拷贝建议

| 文档编号 | REF-20261128-008 |
| --- | --- |
| 版本 | v1.0 |
| 日期 | 2026-11-28 |
| 作者 | zeek.zhao（Agent 代笔） |
| 关联 | TSK-20261128-015 |
| 状态 | 有效 |

## 1. 背景与结论

用户诉求：`仓库大小(MB)` 列覆盖**全部**仓库，用于拉取代码时判断浅拷贝（`--depth=1`）还是深拷贝（完整历史）。经逐平台实测，可得性如下：

| 平台 | 行数 | 可得性 | 数据状态 |
| --- | --- | --- | --- |
| github | 90 | ✅ `GET /repos/{owner}/{repo}` 的 `size` 字段（KB→MB） | 89/90 有值；`orgflow-devops1` 上游已删除 404，常态留空（excel-sync 会自动删行） |
| gitee | 28 | ❌ OpenAPI v5 `GET /repos/{owner}/{repo}` **无 size 字段**（实测 20 次成功调用均返回 None） | 留空 |
| gitlab | 8 | ❌ 公开 API `GET /projects/:id` 不返回 `statistics`（需该项目 Maintainer 以上权限认证） | 留空 |
| yoctoproject | 4 | ❌ cgit 界面无 HTTP API | 留空 |

## 2. 浅/深拷贝决策建议

1. **github 行（90 行，含全部自有仓）**：直接按 `仓库大小(MB)` 数值判断。经验阈值：≤50MB 浅拷贝足够日常使用；>200MB（如 poky/autoware 级别）建议浅拷贝，需要完整历史时再 `git fetch --unshallow`。
2. **gitee 28 行**：平台不提供 size。该清单中 gitee 行均为教程/驱动/示例类小仓（esp32_100ask、embedfire、正点原子等），**默认浅拷贝安全**。
3. **gitlab 8 行 / yoctoproject 4 行**：无公开数据。gitlab 行为社区镜像仓（小）；yoctoproject 4 行（poky/meta-*）**均为大型仓**，建议浅拷贝+按需浅层子模块。
4. 协议已全站统一 HTTPS（TSK-015 删除协议列），`repo init` 的 remote 一律 `{platform}_https`，无需再区分 git/ssh 端点。

## 3. 维护

- github 行 size 由 excel-sync / excel-autofill / stats_report 按 API 刷新；
- 若 gitee/gitlab 未来开放 size 字段，可在 `sync_self_repos.py`/`autofill_repos.py` 增加对应平台分支；
- 「合计」行（repos 表末尾，`SUM` 公式）提供全表体量总览。
