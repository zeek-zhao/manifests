# 设计文档 DSN-20261128-001：基于 Excel 动态生成 manifest

| 文档属性 | 内容 |
|---|---|
| 编号 | DSN-20261128-001 |
| 版本 | v0.4（待复核；CI 触发链路按用户反馈修订，其余同 v0.3） |
| 日期 | 2026-11-28 |
| 编制 | AI Agent (zeek.zhao) |
| 审核 | 用户（v0.4 复核中） |
| 状态 | 待复核（复核通过后进入第二阶段实施） |

## 0. 修订记录

| 版本 | 日期 | 修订内容 | 依据 |
|---|---|---|---|
| v0.1 | 2026-11-28 | 初稿：7-sheet 结构（repos_external / repos_self / overrides_self / remotes / owners / enums / config） | 用户初始需求 |
| v0.2 | 2026-11-28 | 精简为 4-sheet；自有仓库并入主表由自动化维护（人工仅配 path 与 linkfiles 两项）；remotes 表升级 fetch/push URL 映射并考虑代理；新增 readme 说明 sheet；砍除 3 个管理列；决策点 D1–D6 确认落档 | 用户修订反馈；v0.1 决策点 D1–D6 全部同意 |
| v0.3 | 2026-11-28 | ①不采纳砍除管理列（D7 反转），主表扩充仓库描述信息（新增 purpose/contents/relations，恢复 visibility/category/suggested_action），目标「不打开仓库即知其用途」；②D8/D9/D10 确认落档；③新增双 CI 工作流设计（全量自动化 + 手动仅更新工作簿） | 用户 v0.3 反馈 |
| v0.4 | 2026-11-28 | 仅修订 §11 双 CI 工作流触发链路：手动流改为「基于主分支创建 Excel 分支→单提交推送→人工修改后合并回主分支并删分支」；全量流改为「合并完成后人工手动触发」，移除 push 自动触发；哈希机制降级为幂等辅助。其余内容保持 v0.3 不变 | 用户触发链路反馈 |

## 1. 背景与目标

现有链路以 `catalogs/*.json` 为单一事实来源，`tools/generate_manifests.py` 渲染为多维度 repo XML 清单。重构目标：

1. 单一事实来源改为 Excel 工作簿，仓库清单表格化维护；
2. **自有仓库（zeek-zhao 名下）由自动化获取并全部自动填写**，人工仅配置两项：本地检出路径（path）、链接文件位置（linkfiles）；
3. 外部仓库在主表逐行人工维护；
4. 远程拉取/推送 URL 不写在仓库行内，由平台映射表统一提供，支持代理场景；
5. 工作簿自带说明 sheet，字段含义与填写方法开卷可查。

## 2. 工作簿总体设计（4 sheets，v0.2 确立、v0.3 延续）

文件路径：`catalogs/manifests.xlsx`（D2 已确认）。

| Sheet 名 | 职责 | 维护方式 |
|---|---|---|
| `repos` | 主表：全部仓库检出条目（自有+外部混合），一行一个检出条目 | 自有行=自动化刷新（path/linkfiles 人工优先）；外部行=人工 |
| `remotes` | 平台名 → fetch/push URL 映射（含代理列），生成 `<remote>` 节点 | 人工低频 |
| `config` | 全局生成配置键值对（默认协议、代理开关、自有 owner、快速上手示例） | 人工低频 |
| `readme` | 说明 sheet：设计说明、字段字典、填写指引 | 随设计更新 |

### 2.1 v0.1 → v0.2 结构变更与理由（应反馈第 4 条逐项说明）

| 变更 | 理由 |
|---|---|
| 删除 `repos_self` 与 `overrides_self` 独立 sheet，自有仓库行并入主表 | 用户明确不需要自有独立 sheet；owner 均为本人，主表按 name 前缀即可识别自有行，自动化直接维护，覆盖需求收敛为 path/linkfiles 两项人工配置，无需独立覆盖表 |
| 删除 `owners` 表 | owner 唯一（zeek-zhao），owner 级协议偏好无实际区分场景；自有 owner 识别改为 `config.self_owner` 单键 |
| 删除 `enums` 表 | 枚举值说明并入 `readme` 字段字典；合法性行校验由生成器二次兜底（下拉校验用 Excel 内置列表常量实现，不占独立 sheet） |
| 主表管理列（v0.2 曾砍除，v0.3 依用户反馈恢复并扩充） | 用户目标「不打开仓库就能清楚知道每个仓库是干什么的」——主表同时承担仓库知识库职能；扩充 3 个描述列（purpose/contents/relations），恢复 visibility/category/suggested_action；这些列均不参与 XML 生成，纯文档/管理用途 |
| 不设自有标签列（v0.1 的 `self_tag`） | 用户明确不需要；自有行由 name 前缀识别，by-owner 维度文件照常由 name 派生生成，不依赖标签列 |
| 新增 `readme` 说明 sheet | 用户要求：设计说明、字段含义用途、人工/自动分工与填写示例开卷可查 |

