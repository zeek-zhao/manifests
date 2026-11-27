# 设计文档 DSN-20261128-001：基于 Excel 动态生成 manifest

| 文档属性 | 内容 |
|---|---|
| 编号 | DSN-20261128-001 |
| 版本 | v0.1（待审核） |
| 日期 | 2026-11-28 |
| 编制 | AI Agent (zeek.zhao) |
| 审核 | 待用户审核 Excel 设计 |
| 状态 | 待审核（审核通过后进入第二阶段实施） |

## 1. 背景与目标

现有链路以 `catalogs/*.json` 为单一事实来源，`tools/generate_manifests.py` 将其渲染为多维度 repo XML 清单。本次重构将**单一事实来源改为 Excel 工作簿**，目标是：

1. 仓库清单用 Excel 维护（表格化编辑、下拉校验、筛选排序）；
2. **自有仓库（zeek-zhao 名下）不逐行手工维护**：由自动化获取全部仓库及分支，写入独立 sheet 并自动打自有标签；
3. **主表仅逐行维护外部仓库**；
4. 保留现有多维度生成能力（by-protocol/platform/language/topic/owner）与 repo XML 属性兼容性。

## 2. 工作簿总体设计

建议文件路径：`catalogs/manifests.xlsx`（替代 `catalogs/*.json` 成为主数据源；原 JSON 保留为可选导出快照，见 §8 决策点）。

| Sheet 名 | 职责 | 维护方式 |
|---|---|---|
| `repos_external` | 主表：外部仓库清单，一行一个检出条目 | 人工维护 |
| `repos_self` | 自有仓库自动清单（仓库+分支+标签） | 第二阶段自动化生成，人工不改 |
| `overrides_self` | 自有仓库覆盖/禁用配置（改路径、改分支、禁用纳管） | 人工维护 |
| `remotes` | 平台 → 协议 URL 映射（生成 `<remote>`） | 人工维护（低频） |
| `owners` | owner 级配置（协议偏好、分组、自有标记） | 人工维护（低频） |
| `enums` | 枚举字典（下拉校验数据源 + 值说明） | 人工维护（低频） |
| `config` | 全局生成配置键值对 | 人工维护（低频） |

## 3. 主表 `repos_external` 列定义（外部仓库，逐行维护）

| # | 列名 | 含义 | 格式/约束 | 必填 | 填写示例 |
|---|---|---|---|---|---|
| 1 | `name` | 仓库全名 `owner/repo.git` | 文本；`/` 分隔且以 `.git` 结尾；**唯一键为 name+path 组合**（同仓库多分支检出时允许重复 name） | 必填 | `bazelbuild/examples.git` |
| 2 | `path` | `repo sync` 本地检出目录 | 文本；全局唯一；不含 `..`、不以 `/` 开头 | 必填 | `c++/bazel_examples` |
| 3 | `branch` | 跟踪分支 | 文本；不得为空 | 必填 | `master` |
| 4 | `platform` | 托管平台 | 枚举，必须存在于 `remotes` 表 | 必填 | `github` |
| 5 | `topic` | 主题维度 | 文本（生成时 slug 化）；用于 by-topic 拆分 | 必填 | `cpp` |
| 6 | `language` | 语言维度 | 文本（slug 化）；仅影响 by-language 拆分，不进 project 属性 | 必填 | `c/c++` |
| 7 | `groups` | 自定义分组 | 逗号分隔多值；生成时自动追加 `platform,topic` | 选填（留空=仅平台/主题组） | `project,embedded` |
| 8 | `protocol` | 协议偏好 | 枚举：`https` / `git`（SSH）/ 留空（继承 owner 或默认） | 选填 | `git` |
| 9 | `visibility` | 可见性（管理列） | 枚举：`public`/`private`/`internal` | 选填 | `public` |
| 10 | `category` | 管理分类（管理列） | 枚举（沿用现有中文分类） | 选填 | `元工具与工程流程` |
| 11 | `description` | 描述（管理列） | 文本 | 选填 | `Bazel 官方示例仓库` |
| 12 | `suggested_action` | 处置建议（管理列） | 枚举：`保留`/`观察`/`淘汰`/`待评估` | 选填 | `保留` |
| 13 | `linkfiles` | linkfile 映射 | 一行多条用 `;` 分隔，每条 `src:dest`；留空不生成节点 | 选填 | `.:sample/cpp-sample/docker` |
| 14 | `note` | 备注（自由文本，不参与生成） | 文本 | 选填 | `上游更新频繁，季度复查` |

