# GUIDE-20261128-001 manifests 清单工程使用说明

| 文档编号 | GUIDE-20261128-001 |
| --- | --- |
| 版本 | v1.0 |
| 日期 | 2026-11-28 |
| 作者 | zeek.zhao（Agent 代笔） |
| 状态 | 已发布 |

本说明面向需要维护 `zeek-zhao/manifests` 清单或新增仓库的协作者，覆盖清单结构、字段含义、同步流程与统计表用法。

## 1. 工程定位与数据流

`manifests` 是多仓库 repo manifest 管理工程。**`catalogs/manifests.xlsx` 是唯一数据源**，其余一切产物均由工具生成：

```
manifests.xlsx ──generate_manifests.py──▶ manifests/*.xml（repo 清单）
       │            └─catalog_to_markdown.py──▶ docs/catalog.md（人类可读目录）
       └─validate_manifests_xlsx.py --export-json──▶ manifests-excel-snapshot.json（PR 审阅视图）
```

- `manifests-excel-snapshot.json`：生成器导出的机器可读快照（中文直出），仅为 PR 审阅提供 diff 视图，**不是数据源**，请勿手改。
- `docs/catalog.md`：生成产物，请勿手改（pre-commit 强制校验一致性）。

## 2. Excel 清单结构（5 个 Sheet）

| Sheet | 用途 | 维护方式 |
| --- | --- | --- |
| `repos` | 主表，每个仓库一行（131 行） | 人工/自动化混合 |
| `remotes` | 平台 URL 映射（fetch/push/代理），4 平台 | 人工，行内零 URL |
| `config` | 全局键值（default_protocol/self_owner/use_proxy_https/quickstart 两键） | 人工 |
| `readme` | 流程说明 + 字段字典 + 填写指引 | 人工 |
| `统计` | 自动统计（公式），同时维护标签分类清单 | 公式自动 + 分类清单人工 |

`repos` 主表 19 列：

- **结构列（自动维护，人工勿改）**：`name`（owner/repo.git，唯一键）、`path`（检出路径，自有行空则自动补 `project/<repo>`）、`branch`（自有行以 API default_branch 为准）、`platform`（gitee/github/gitlab/yoctoproject，外键→remotes 表）、`protocol`（自有行由 sync 清空，生成器按 default_protocol 补 https）、`description`（自有行来自 API）。
- **知识列（人工维护，自动化永不覆盖）**：`purpose` 仓库用途、`contents` 主要内容、`relations` 仓库间关系。
- **管理列（人工维护）**：`仓库属性`（公开/私有；自有行由 excel-sync 从 GitHub API 刷新）、`标签分类`（统一 15 分类体系，下拉引用「统计」sheet）、`suggested_action`、`note`。
- **扩展列**：`topic`、`language`、`groups`（逗号分隔；生成时自动追加 `platform`/`topic`/`visibility-{公开|私有}` 派生组，见 §5.2）、`linkfiles`（`src:dest` 分号分条）。

维度产物规则：生成列自动追加 platform/topic 到 groups；slug 规则见 REF-004。

## 3. excel-sync 同步流程

excel-sync 为**人工触发**的 GitHub Actions 工作流（`.github/workflows/excel-sync.yml`）：

1. 在 GitHub 仓库 Actions 页选择 `excel-sync` → `Run workflow`；
2. 工作流执行：`sync_self_repos.py`（按 §8 六策略抓取名下仓库，刷新 branch/platform/description/仓库属性，清空自有行 protocol，追加新仓库；无 `GH_PAT` Secret 时仅做确定性重建并警告跳过）→ `generate_manifests.py --excel` 重建清单 → `--check` 校验 → 有差异才自动提交 `chore(manifest): regenerate from excel [skip ci]`；
3. 拉取 main 获取结果。

配套 `excel-validate.yml`（人工触发）：基于指定 base 建临时分支 `excel/update-<时间戳>`，规范化 Excel（冻结首行/列宽/暗色主题/下拉）后单提交推送，人工合并。CI 永不删除分支。

本地等效命令：

```bash
python3 tools/generate_manifests.py --excel            # 重建清单
python3 tools/generate_manifests.py --excel --check    # 一致性校验
python3 tools/validate_manifests_xlsx.py               # 结构与规则校验
python3 tools/validate_manifests_xlsx.py --normalize   # 规范化（含暗色模板）
python3 tools/catalog_to_markdown.py                   # 重生成 docs/catalog.md
GH_TOKEN=<PAT> python3 tools/sync_self_repos.py --dry-run  # 同步预览
pre-commit run --all-files
```

## 4. 统计表用法

「统计」sheet 全部为公式（`COUNTA`/`COUNTIF` 引用整列），随 repos 表数据自动刷新，无需手动更新：

