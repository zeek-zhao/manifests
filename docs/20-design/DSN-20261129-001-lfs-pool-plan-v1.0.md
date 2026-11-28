# DSN-20261129-001-lfs-pool-plan-v1.0

| 文档属性 | 内容 |
|---|---|
| 编号 | DSN-20261129-001-lfs-pool-plan-v1.0 |
| 版本 | v1.0（2026-11-29） |
| 编制 / 审核 | AI Agent (zeek.zhao) / 待用户审核 |
| 状态 | **规划版（暂缓实施）**——决策点 §8 全部确认后方可实施 |
| 适用 | 满足 Git LFS 条件的仓库纳入镜像池的处理规划 |
| 关联 | DSN-20261128-017（主方案，D1~D6 决策沿用）、GUIDE-20261129-001（操作手册） |

## 1. 背景与现状

- 当前池内 LFS 语义：mirror clone 时禁用 `filter.lfs.*`，**LFS 指针文件随池分发**（与普通 clone 语义一致），LFS 大文件内容不含（`pools-manifest.json.lfs_policy` 已声明）。
- 已知 LFS 实例：`t-thanh/autoware2020-course`（151MB kitti bag，上游 LFS 对象 404 导致 run21~23 连续失败，最终以指针语义入池）；robot 组其他仓亦存在 LFS 标记文件。
- 需求：当某 LFS 仓库的**内容**确实需要分发时（如数据集、模型、仿真 bag），按本规划以独立 image 承载。

## 2. 目标与非目标

- **目标**：为白名单内的 LFS 仓提供内容的加密分发通道（复用现有加密/红线/对账体系），按需构建与拉取。
- **非目标**：不改变组池镜像的指针语义；不做 LFS 仓全量自动同步；不替代上游 LFS 服务。

## 3. 选型对比

| 方案 | 描述 | 优点 | 缺点 | 结论 |
|---|---|---|---|---|
| **A. 每仓独立 OCI 镜像（`<group>-<repo>-lfs` tag）** | 与 D3 大仓机制同构：白名单仓单独构建，层内放 LFS 对象归档 | 拉取粒度=仓；复用每仓一层/加密/红线/对账全套；大文件不进组池 | 镜像数量随白名单增长 | **推荐** |
| B. 多仓聚合 LFS 镜像 | 白名单仓的对象包合成一个镜像 | 镜像数少 | 拉取粒度差（拿 1 仓下全部）；层膨胀 | 否 |
| C. 非 OCI 制品存储（gh release/S3） | 对象包直传制品库 | 实现简单 | 脱离 OCI 体系：无加密一致性、无红线门禁、对账另起炉灶 | 否 |

## 4. 层级划分（双层体系）

```
组池镜像  manifests-pool-<group>:run-N     ← 维持现状（LFS 指针入池，声明于 lfs_policy）
内容镜像  manifests-pool-<group>-<repo>-lfs:<tag> ← 新增（白名单仓，内容层）
   层 0 = lfs-objects.tar（git lfs fetch all 的 .git/lfs/objects 归档 + lfs-manifest.json：OID/size/path 对照表）
   private 仓 → 层 0 同样走 JWE 定向加密 + 红线自检（加密判定与主流程一致）
   -meta 镜像沿用（payload 分发）
```

- 层 0 的 `lfs-objects.tar` 结构：`<oid 前 2 位>/<oid>`（git-lfs 标准布局）+ 顶层 `lfs-manifest.json`（`[{oid, size, path-in-repo}]`，由 `git lfs ls-files --format` 生成）。
- **对账天然成立**：LFS 对象的 OID 即其 sha256——还原后 `sha256sum` 直接对照 `lfs-manifest.json`，无需额外摘要体系。

## 5. 触发方式

| 方式 | 说明 |
|---|---|
| workflow_dispatch（推荐） | `group-pool.yml` 扩展 inputs：`lfs_repos`（`组:仓` 逗号串，如 `robot:autoware2020-course`）；按需手动触发，**不做 schedule**（大文件带宽成本，无变更检测必要） |
| push | 仅 `config/pool-lfs-whitelist.txt`（白名单唯一出处）与工具变更时触发对应仓 |
| workflow_call | 预留 |

- 白名单文件 `config/pool-lfs-whitelist.txt`：行格式 `组:owner/repo.git`，作为"哪些 LFS 仓要内容池"的唯一出处（与 `pool-groups.txt` 同风格）。

## 6. 构建流程草案（复用主链）

原子 fetch（含 LFS：clone 时 `git lfs fetch --all`，对象进 bare 仓；clone 即删红线不变）→ 归档 lfs-objects.tar + lfs-manifest.json → （private 层 JWE 加密）→ 红线自检 → push `<group>-<repo>-lfs:<tag>` → -meta → 清理 prune。

预计改动：`pool_build.py` 增 `--lfs-repo` 模式（复用 stage_encrypt/push/meta）；`pool_restore.py` 增 `--lfs` 模式（解密后按 lfs-manifest.json 对账并按 path 回填到工作副本）；workflow 增 inputs 与分支 job。

## 7. 风险

| 风险 | 说明 | 缓解 |
|---|---|---|
| ghcr 单 blob 大小 | LFS 归档可能超常规层体积（>1GB），ghcr 对大 blob 的接受度需实测 | 实施前 demo 一个 151MB 样本；必要时分卷 tar（对账仍按对象粒度） |
| 上游 LFS 不可用 | autoware2020-course 已见 404 | fetch 失败降级跳过（沿用主链 skipped 机制），白名单仓内容池标记不可用 |
| 版本漂移 | 指针池（组镜像）与内容池（-lfs 镜像）构建时点不同 | 两镜像 manifest 均记录 head；lfs-manifest.json 含 OID，还原时可校验指针→对象一致性 |
| 带宽/时长 | 单仓 LFS 全量 fetch+推镜像耗时 | 仅白名单按需触发；分卷；CI 超时配置放宽 |
| 白名单膨胀 | 需求蔓延导致镜像数失控 | 白名单改动需 OWNER 确认（文件 review 即闸门） |

## 8. 决策点与待确认项（实施前置条件）

1. **白名单清单**：首批纳入哪些仓（候选：autoware2020-course？需 OWNER 确认内容分发需求真实存在）；
2. **镜像粒度**：按仓独立（推荐）vs 聚合；
3. **加密范围**：private LFS 仓层加密=沿用红线（推荐，默认）；public LFS 仓层明文；
4. **分卷阈值**：单层 >1GB 是否分卷（实施时 demo 实测 ghcr 行为后定）；
5. **回填方式**：还原后对象回填 `git lfs` 本地仓（`pool_restore --lfs` 自动）vs 仅落归档目录人工处理；
6. **清理策略**：-lfs 镜像旧 tag 保留几个版本。

## 9. 状态

**规划版，暂缓实施。** 待 §8 决策点确认后，另出落地计划（PLN）排期。

## 10. 变更记录

| 版本 | 日期 | 说明 |
|---|---|---|
| v1.0 | 2026-11-29 | 首版：选型（推荐独立镜像）、双层体系、触发方式、风险与决策点；暂缓实施 |