## 3. 主表 `repos` 列定义（v0.3：17 列 = 生成列 9 + 描述列 4 + 管理列 3 + 备注 1）

### 3.1 生成列（参与 manifest XML 生成与维度拆分）

| # | 列名 | 含义 | 格式/约束 | 必填 | 人工/自动 | 填写示例 |
|---|---|---|---|---|---|---|
| 1 | `name` | 仓库全名 `owner/repo.git` | 文本；`/` 分隔且 `.git` 结尾；**唯一键为 name+path 组合** | 必填 | 自有行自动生成；外部行人工 | `bazelbuild/examples.git` |
| 2 | `path` | `repo sync` 本地检出目录 | 文本；全局唯一；不含 `..`、不以 `/` 开头 | 必填 | **自有仓库人工配置项①**（留空时自动化填默认 `project/<repo名>`，已有值不覆盖） | `c++/bazel_examples` |
| 3 | `branch` | 跟踪分支 | 文本；非空 | 必填 | 自有行=自动化填 API default_branch；外部行人工 | `master` |
| 4 | `platform` | 平台名引用（→ remotes 表） | 必须存在于 remotes.platform | 必填 | 自有行自动；外部行人工 | `github` |
| 5 | `protocol` | 协议偏好 | `https`/`git`/留空（继承 config.default_protocol） | 选填 | 自有行留空；外部行可选 | `git` |
| 6 | `topic` | 主题维度（slug 化后进 by-topic） | 文本自由值 | 必填 | 自有行人工可改；外部行人工 | `cpp` |
| 7 | `language` | 语言维度（仅影响 by-language 拆分，不进 project 属性） | 文本自由值 | 必填 | 同上 | `c/c++` |
| 8 | `groups` | 自定义分组 | 逗号分隔多值；生成时自动追加 `platform,topic` | 选填 | 人工 | `project,embedded` |
| 9 | `linkfiles` | 链接文件位置（链接到检出树其他位置） | 多条 `;` 分隔，每条 `src:dest`；src 为仓库内源（整库用 `.`） | 选填 | **自有仓库人工配置项②**（自动化不覆盖） | `.:sample/cpp-sample/docker` |

### 3.2 描述列（仓库知识库，不映射 XML；目标：不打开仓库即知其用途）

| # | 列名 | 含义 | 格式/约束 | 必填 | 人工/自动 | 填写示例 |
|---|---|---|---|---|---|---|
| 10 | `description` | 一句话描述 | 文本，建议 ≤80 字 | 选填 | 自有行=自动化填 API description；外部行人工 | `Bazel 官方示例仓库` |
| 11 | `purpose` | 仓库用途 | 文本；为什么收录/管理该仓库 | 选填 | 人工（API 无此语义信息） | `作为 manifest 管理的第三方示例集，供 repo sync 演练` |
| 12 | `contents` | 主要内容 | 文本；仓库里有什么（关键目录/组件） | 选填 | 人工 | `examples/ 下 20+ 构建示例；CI 配置模板` |
| 13 | `relations` | 与其他仓库的关系 | 文本；依赖/派生/配套关系，可写对方 name | 选填 | 人工 | `配套 manifests 快速上手示例；派生自 bazelbuild/examples` |

### 3.3 管理列与备注（不映射 XML）

| # | 列名 | 含义 | 格式/约束 | 必填 | 人工/自动 | 填写示例 |
|---|---|---|---|---|---|---|
| 14 | `visibility` | 可见性 | `public`/`private`/`internal` | 选填 | 自有行=自动化填 API visibility；外部行人工 | `public` |
| 15 | `category` | 管理分类 | 中文枚举（元工具与工程流程/运维与监控/…） | 选填 | 人工 | `元工具与工程流程` |
| 16 | `suggested_action` | 处置建议 | `保留`/`观察`/`淘汰`/`待评估` | 选填 | 人工 | `保留` |
| 17 | `note` | 备注（自由文本） | 文本 | 选填 | 人工；自动化仅在「上游仓库已消失」时标注 | `上游更新频繁，季度复查` |