- B3 仓库总数 = `COUNTA(repos!$A:$A)-1`；
- B4/B5 公开/私有数、B6 私有占比；
- A9 起平台分布（各平台仓库数）；
- A14 起**标签分类清单**：A15:A29 为 15 个分类，B 列 `COUNTIF(repos!$O:$O, A行)` 计数。**该区域是「标签分类」下拉的单一维护点**——新增分类只需在 A 列插入一行并同步扩下拉引用区间（`validate --normalize` 会重建下拉）。

## 5. 代码拉取方式

清单 remote 以 HTTPS 为主；私有仓库（仓库属性=私有，生成组 `visibility-私有`）拉取前需先完成认证。

### 5.1 认证方式（四选一）

**gh CLI（GitHub 推荐）**

```bash
gh auth login                       # 或 export GH_TOKEN=<PAT>
gh auth setup-git                   # 将 gh 注册为 git 凭据助手（含私有仓）
gh repo clone zeek-zhao/ai-book     # 单仓直取
```

**SSH**

```bash
ssh-keygen -t ed25519 && cat ~/.ssh/id_ed25519.pub   # 公钥录入 GitHub/Gitee 账号
git clone git@github.com:zeek-zhao/ai-book.git
git clone git@gitee.com:owner/repo.git               # 多平台在 ~/.ssh/config 配别名
```

**HTTPS + PAT**

```bash
git clone https://github.com/zeek-zhao/ai-book.git
# 用户名填账号、密码填 PAT；凭据缓存用 git config credential.helper store/cache（仅仓库局部配置）
```

**本地代理（禁全局，按仓库局部或一次性）**

```bash
git -c http.proxy=socks5://127.0.0.1:1080 clone https://github.com/owner/repo.git  # 一次性
git config http.proxy http://127.0.0.1:7890        # 仓库目录内执行，仅该仓库生效
# repo 全清单场景：remotes 表已内置 proxy_https_url，config.use_proxy_https=TRUE 时
# 生成的 fetch 地址自动切代理，pushurl 恒为真实地址
```

### 5.2 拉取范围（三种）

**单仓库**：`repo sync` 后跟清单中的 path 或 name。

```bash
repo init -u git@github.com:zeek-zhao/manifests.git -b main -m manifests/default.xml
repo sync esp/esp32_100ask_project
```

**指定组**：按组批量拉取统一走**维度清单**（跨 repo 版本最可靠）；每个 project 的 `groups` 属性内嵌 `platform/topic/visibility-{公开|私有}`，便于自研脚本按组过滤。

```bash
repo init -u git@github.com:zeek-zhao/manifests.git -b main \
  -m manifests/generated/by-topic/robot.xml        # 例：robot 组
repo sync -j30
# 私有仓：用 by-owner/zeek-zhao.xml（认证后）或按 visibility-私有 组过滤 name 逐仓 clone
```

**全部仓库**：

```bash
repo init -u git@github.com:zeek-zhao/manifests.git -b main -m manifests/default.xml
repo sync -j30 -c    # default.xml 聚合全部维度；-c 仅拉当前分支
```

## 6. 新增仓库操作指引

1. **自有仓库**：无需手改 Excel——推送/创建到名下后触发 excel-sync 即自动追加；随后人工补知识列（purpose/contents/relations）与标签分类。
2. **外部仓库**：在 repos 表末尾追加行，至少填 `name`（owner/repo.git）、`path`、`branch`、`platform`、`topic`、`language`；建议补知识列与标签分类；URL 一律加到 remotes 表，不得写入行内。
3. 本地校验：`pre-commit run --all-files` 全绿后再提交。

## 7. 文档目录结构（ISO 命名 `<类型>-<YYYYMMDD>-<序号>-<slug>-v<major>.<minor>`）

| 目录 | 类型 | 内容 |
| --- | --- | --- |
| `docs/00-guide/` | GUIDE | 使用说明、快速上手 |
| `docs/10-task/` | TSK | 任务书（每任务一份） |
| `docs/20-design/` | DSN | 设计文档（含决策点，评审后才实施） |
| `docs/30-plan/` | PLN | 落地计划 |
| `docs/40-log/` | LOG | AI 操作日志（逐步记录） |
| `docs/50-report/` | RPT | 汇报文档 |
| `docs/60-reference/` | REF | 架构/钩子/关键字等参考 |
| `docs/catalog.md` | — | 生成产物（工具路径硬编码，留根） |

## 8. FAQ

- **快照与 Excel 不一致怎么办？** 快照由生成器导出，不一致说明有人手改了快照；恢复方式 `python3 tools/generate_manifests.py --excel --export-json`。
- **私有仓公开/私有如何判定？** 自有行由 excel-sync 从 GitHub API（`/user/repos`，需 `GH_PAT` Secret）读取 visibility 映射为 公开/私有；外部行默认公开。
- **为何协议列是空的？** 设计如此（K6）：自有行 protocol 由 sync 清空，生成器统一按 `config.default_protocol`（https）生成，避免散落协议配置。
- **分支规范？** 多分支开发；Issue/PR 必须标注所属分支；提交身份仅 zeek.zhao。