说明：`owner` 不单独设列，由 `name` 按 `owner/repo.git` 派生（与现生成器 `get_owner()` 一致），用于关联 `owners` 表与 by-owner 维度。

## 4. 自动表 `repos_self` 列定义（自有仓库，第二阶段自动化写入，人工不改）

| # | 列名 | 含义 | 来源（自动化） | 示例 |
|---|---|---|---|---|
| 1 | `name` | 仓库全名 | GitHub API `owner/repo.git` | `zeek-zhao/manifests.git` |
| 2 | `default_branch` | 默认分支 | API `default_branch` | `main` |
| 3 | `branches` | 全部分支 | API branches 列表，逗号分隔 | `main,obsidian,markdown` |
| 4 | `visibility` | 可见性 | API `private/public` | `private` |
| 5 | `description` | 描述 | API `description` | `SWD NAS 服务平面文档中心` |
| 6 | `ssh_url` | SSH 克隆地址 | API `ssh_url` | `git@github.com:zeek-zhao/manifests.git` |
| 7 | `https_url` | HTTPS 克隆地址 | API `clone_url` | `https://github.com/zeek-zhao/manifests.git` |
| 8 | `pushed_at` | 最后推送时间 | API `pushed_at` | `2026-11-28T00:40:00Z` |
| 9 | `archived` | 归档标记 | API `archived` | `FALSE` |
| 10 | `is_fork` | fork 标记 | API `fork` | `FALSE` |
| 11 | `self_tag` | 自有标签 | 由 `owners` 表 `auto_sync=TRUE` 的 owner 派生，默认该 owner 名 | `zeek-zhao` |

**自有仓库纳入 manifest 的规则**（默认值，均可被 `overrides_self` 覆盖）：默认 `path=project/<repo名>`、`branch=default_branch`、`protocol` 继承 owner 配置、groups 自动追加 `self_tag` 标签组（如 `zeek-zhao`），并保留现有 by-owner 维度输出。

## 5. 覆盖表 `overrides_self` 列定义

| # | 列名 | 含义 | 格式 | 必填 | 示例 |
|---|---|---|---|---|---|
| 1 | `name` | 目标自有仓库 | 与 `repos_self.name` 一致 | 必填 | `zeek-zhao/obsidian.git` |
| 2 | `path` | 覆盖检出路径 | 文本；留空=默认值 | 选填 | `project/obsidian-md` |
| 3 | `branch` | 覆盖分支 | 文本；留空=默认分支 | 选填 | `markdown` |
| 4 | `groups` | 追加分组 | 逗号分隔 | 选填 | `notes` |
| 5 | `protocol` | 协议覆盖 | `https`/`git`/留空 | 选填 | 留空 |
| 6 | `enabled` | 是否纳入 manifest | `TRUE`/`FALSE`，默认 `TRUE` | 必填 | `TRUE` |
| 7 | `note` | 备注 | 文本 | 选填 | `markdown 分支另存一份` |

> 现仓库已有先例：`zeek-zhao/obsidian.git` 以两条记录分别挂 `obsidian` 与 `markdown` 分支到不同 path——重构后由「默认一条 + overrides 覆盖一条」表达，语义不变。

## 6. 辅助表列定义

### 6.1 `remotes`（生成 `<remote>` 节点）

| 列名 | 含义 | 格式 | 必填 | 示例 |
|---|---|---|---|---|
| `platform` | 平台标识 | 小写字母/数字；生成 `remote name` 前缀 | 必填 | `github` |
| `https_url` | HTTPS fetch 基准 | URL，无尾斜杠 | 必填 | `https://github.com` |
| `git_url` | SSH fetch 基准 | URL，无尾斜杠 | 必填 | `ssh://git@github.com` |

