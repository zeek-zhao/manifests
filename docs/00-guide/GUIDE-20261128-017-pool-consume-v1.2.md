# GUIDE-20261128-017-pool-consume-v1.2

| 文档属性 | 内容 |
|---|---|
| 编号 | GUIDE-20261128-017-pool-consume-v1.2 |
| 版本 | v1.2（2026-11-29）：离线消费工作流重写（kit 套件为主线），实测矩阵更新 |
| 编制 / 审核 | AI Agent (zeek.zhao) / 待用户审核 |
| 状态 | 生效中 |
| 适用 | manifests 组镜像池消费侧（DSN-20261128-017-v1.0） |

## 0. 消费套件（kit 镜像，推荐入口）

`ghcr.io/zeek-zhao/manifests-pool-kit:latest` 是离线消费的一体化套件（FROM scratch，四个文件）：

| 文件 | 作用 |
|---|---|
| `pool_restore.py` | 还原工具（纯标准库，Python 3.10+） |
| `ctd-decoder` | 解密器静态二进制（linux-amd64，imgcrypt v2.0.3） |
| `README.txt` | 离线速查（同本文档精简版） |
| `checksums.txt` | 完整性校验（`sha256sum -c`） |

**国内网络/完全离线场景**（连 manifests 仓库都无法访问时）：

```bash
# ①（有网机器，一次性）拉取并导出三个镜像为离线文件
docker pull ghcr.io/zeek-zhao/manifests-pool-kit:latest
docker pull ghcr.io/zeek-zhao/manifests-pool-<组>:run-<N>
docker pull ghcr.io/zeek-zhao/manifests-pool-<组>:run-<N>-meta
docker save ghcr.io/zeek-zhao/manifests-pool-kit:latest -o pool-kit.tar
docker save ghcr.io/zeek-zhao/manifests-pool-<组>:run-<N> -o pool-<组>.tar
docker save ghcr.io/zeek-zhao/manifests-pool-<组>:run-<N>-meta -o pool-<组>-meta.tar
# ②（U 盘/内网传输这三个 .tar 文件）
# ③（离线机器）导入
docker load -i pool-kit.tar && docker load -i pool-<组>.tar && docker load -i pool-<组>-meta.tar
```

此后所有步骤只依赖本地 docker 与（还原 private 仓时）一份 JWE 私钥。

## 0.1 消费全流程（每步命令与预期结果）

```bash
# 步骤 1：解包 kit 套件
docker pull ghcr.io/zeek-zhao/manifests-pool-kit:latest
docker create --name kit --entrypoint /bin/true ghcr.io/zeek-zhao/manifests-pool-kit:latest
docker cp kit:/kit ./pool-kit && docker rm kit
# 预期：./pool-kit/ 下有 pool_restore.py、ctd-decoder、README.txt、checksums.txt

# 步骤 2：完整性校验
cd pool-kit && sha256sum -c checksums.txt && cd ..
# 预期：四个文件全部输出 OK

# 步骤 3：拉取目标组镜像（离线场景已由 docker load 提供，跳过）
docker pull ghcr.io/zeek-zhao/manifests-pool-smoke:run-27

# 步骤 4：还原 public 仓库（无需私钥）
GH_PAT=<可选> python3 pool-kit/pool_restore.py \
  --image ghcr.io/zeek-zhao/manifests-pool-smoke:run-27 \
  --meta  ghcr.io/zeek-zhao/manifests-pool-smoke:run-27-meta \
  --repo CThreadPool \
  --decoder ./pool-kit/ctd-decoder --out restore/
# 预期：RESTORE_OK CThreadPool -> restore/pools/smoke/CThreadPool.tar（sha256 … 对账一致）

# 步骤 5：还原 private 仓库（需 JWE 私钥）
python3 pool-kit/pool_restore.py \
  --image ghcr.io/zeek-zhao/manifests-pool-smoke:run-27 \
  --meta  ghcr.io/zeek-zhao/manifests-pool-smoke:run-27-meta \
  --repo database-sample \
  --key /path/to/jwe.key --decoder ./pool-kit/ctd-decoder --out restore/
# 预期：RESTORE_OK database-sample -> restore/pools/smoke/database-sample.tar（sha256 … 对账一致）
# 私钥误缺时预期：FATAL: 仓库 database-sample 位于加密层，还原需 --key <JWE 私钥>

# 步骤 6：核对产物
ls restore/pools/<组>/   # 预期：各 <仓库>.tar 与 pools-manifest.json（工具自动落盘供二次对账）
tar -tf restore/pools/<组>/<仓库>.tar | head   # 预期：git 快照目录树
```

