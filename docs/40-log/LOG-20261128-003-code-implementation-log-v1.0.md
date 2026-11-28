# LOG-20261128-003 — TSK-20261128-004 代码实施操作日志

| 文档属性 | 内容 |
|---|---|
| 编号 | LOG-20261128-003 |
| 版本 | v1.0 |
| 日期 | 2026-11-28 |
| 编制 | AI Agent (zeek.zhao) |
| 审核 | 待用户验收 |
| 状态 | 已完成（提交 eb9f935 + dd24b79 已推送，CI push/pull_request 双绿） |
| 关联 | TSK-20261128-004 / PLN-20261128-004 / DSN-20261128-001 v0.5 |

## 执行过程

1. 读取 DSN §7/§8/§9/§11/§13 与旧版 `tools/generate_manifests.py`（289 行）。
2. 重写 `tools/generate_manifests.py`（539 行）：新增 `--excel`/`--xlsx`/`--export-json`、Excel 全量规则校验、remotes 代理规则（`use_proxy_https`）、quickstart 改由 config 表驱动（回退硬编码兜底）；旧生成函数体经 `git show HEAD` 取回原样保留。
3. 字节一致验收：JSON 数据源与 `--excel` 两种模式输出 `diff -r` 完全一致（IDENTICAL），`--check` 双模式通过。
4. 快照导出对齐现有 `pretty-format-json` 格式（`\uXXXX` 转义 + 2 空格缩进 + 末尾换行）。
5. 行序重排：Excel 行序对齐 JSON 文件字母序，消除混合维度桶（by-platform/by-language/by-topic）内 project 顺序 diff（涉及 10 个生成文件）。
6. openpyxl 坑定位与修复：`ws.cell(row, col, value=None)` 在 `value=None` 时不赋值导致清空失效、跨行串值；统一改用 `.value` 直赋并在 LOG 中记录。
7. 新增 `tools/validate_manifests_xlsx.py`：validate / --normalize（冻结首行、表头加粗、列宽、下拉重建）/ 快照导出；normalize 后再校验及 `--excel --check` 均通过。
8. 新增 `tools/sync_self_repos.py`（§8 全策略 + `--dry-run`）；修正 API 选择：改用认证接口 `/user/repos?type=owner` 并按 `owner.login` 过滤（`/users/{owner}/repos` 仅返回公开仓库，会误标 30+ 私有仓为上游已消失）；首行判定兼容 obsidian 双行。dry-run 实测 60 项动作（51 行 protocol 清空、obsidian branch→main、3 行 description 刷新、orgflow-devops1 上游已消失、alpu gitee 跳过、11 个新仓库待追加），按 PLN 仅 dry-run 未实跑。
9. `tools/catalog_to_markdown.py` 数据源改为 Excel；`docs/catalog.md` 重生成（184 行，50 自有仓库分类表）。
10. 新增 `.github/workflows/excel-validate.yml`（dispatch + base_branch 入参 → 建 `excel/update-<YYYYMMDD-HHmm>` 分支（ls-remote 判重）→ 校验规范化 → 单提交推送，不合并不删）与 `excel-sync.yml`（dispatch → sync → `--excel` 重建 → `--check` → 有变更才提交 `chore(manifest): regenerate from excel [skip ci]`）。
11. `.pre-commit-config.yaml` 新增 3 个本地钩子：generate-manifests-excel-check / validate-manifests-xlsx / catalog-markdown-check。
12. `tools/enrich_catalog.py` 退役删除（D6）；确认无代码引用，仅历史文档保留提及。
13. README / docs/design / docs/implementation / docs/quickstart 四件套改写为 Excel 单一事实来源叙述。
14. 行序回退事故与恢复：sync dry-run 验证前的 `git checkout -- catalogs/manifests.xlsx` 将尚未提交的「重排+normalize」版本回退到 26fe4bb（行序回退、格式回退，知识列无损）；重写临时脚本重排（首版误把 `manifests-excel-snapshot.json` 计入 JSON 源导致 240 条重复断言失败，排除快照后按文件字母序匹配 120 行）并重新 normalize，字节一致恢复后随 eb9f935 提交。教训：跨命令依赖的工作树改动应及时提交，验证间隙禁止 checkout 回退。
15. CI 首跑失败（run 46053898835/46053906708）：runner 未安装 openpyxl，generate-manifests-excel-check / validate-manifests-xlsx / catalog-markdown-check 三个新钩子全部报缺依赖；ci.yml 安装步骤追加 openpyxl（dd24b79）后 push/pull_request 双绿（run 46054054691/46054061509）。
16. 最终验收：`--excel` 与 JSON 数据源输出逐字节一致；`--check` 双模式、`validate_manifests_xlsx.py`、`catalog_to_markdown.py --check` 通过；pre-commit 10 钩子全过；CI 双绿。

## 风险与残留

- `sync_self_repos.py` 实跑未执行（属 excel-sync 工作流职责）。dry-run 显示 K6 清空自有行 protocol 后，自仓将落入 https 协议桶，manifests 会随之重建提交——设计行为，非回归。
- `excel-sync.yml` 依赖仓库 Secret `GH_PAT`（`/user/repos` 需用户 PAT；`GITHUB_TOKEN` 无法列出用户私有仓）；未配置时该步以 warning 跳过，仅执行确定性重建。
- yoctoproject 4 行为裸 `repo.git`（无 owner 前缀），Excel 校验的 name 规则已放宽为允许裸名。
- 过渡期 `catalogs/*.json` 与 `catalogs/manifests-excel-snapshot.json` 仅只读；后续退役需另立任务书。

## 上下文压缩记录

- RTK 等效方案执行：远端输出精简（grep/日志裁剪）+ 对话侧 compress 分块压缩；无远端 rtk 安装（环境限制，见 LOG-20261128-001）。