> 列数说明（v0.3 改动理由）：D7 原建议「砍除三管理列」用户不采纳，反转为扩充——新增 `purpose`/`contents`/`relations` 三个语义描述列（API 无法提供，必须人工沉淀），恢复 v0.2 曾砍除的三管理列；`description`/`visibility` 由自有仓库自动化填充。全表 17 列分三块，readme 字段字典逐列解释，避免混用。

## 4. `remotes` 平台映射表（fetch/push URL，行内不写 URL）

| 列名 | 含义 | 格式 | 必填 | 示例 |
|---|---|---|---|---|
| `platform` | 平台标识（主表引用键） | 小写字母/数字 | 必填 | `github` |
| `https_url` | HTTPS 默认 URL（fetch 与 push） | URL 无尾斜杠 | 必填 | `https://github.com` |
| `git_url` | SSH URL（fetch 与 pushurl） | URL 无尾斜杠 | 必填 | `ssh://git@github.com` |
| `proxy_https_url` | 走代理时的 HTTPS fetch URL | URL 无尾斜杠；留空=无代理 | 选填 | `https://ghproxy.example.com/github.com` |

生成 `<remote>` 规则（替代 v0.1 单一 URL 列）：

| 生效协议 | config.use_proxy_https | fetch | pushurl |
|---|---|---|---|
| `https` | FALSE（默认） | `https_url` | `https_url` |
| `https` | TRUE | `proxy_https_url`（该平台未配代理列则回退 `https_url`） | `https_url`（push 始终走真实地址） |
| `git`（SSH） | 任意 | `git_url` | `git_url`（SSH 走 22 端口代理场景罕见，不设代理列；如确需再扩展 `proxy_git_url`） |

remote 节点名仍为 `{platform}_{protocol}`，与现有 `_remotes.xml` 兼容（git 协议多写 pushurl 的既有行为保留）。

> 未填写规则：仓库行不携带任何 URL（只写 platform 名）；各场景默认值由本表与 config 提供，「未填写时使用默认 URL」由此实现。

## 5. `config` 全局配置表（键值对）

| 键 | 含义 | 默认 | 示例 |
|---|---|---|---|
| `default_protocol` | 全局缺省协议（行 protocol 留空时生效） | `https` | `https` |
| `self_owner` | 自有仓库属主（主表 name 前缀识别键，自动化目标） | `zeek-zhao` | `zeek-zhao` |
| `use_proxy_https` | HTTPS fetch 是否走代理列 | `FALSE` | `FALSE` |
| `quickstart_https_repo` | HTTPS 快速上手示例仓库 | — | `bazelbuild/examples.git` |
| `quickstart_self_repo` | 自有快速上手示例仓库 | — | `zeek-zhao/docker-sample.git` |

## 6. `readme` 说明 sheet 内容设计

| 区块 | 内容 |
|---|---|
| A 工作簿设计说明 | 本工作簿用途（manifest 单一事实来源）、4-sheet 分工、更新流程概述（修改推送 → 哈希检测 → 自动重建 manifest → CI 校验）、版本与修订日期 |
| B 字段字典 | 全部 sheet × 全部列：列名 / 含义 / 用途（映射哪个 manifest 字段或管理用途）/ 人工填 or 自动生成 / 格式约束 / 填写示例（与本文档 §3–§5 同源，Excel 侧为操作视图） |
| C 填写指引 | ①新增外部仓库：在 repos 表按 §3 列顺序填一行，platform 必须是 remotes 表已有平台名；②自有仓库配置：仅在自动化生成的行上填 path 与 linkfiles 两列，其余列不要手改（下次同步会被刷新）；③代理开关：config.use_proxy_https=TRUE 且 remotes 表对应平台填 proxy_https_url 才生效；④常见校验错误对照（path 重复、platform 未登记、name 格式错误）；⑤描述列分工：description/visibility 由自动化填充（自有行），purpose/contents/relations/category/suggested_action 为人工知识沉淀列，自动化永不覆盖 |

## 7. Excel ↔ manifest 字段映射总表