**实测矩阵**（run-27/smoke 组，2026-11-29）：6/6 对账一致——public 2 仓（product-sample、CThreadPool）无 key 匿名路径；private 4 仓（standard-version、database-sample、docker-sample、vue-sample）带 key 解密；缺 key 保护文案验证。

## 1. 你将得到什么

每个 topic 组一个公开 OCI 镜像（ghcr.io/zeek-zhao/manifests-pool-<组名>:<tag>）：

- **public 仓库**：明文层，`docker pull` 后解包即得（`pools/<组>/<仓库>.tar`，git 快照 tar）；
- **private 仓库**：imgcrypt(JWE) 加密层，任何人可拉到**密文**，持私钥者用 `tools/pool_restore.py` 还原；
- **-meta 镜像**（同名 tag + `-meta`）：明文小镜像，只含解密 payload（公钥参数+摘要，无机密），还原工具自动取用。

镜像内布局（每仓一层，层内路径统一）：

```
pools/<组>/<仓库>.tar          # git 快照（git archive HEAD）
pools/<组>/pools-manifest.json # 条目：name/layer_index/encrypted/sha256/head
```

## 2. 前提准备（一次性）

| 项 | 说明 |
|---|---|
| ctd-decoder | containerd 解密工具（imgcrypt v2.0.3 `cmd/ctd-decoder` 编译产物；无 release 二进制，可用 go 构建或向管理员索取） |
| JWE 私钥 | 与构建公钥（仓库 `keys/jwe.pub`）配对的私钥，本机存放 `.secrets/jwe-pool.key`（600） |
| Python 3.10+ | 仅标准库 |
| token（可选） | 镜像公开后匿名可拉；若镜像仍为 private，导出 `GH_PAT` |

## 3. 还原命令

### 3.1 还原 private 仓库（加密层）

```bash
python3 tools/pool_restore.py \
  --image ghcr.io/zeek-zhao/manifests-pool-app:enc \
  --meta  ghcr.io/zeek-zhao/manifests-pool-app:enc-meta \
  --repo kuaidian \
  --key ~/.secrets/jwe-pool.key \
  --decoder ./ctd-decoder \
  --out restore/
# 成功输出：RESTORE_OK kuaidian -> restore/pools/app/kuaidian.tar（sha256 对账一致）
```

### 3.2 还原 public 仓库（明文层）

```bash
docker pull ghcr.io/zeek-zhao/manifests-pool-app:enc
docker create --name t ghcr.io/zeek-zhao/manifests-pool-app:enc
docker cp t:pools/app/WorthTrack.tar .
docker rm t
```

（或直接 `pool_restore.py`——public 层不加密，工具同样按 sha256 对账输出。）

### 3.3 批量还原

对 `pools-manifest.json` 中目标条目循环调用 3.1（`--repo` 换名即可；工具每次独立对账）。

## 4. 安全须知

1. **密文公开 ≠ 明文公开**：加密层可被任何人下载，但没有 JWE 私钥无法解开（RFC 5652/JWE，RSA-2048）；私钥一旦泄漏，42 个私有仓的快照全部暴露——按最高等级保管（`.secrets/` 600，不落日志、不入库、不进聊天）；
2. 私钥轮换 = 全量重推（轮换前与 OWNER 确认）；
3. `pools-manifest.json` 与 `-meta` 镜像公开无害（只有公钥参数与摘要）；
4. 还原产物含完整 git 快照，还原后按原仓库的密级管理，勿再分发。

## 5. 已知限制（与 DSN 风险表对应）

| 限制 | 说明 | 状态 |
|---|---|---|
| F-19 | containerd pull 自动解密管线 payload TypeUrl 为空，`ctr images pull` 的 unpack 路径不可用 | 消费侧统一走 `pool_restore.py`（ctd-decoder 手动路径，实测双样本 PASS）；待 containerd/imgcrypt 版本对齐后可复评 |
| F-20 | user-owned 包可见性无 API，公开化需 UI（Settings→Packages→Change visibility→Public） | 待 OWNER UI 操作 |
| 超大仓 | >500MB（apollo、qtkaifajingyan）不入组镜像（D3 决策），按需单独构建 | 待需求 |

## 6. 变更记录

| 版本 | 日期 | 说明 |
|---|---|---|
| v1.0 | 2026-11-28 | 首版（A8 治理，随 image-pool-ghcr 分支交付） |
| v1.1 | 2026-11-29 | 占位符表述规范化，状态更新 |
| v1.2 | 2026-11-29 | 离线消费工作流重写（kit 套件为主线）；smoke 组 6 仓实测矩阵；public 明文还原免 key |
