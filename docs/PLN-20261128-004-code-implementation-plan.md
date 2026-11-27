# 落地计划 PLN-20261128-004：代码实施步骤（TSK-20261128-004）

| 文档属性 | 内容 |
|---|---|
| 编号 | PLN-20261128-004 |
| 版本 | v1.0 |
| 日期 | 2026-11-28 |
| 编制 | AI Agent (zeek.zhao) |
| 状态 | 执行中 |

## 步骤

| # | 步骤 | 验证 |
|---|---|---|
| 1 | 生成器改造（Excel 加载器+§9 校验+代理规则+config quickstart+CLI） | `--excel` 与 JSON 源输出 `diff -r` 逐字节一致 |
| 2 | `tools/validate_manifests_xlsx.py`（校验+规范化+快照） | 对现状 xlsx 校验通过；快照生成且 JSON 源不受影响 |
| 3 | `tools/sync_self_repos.py`（§8 策略，urllib 直连 API，无新依赖） | `--dry-run` 输出 50 自有行动作清单 |
| 4 | 双 workflow YAML + pre-commit 钩子 | YAML 解析通过 |
| 5 | catalog_to_markdown 适配 + enrich_catalog.py 删除 | markdown 重生成与现内容一致（数据未变） |
| 6 | 文档改写（README/design/implementation/quickstart/AGENTS/LOG-003） | 提交推送 |
| 7 | 全量验证 + 分批提交 + 推送 + CI 观测 | pre-commit 绿、CI 绿 |

## 关键实现决策

| # | 决策 | 说明 |
|---|---|---|
| K1 | Excel 加载器输出复用现有 repo dict 形状（preferred_protocol/groups[]/linkfiles[{src,dest}]） | 渲染层零改动，保证字节一致 |
| K2 | owners 由 config.self_owner + 自有行存在性合成 `{self_owner:{}}` | 复现 by-owner/zeek-zhao.xml（JSON 现行为），不带协议偏好 |
| K3 | 快照默认 `catalogs/manifests-excel-snapshot.json`，JSON 加载器排除 `*-excel-snapshot.json` | §13 catalog_to_markdown 读快照的桥；不污染 glob |
| K4 | 代理规则仅在 use_proxy_https=TRUE 且 proxy 列非空时改写 https fetch，此时补 pushurl=真实 https_url；FALSE 时与 JSON 现状完全一致 | 现状 FALSE → 字节一致 |
| K5 | sync 平台非 github 的自有行跳过（如 gitee 的 alpu），记录于输出 | GitHub API 覆盖范围 |
| K6 | sync 按 §8 清空自有行 protocol（首跑会改变现状 git→空，设计行为） | LOG 记录 |

## 风险与回滚

| 风险 | 对策 |
|---|---|
| Excel 源与 JSON 源产出漂移 | 验收 1 字节级 diff；漂移即阻断提交 |
| workflow 在真实仓库上误触发 | 仅 workflow_dispatch 人工触发，且 excel-sync 只在合并后人工触发（§11.3） |
| enrich 删除导致 catalog.md 断链 | catalog_to_markdown 改为读 Excel，验证 5 覆盖 |