### 7.1 `<project>` 节点映射（自有行与外部行通用）

| Excel 来源 | 生成规则 | `<project>` 属性/节点 | 示例（输入→输出） |
|---|---|---|---|
| `path` | 原样 | `path` | `c++/bazel_examples` → `path="c++/bazel_examples"` |
| `platform` + 生效协议 | `f"{platform}_{protocol}"` | `remote` | `github`+`git` → `remote="github_git"` |
| `groups` + `platform` + `topic` | 去重拼接，顺序：手填组→platform→topic | `groups` | 手填`project`+`github`+`cpp` → `groups="project,github,cpp"` |
| `name` | 原样 | `name` | `bazelbuild/examples.git` → `name="bazelbuild/examples.git"` |
| `branch` | 原样 | `dest-branch` | `master` → `dest-branch="master"` |
| `branch` | `refs/heads/{branch}` | `revision` | `master` → `revision="refs/heads/master"` |
| `linkfiles` | 拆分 `;` 与 `:` | 子节点 `<linkfile src dest>` | `.:a/b` → `<linkfile src="." dest="a/b" />` |
| （无对应列） | 留空不生成 | `upstream/sync-c/sync-s/...` | 维持现行为：不输出 |

生效协议优先级（不变）：行 `protocol` > `config.default_protocol`（v0.2 起不再有 owner 级偏好，owners 表已删）。

### 7.2 其他节点映射

| Excel 来源 | XML 产物 | 说明 |
|---|---|---|
| `remotes` 表整表 | `manifests/_remotes.xml` 每个 `<remote>` | 按 §4 规则取 fetch/pushurl（含代理开关） |
| 主表 `name` 前缀 owner | `generated/by-owner/{owner}.xml` | owner 由 name 派生（`get_owner()`），与自有标签无关；维度文件照常产出 |
| `language`（slug 化） | `generated/by-language/{slug}.xml` 归组 | slug 规则 §7.3 |
| `topic`（slug 化） | `generated/by-topic/{slug}.xml` 归组 | 同上 |
| `platform` | `generated/by-platform/{platform}.xml` 归组 | 文件名即平台名 |
| 生效协议 | `generated/by-protocol/{protocol}.xml` 归组 | `git`/`https` 两文件 |
| 全部分类文件 | `manifests/default.xml` `<include>` 索引 | 排序后全量包含，含 `_remotes.xml`/`_hooks.xml` 头 |
| `config.quickstart_*` | `manifests/examples/quickstart-*.xml` | 替代生成器内硬编码字典（D1 已确认方案的一部分） |
| `_hooks.xml` | 静态模板（include `_remotes.xml`） | 不进 Excel，维持现状 |

### 7.3 slug 规则（与现 `slugify()` 一致）

`c/c++→c-cpp`、`c++→cpp`、空格→`-`、`/`→`-`、`+`→`p`、`.`→`-`、连续`-`合并、去首尾`-`；示例：`openHarmony 11` → `openharmony-11`。

## 8. 自有仓库自动化写入策略（第二阶段 `tools/sync_self_repos.py`）

1. **识别**：主表中 name 前缀 == `config.self_owner` 的行判定为自有行；
2. **刷新范围**：自有行刷新 `branch`（API default_branch）、`platform`、`description`、`visibility`（API 值），并确保 `protocol` 留空（继承默认）；`purpose`/`contents`/`relations`/`category`/`suggested_action`/`note` 为人工知识列，自动化永不覆盖；
3. **人工优先两项**：`path` 已有值不覆盖（人工配置项①），留空填默认 `project/<repo名>`；`linkfiles` 永不覆盖（人工配置项②）；
4. **同仓库多行**：同一 name 的第一行视为自动行刷新，其余行视为人工检出条目原样保留（兼容现仓库 obsidian 双分支双 path 先例）；
5. **上游消失**：API 已不存在但表中仍有的自有行不删除，在 note 标注「上游已删除，待人工确认」；
6. **外部行保护**：非 self_owner 前缀的行自动化完全不触碰。

## 9. 校验规则汇总

| 规则 | 说明 |
|---|---|
| 唯一键 | `name+path` 组合全局唯一（同仓库多分支多路径检出合法） |
| `path` 合法性 | 非空、唯一、不含 `..`、不以 `/` 开头 |
| `name` 格式 | `owner/repo.git` |
| 外键 | `platform` ∈ `remotes.platform` |
| 枚举 | `protocol` ∈ {https, git, 留空}；Excel 侧用下拉常量，生成器二次校验兜底 |
| slug 冲突 | topic/language slug 化后同 slug 不同值时报错 |