映射：`<remote name="{platform}_https" fetch="{https_url}" />`；`<remote name="{platform}_git" fetch="{git_url}" pushurl="{git_url}" />`（与现有 `_remotes.xml` 完全一致，git 协议多写 pushurl）。

### 6.2 `owners`

| 列名 | 含义 | 格式 | 必填 | 示例 |
|---|---|---|---|---|
| `owner` | 仓库属主（name 前缀） | 文本 | 必填 | `zeek-zhao` |
| `preferred_protocol` | owner 默认协议 | `https`/`git`/留空 | 选填 | `git` |
| `groups` | owner 组 | 逗号分隔 | 选填 | `owner-zeek-zhao` |
| `auto_sync` | 是否自有自动化同步 | `TRUE`/`FALSE` | 必填 | `TRUE` |
| `self_tag` | 自有标签组名 | 文本；留空=owner 名 | 选填 | `zeek-zhao` |

映射：`preferred_protocol`→仓库协议缺省值；`auto_sync=TRUE` 的 owner 触发第二阶段自动获取并打 `self_tag` 标签；`groups` 供生成器按需合并（现版本未合入 project groups，保持兼容）。

### 6.3 `enums`（下拉校验与值说明，不直接映射 XML）

| 列组 | 取值示例 | 用途 |
|---|---|---|
| `platform` | github/gitee/gitlab/yoctoproject | 校验主表 platform |
| `protocol` | https/git | 校验 protocol 列 |
| `visibility` | public/private/internal | 校验 visibility |
| `category` | 元工具与工程流程/运维与监控/… | 校验 category |
| `suggested_action` | 保留/观察/淘汰/待评估 | 校验 suggested_action |
| `language`/`topic` | 常用值建议 | 仅提示，不强制（自由扩展维度） |

### 6.4 `config`（键值对）

| 键 | 含义 | 默认 | 示例 |
|---|---|---|---|
| `default_protocol` | 全局缺省协议 | `https` | `https` |
| `quickstart_https_repo` | HTTPS 快速上手示例仓库 | — | `bazelbuild/examples.git` |
| `quickstart_self_repo` | 自有快速上手示例仓库 | — | `zeek-zhao/docker-sample.git` |

## 7. Excel 列 ↔ manifest 字段映射总表

### 7.1 `<project>` 节点映射（主表 + 自有合成行通用）

| Excel 来源 | 生成规则 | `<project>` 属性/节点 | 示例（输入→输出） |
|---|---|---|---|
| `path` | 原样 | `path` | `c++/bazel_examples` → `path="c++/bazel_examples"` |
| `platform` + 生效协议 | `f"{platform}_{protocol}"` | `remote` | `github`+`git` → `remote="github_git"` |
| `groups` + `platform` + `topic`（+自有行追加 `self_tag`） | 去重拼接，顺序：手填组→platform→topic(→self_tag) | `groups` | 手填`project`+`github`+`cpp` → `groups="project,github,cpp"` |
| `name` | 原样 | `name` | `bazelbuild/examples.git` → `name="bazelbuild/examples.git"` |
| `branch` | 原样 | `dest-branch` | `master` → `dest-branch="master"` |
| `branch` | `refs/heads/{branch}` | `revision` | `master` → `revision="refs/heads/master"` |
| `linkfiles` | 拆分 `;` 与 `:` | 子节点 `<linkfile src dest>` | `.:a/b` → `<linkfile src="." dest="a/b" />` |
| （无对应列） | 留空不生成 | `upstream/sync-c/sync-s/...` | 维持现行为：不输出 |

生效协议优先级（不变）：行 `protocol` > owner `preferred_protocol` > `config.default_protocol`（现默认 `https`）。

### 7.2 其他节点映射

