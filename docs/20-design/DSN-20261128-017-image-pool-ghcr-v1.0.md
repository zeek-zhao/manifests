# 设计文档：manifests 镜像池 ghcr 公开分发（image-pool-ghcr）

| 项 | 内容 |
|---|---|
| 编号 | DSN-20261128-017-image-pool-ghcr-v1.1 |
| 日期 | 2026-11-28 |
| 编制 | zeek.zhao（AI 协作） |
| 审核 | 用户（v1→v2→v3 三轮审核，决策点 2026-11-28 确认） |
| 状态 | 已批准 |

## 1. 背景与目标

manifests 清单仓库（Excel 单一事实源→XML 清单）现有 129 条目：87 public + 42 private（全部 github/zeek-zhao）。目标：CI 按 topic 组将仓库内容打包为**公开 OCI 镜像**发布 ghcr.io，国内可加速拉取；private 仓库内容所在镜像层以 **imgcrypt（OCI 镜像层加密）**保护。

实测数据：有大小数据条目 108/129，总量 7.4 GB，最大单仓 3.3 GB，中位 3.4 MB，42 个 private 总量 742 MB；>500MB 大仓仅 2 个（ApolloAuto/apollo 3.3GB robot、qtkaifajingyan 622MB qt，均 public）。

## 2. 安全模型（红线）

- 「全公开包」≠ 私有内容明文公开。**42 个 private 仓库所在层必须加密后才能进入公开镜像**——CI 硬门禁（pool_scan.py 校验加密标记）。
- 消费侧：任何人可 `docker pull`（拿到密文层）；持 JWE 私钥者方可 `ctr images decrypt` 还原 private 内容。
- 单密钥对（JWE，RSA 2048 pkcs8）：公钥入仓 `keys/jwe.pub`；私钥存工作区 `/home/jenkins/zeek_work/.secrets/jwe.key`（600，AGENTS §4）+ repo secrets（仅 CI 自验证 job 使用）。
- 密钥泄漏=42 个 private 内容全暴露（密文公开可下载是前提）；轮换成本=全量重加密重推。

## 3. 加密方案

- 工具：imgcrypt（containerd 官方镜像层加密项目）。**R1 实测**：宿主 ctr 1.6.31（官方发行）无 encrypt/decrypt 子命令、无 go、无 nerdctl → 处置：golang 容器内编译 imgcrypt ctr（容器内 root 可连挂载的 `/run/containerd/containerd.sock`），二进制放 `/tmp/imgcrypt-out/`（临时区）；CI runner 上同法构建（或缓存镜像）。
- 加密动作：`ctr images encrypt --recipient jwe:keys/jwe.pub --layer <private层digest> <组镜像>`；JWE 加密在 ctr 客户端完成。
- 层映射：镜像 `FROM scratch`，每仓一条 `COPY`（层顺序与清单顺序一致），private 层 digest 由构建清单（pools-manifest.json）记录并核验。
- 消费侧解密：`ctr images decrypt --key /home/jenkins/zeek_work/.secrets/jwe.key`（需 imgcrypt 能力环境；GUIDE 提供 nerdctl/ctr 部署指引）。R2：解密端 containerd 需要 imgcrypt 能力——Demo 中实测记录真实边界。

## 4. 镜像组织

- **组镜像**：`ghcr.io/zeek-zhao/manifests-pool-<topic>:<tag>`，内含该组所有 ≤500MB 仓库；private 仓层=JWE 密文，public 仓层=明文 tar。
- **大仓独立镜像**（D3）：>500MB 每仓一个独立镜像 `manifests-pool-single-<repo>:<tag>`；按需拉取，不拉即不下。当前 2 个（均 public，无加密需求）；若未来出现 private 大仓，同样独立镜像+层加密。
- 层内布局：`/pools/<topic>/<repo>.tar`（mirror 包，D4）+ `pools-manifest.json`（sha256/加密标记/revision/tag）。

## 5. 原子约束与明文治理

- 下载 step 内逐仓闭环：`clone --mirror → tar → 构建输入就位 → shred 原明文 tar`；两段式（先整体下载再统一加密）禁止。
- 明文层「三不」：不 push（加密前镜像不推送）、不 save 出构建机（除 ctr import 必要路径）、不进构建缓存（构建后 `docker builder prune`）。
- 诚实声明：runner 明文瞬态窗口可压缩不可归零。

## 6. registry（D1）

- **仅 ghcr.io**，包公开（public）。
- ACR：保留配置占位（文档记载），当前不启用；启用时仅需增补推送凭据与目标地址。

## 7. Demo 设计（样本组=app）

| 仓库 | 属性 |
|---|---|
| zeek-zhao/kuaidian | private |
| zeek-zhao/linkManager | private |
| zeek-zhao/WorthTrack | public |
| zeek-zhao/tabharbor | public |

端到端：JWE 密钥对生成→原子 fetch+tar→docker build（每仓一层，FROM scratch）→docker save→ctr import→encrypt private 层→push ghcr 公开→消费侧 pull→确认 private 层密文→decrypt→还原→sha256 与直接 clone 全等。

## 8. CI 设计（group-pool.yml）