## 10. 决策点状态

| # | 决策点 | 结论 |
|---|---|---|
| D1 | 生成器直读 `.xlsx`（openpyxl）+ 可选 `--export-json` 快照 | **已确认采纳** |
| D2 | Excel 路径 `catalogs/manifests.xlsx` | **已确认采纳** |
| D3 | 自有标签组名 | **随 v0.2 结构取消**（用户不要标签列，自有行靠 name 前缀识别） |
| D4 | linkfiles 语法 `src:dest;src:dest` | **已确认采纳** |
| D5 | 原 `catalogs/*.json` 过渡期保留只读，稳定后删除 | **已确认采纳** |
| D6 | `enrich_catalog.py` 退役，能力并入自动化 | **已确认采纳** |
| D7（新） | 主表砍除 visibility/category/suggested_action 三管理列 | **用户不采纳，反转为扩充**：恢复三列并新增 purpose/contents/relations 描述列（见 §3.2/§3.3） |
| D8（新） | 4-sheet 结构：owners/enums 并入 config/readme | **已确认采纳** |
| D9（新） | 仓库行不设 URL 覆盖列，fetch/push 全走 remotes 平台映射表 | **已确认采纳** |
| D10（新） | 自有行 branch 以 API default_branch 为准；需特殊分支时以同 repo 人工行表达 | **已确认采纳** |
| D11（新） | CI 双工作流设计（全量自动化 excel-sync + 手动 excel-validate，含幂等收敛机制） | **触发链路已按用户 v0.4 反馈修订**（§11.1–§11.5：Excel 分支流转 + 合并后人工触发全量流），修订版待复核 |

## 11. CI 工作流设计（v0.4：触发链路按用户反馈修订）

现有 `.github/workflows/ci.yml`（pre-commit + 生成一致性检查）保持不变；新增以下两个工作流，与 ci.yml 分工互补。**两个工作流均仅手动触发**，流转链路完全由人工控制。

### 11.1 `excel-validate.yml` — 手动工作流（仅更新 Excel 工作簿本身）

**职责**：基于主分支创建 Excel 分支并推送规范化结果，供用户拉取修改；**不触发仓库信息抓取**（不调 GitHub API、不改自有行数据）、不重建 manifest、**不做合并**。

| 项 | 设计 |
|---|---|
| 触发 | 仅 `workflow_dispatch`（人工手动） |
| base 分支 | 主分支（默认 `main`，dispatch 入参 `base_branch` 可指定） |
| 步骤 | ① 基于 base 分支创建 Excel 分支（命名 `excel/update-<YYYYMMDD-HHmm>`，同名已存在则报错不覆盖）→ ② 工作簿结构与规则校验（sheet/列名齐全、§9 全部规则、readme 字段字典与实际列一致性）→ ③ 规范化处理（列宽/冻结首行/下拉校验重刷，openpyxl 原位更新）→ ④ 可选导出 JSON 快照（`--export-json`，D1 方案）→ ⑤ **产生且仅产生一个提交**「chore(excel): validate & normalize workbook」推送到 Excel 分支 → 结束 |
| 边界 | 不合并回主分支（由用户完成）；不在 base 分支上产生提交；不删除分支（用户还要在其上修改） |

### 11.2 `excel-sync.yml` — 全量自动化工作流（人工在合并完成后触发）

**职责**：自动完成所有仓库信息的获取与 manifest 更新。

| 项 | 设计 |
|---|---|
| 触发 | 仅 `workflow_dispatch`（人工手动；**前置条件**：用户已将 Excel 分支合并回主分支并删除该分支） |
| 步骤 | checkout → `sync_self_repos.py` 按 §8 策略更新主表自有行（GitHub API，TOKEN 临时注入）→ 生成器 `--excel` 重建全部 manifest → `--check` 校验生成物一致 → §9 规则校验（违规列出行号失败退出）→ Excel 或 manifest 有变更则自动提交「chore(manifest): regenerate from excel」并推送（无变更则跳过提交）→ 更新哈希记录 `.github/.excel-hash` |
| 幂等机制 | 哈希检测**不再是触发条件**（v0.4 移除 push 自动触发），仅作内部幂等辅助：记录上次全量处理后的工作簿状态，重复 dispatch 且无变化时快速跳过重建；自动提交仍带 `[skip ci]`（防御未来误恢复自动触发产生循环） |
| 失败处理 | 任一步骤失败即红，不改哈希记录；仓库信息抓取失败（API 限流）时保留旧数据不写入半成品 |