| Excel 来源 | XML 产物 | 说明 |
|---|---|---|
| `remotes` 表整表 | `manifests/_remotes.xml` 每个 `<remote>` | git 协议带 `pushurl`，注释与现格式一致 |
| `owners` 表 `owner` 列 | `manifests/generated/by-owner/{owner}.xml` | 仅 `auto_sync=TRUE` 或显式列出的 owner 产出 |
| 主表/自动表行的 `language`（slug 化） | `generated/by-language/{slug}.xml` 归组 | slug 规则见 §7.3 |
| 行 `topic`（slug 化） | `generated/by-topic/{slug}.xml` 归组 | 同上 |
| `platform` | `generated/by-platform/{platform}.xml` 归组 | 文件名即平台名 |
| 生效协议 | `generated/by-protocol/{protocol}.xml` 归组 | `git`/`https` 两文件 |
| 全部分类文件 | `manifests/default.xml` `<include>` 索引 | 排序后全量包含，含 `_remotes.xml`/`_hooks.xml` 头 |
| `config.quickstart_*` | `manifests/examples/quickstart-*.xml` | 替代现生成器内硬编码字典 |
| `_hooks.xml` | 静态模板（include `_remotes.xml`） | 不进 Excel，维持现状 |

### 7.3 slug 规则（topic/language → 文件名，与现 `slugify()` 一致）

`c/c++→c-cpp`、`c++→cpp`、空格→`-`、`/`→`-`、`+`→`p`、`.`→`-`、连续`-`合并、去首尾`-`；示例：`openHarmony 11` → `openharmony-11`。

## 8. 设计决策与待确认点

| # | 决策点 | 建议 | 备选 |
|---|---|---|---|
| D1 | 生成器读 Excel 方式 | 直接读 `.xlsx`（新增依赖 `openpyxl`，CI 已有 Python 环境） | Excel 为编辑入口，另加 `--export-json` 快照入库便于 diff 审查（两者可并存，建议采用「直读+可选快照」） |
| D2 | Excel 文件路径 | `catalogs/manifests.xlsx` | 仓库根 `manifests.xlsx` |
| D3 | 自有标签组名 | `self_tag` 默认=owner 名（`zeek-zhao`），进 project groups | 固定字面量 `self` |
| D4 | `linkfiles` 单元格语法 | `src:dest;src:dest`（`:` 分隔、`;` 分条） | 每行一条多单元格 |
| D5 | 原 `catalogs/*.json` 去留 | 过渡期保留只读，切换稳定后删除 | 立即删除 |
| D6 | `enrich_catalog.py`（180 行，GitHub API 补全 category/visibility/description） | 退役，其能力由第二阶段 `repos_self` 自动化吸收 | 保留并适配 Excel |

## 9. 第二阶段实施预告（审核通过后另行确认任务书）

1. **自动获取**：`tools/sync_self_repos.py` 调 GitHub API 拉取 `auto_sync=TRUE` owner 的全部仓库+分支，重写 `repos_self` sheet（含 §4 全部列），`overrides_self` 不动；
2. **哈希触发**：CI/本地钩子计算 `catalogs/manifests.xlsx` 哈希（sha256），与上次记录比对；变化则执行 `generate_manifests --excel` 并校验生成物一致性（沿用 `--check` 机制），必要时自动提交「chore(manifest): regenerate from excel」；
3. **校验闭环**：path 唯一性、name 格式、platform∈remotes、枚举合法、`overrides_self.name∈repos_self`；违规即失败并列出行号。

## 10. 校验规则汇总（两阶段共用）

| 规则 | 说明 |
|---|---|
| 唯一键 | `name+path` 组合全局唯一（同一仓库多分支检出合法，如 obsidian 先例） |
| `path` 合法性 | 非空、唯一、不含 `..`、不以 `/` 开头 |
| `name` 格式 | `owner/repo.git` |
| 外键 | `platform` ∈ `remotes.platform`；`overrides_self.name` ∈ `repos_self.name` |
| 枚举 | `protocol/visibility/category/suggested_action/enabled` 取值受限（Excel 下拉 + 生成器双保险） |
| slug | topic/language 生成文件名前先 slug 化，冲突（同 slug 不同值）时报错 |

## 11. 影响面（第二阶段实施时同步修改）

`tools/generate_manifests.py`（读 Excel + 合成自有行）、`tools/sync_self_repos.py`（新增）、`tools/enrich_catalog.py`（退役，D6）、`tools/catalog_to_markdown.py`（适配 Excel 或读快照）、`.pre-commit-config.yaml`/CI（哈希触发 + 校验）、`README.md`、`docs/design.md`、`docs/implementation.md`、`docs/quickstart.md`。