- 触发：`workflow_dispatch`（inputs: groups/singles/dry-run）+ `push`（paths: tools/pool_*）+ 周级 schedule。
- matrix：逐组并发；步骤=checkout→选组清单→**原子 fetch+tar**（GH_PAT 认证 private clone）→docker build→save/import→**encrypt**→push ghcr→pools-manifest.json 上传 artifact。
- 空间治理：组构建结束 `docker system prune -f` + builder prune；大仓 job 独立（单独 runner 磁盘预算）。
- 自验证 job（需私钥 secret）：pull 公开镜像→pool_scan.py 解包扫描（非加密层无 private 内容特征）→decrypt 抽样→sha256 校验。

## 9. 工具

- `pool_build.py`：从 snapshot 选组/选大仓，导出构建清单（含层序、加密标记）。
- `pool_restore.py`：消费侧一键还原（pull/import/decrypt/解包/校验）。
- `pool_scan.py`：解包扫描与加密门禁校验。

## 10. 验证方式

Demo 树 sha256 全等；CI run success+artifact 完整；pool_scan 零命中；判定交叉校验（Excel 仓库属性 vs GitHub API visibility）保留。

## 11. 风险清单

| # | 风险 | 对策 |
|---|---|---|
| R1 | imgcrypt 非官方发行组件 | **已实测 PASS**（容器内编译 v2.0.3，CI 同法） |
| R2 | ghcr 对加密 manifest 兼容性 | **已实测 PASS**（push+annotations 往返无损，LOG A4） |
| R3 | Docker 不能解密 imgcrypt 层 | 消费侧需 imgcrypt 能力环境；pool_restore.py + GUIDE 指引 |
| R4 | JWE 私钥单点 | 工作区 .secrets/ 600、不入仓不落日志；轮换=全量重推 |
| R5 | runner 明文瞬态窗口 | 逐仓闭环+shred+三不，不可归零（如实标注） |
| R6 | GH_PAT 全权限 | 可用；建议后续 fine-grained 最小权限 |
| R7 | public 仓库再分发许可证 | 清单标注 license，人工复核 |
| R8 | 大仓 runner 磁盘 | 独立镜像+独立 job |
| R9 | ghcr 存储 | public 免费；月度旧 tag 清理 workflow |
| R10 | GH_PAT 在 secrets 非 vars | 已核实 ✓ |
| R11 | 加密层完整性 | pools-manifest sha256 兜底 |

## 12. 待确认项

- ~~R1/R2 的 Demo 实测结论（编译与 ghcr 推拉往返）——实施首轮给出。~~
- 已实测（2026-11-28，详见 LOG A4）：R1 PASS（imgcrypt v2.0.3 容器内编译 + 定向层加密）；R2 PASS（ghcr 接受加密 manifest，annotations 往返无损）；R4 PASS（ctd-decoder 双样本解密对账全等）；R3 部分完成（docker 拉取密文 OK，匿名拉取待包 public 化 F-20）。
- 新增待确认：F-19（containerd pull 自动解密管线 TypeUrl 空）上游对齐后消费侧可复评；全组（robot/qt 等）扩展节奏；超大仓（apollo/qtkaifajingyan）按需独立构建的需求时机。

## 13. M15 增量：池内容改 git-mirror 裸仓（已批准实施）

**决策记录（2026-11-29 用户确认）**：
- D-M15-1 池内 tar 由「HEAD 快照归档」改为 **git mirror 裸仓本体**（`tar -C bare -cf - .`，顶层 HEAD/objects/refs/config；pools-manifest 增加 `format: "git-mirror"` 与 `repos[].head`）；
- D-M15-2 新增消费侧落位工具 `pool_mirror.py`：--repo/--all 落位裸仓、`--flat` 双布局开关（分组 `<root>/<组>/<仓>.git` / 平铺 `<root>/<仓>.git`）、`--fetch-base` 为 repo XML 的 remote fetch 配置项（默认 `file://<root>/`）、自动生成 `mirror-manifest.txt` 与 `pool-manifest.xml`、`_materialize` 原子落位+`rev-parse HEAD==entry.head` 校验。

**实现**（09a5e10/88c791e）：pool_build stage_fetch 重写、pool_restore 重写（fetch_repo_tar 共用下载/解密/对账，--layer 移除）、consumer-kit 增补第五文件 pool_mirror.py。缺陷 F-21（对账对象误用层 blob）已修——对账对象=层内仓 tar（entry["path"]）。

**验证**：run-29/run-30+kit 全绿；smoke 六仓全链演练（含 private 解密）MIRROR_OK 6/6、rev-parse 一致、XML fetch=file:// 正确；CThreadPool archive 215KB vs mirror 174KB（mirror 更小）、fsck 0 错误、file:// clone OK。

## 变更记录

| 版本 | 日期 | 说明 |
|---|---|---|
| v1.0 | 2026-11-28 | 首版（v3 方案经用户三轮审核+决策点确认后落盘） |
| v1.1 | 2026-11-29 | §13 M15 增量：git-mirror 裸仓布局 + pool_mirror 落位工具（决策已确认，已实施） |