### 11.3 触发链路与流转步骤（合并前后的触发关系）

```
[人工] 触发 excel-validate（选 base 分支）
   └─ CI：基于 base 创建 excel/update-<ts> 分支 → 校验+规范化 → 单提交推送（不合并）
[人工] 拉取 Excel 分支 → 手动修改 Excel → 推送到 Excel 分支
[人工] 将 Excel 分支合并回主分支（base）→ 删除该 Excel 分支
[人工] 触发 excel-sync（此时才抓取仓库信息）
   └─ CI：sync_self_repos 更新自有行 → 重建 manifest → 校验 → 有变更则自动提交推送
```

时序约束：**excel-sync 只允许在 Excel 分支合并、删除之后人工触发**；工作簿的规范化与人工修改全部经由 Excel 分支流转，主分支上只出现「合并提交 + sync 自动提交」两类工作簿相关提交。

### 11.4 Excel 分支的创建与清理

| 环节 | 责任方 | 规则 |
|---|---|---|
| 创建 | CI（excel-validate） | 基于 base 分支；命名 `excel/update-<YYYYMMDD-HHmm>`；同名已存在即失败退出，不覆盖 |
| 修改 | 用户 | 拉取分支后手动编辑工作簿，仅此分支，不在其上做开发内容 |
| 合并 | 用户 | 修改推送后由用户合并回 base（普通 merge，合并提交人须符合 §2 提交身份规范） |
| 删除 | 用户 | 合并完成后用户删除该 Excel 分支（CI 永不删除——分支上还承载用户未合并的修改） |

### 11.5 触发设计改动理由（v0.3 → v0.4）

| 改动 | 理由 |
|---|---|
| 全量流移除「push+哈希变化自动触发」，改为仅人工 dispatch | 用户明确要求「合并完成后由我手动触发」——把执行时机完全交给人工，避免人工还在 Excel 分支上流转时，push 自动触发让 CI 在主分支上跑旧数据或与人工修改竞争 |
| 手动流从「就地提交 base」改为「base 建分支+单提交推送+不合并」 | CI 产生的规范化结果先落隔离分支，经人工拉取、修改、审核后才进主分支，避免未审核变更直接污染主干；单提交保证拉取与合并干净无噪音 |
| 分支删除责任归用户而非 CI | 分支上承载用户未合并的修改，CI 删除会丢工作区；用户合并后自行清理 |
| 哈希机制降级为内部幂等辅助 | 触发权移交人工后，push 自动比对失去意义；保留哈希记录用于重复 dispatch 快速跳过，防重复重建 |

## 12. 第二阶段实施预告（本版复核通过后另行确认任务书）

1. **自动化**：`tools/sync_self_repos.py` 按 §8 策略更新主表自有行（GitHub API：仓库+分支+描述+可见性）；
2. **生成器改造**：`generate_manifests.py` 增加 `--excel` 读取（openpyxl，D1）、remotes 代理规则（§4）、quickstart 从 config 表读取；
3. **工作流落地**：新增 `excel-validate.yml`（建 Excel 分支+单提交）与 `excel-sync.yml`（合并后人工触发的全量流，§11 设计），现有 ci.yml 保持不变；
4. **校验闭环**：§9 规则全部落进生成器与 CI，违规失败并列出行号；
5. **文档**：README/design/implementation/quickstart 同步改写为 Excel 工作流。

## 13. 影响面（第二阶段实施时同步修改）

`tools/generate_manifests.py`（读 Excel + remotes 代理规则 + quickstart 从 config 表读取）、`tools/sync_self_repos.py`（新增）、`tools/enrich_catalog.py`（退役，D6）、`tools/catalog_to_markdown.py`（适配 Excel 或读快照）、`.github/workflows/excel-sync.yml` 与 `excel-validate.yml`（新增，§11）、`.github/.excel-hash`（新增哈希记录，幂等辅助）、`.pre-commit-config.yaml`（Excel 校验钩子）、`README.md`、`docs/design.md`、`docs/implementation.md`、`docs/quickstart.md`。
