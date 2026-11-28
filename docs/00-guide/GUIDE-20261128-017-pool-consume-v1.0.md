# GUIDE-20261128-017-pool-consume-v1.0

| 文档属性 | 内容 |
|---|---|
| 编号 | GUIDE-20261128-017-pool-consume-v1.0 |
| 版本 | v1.0（2026-11-28） |
| 编制 / 审核 | AI Agent (zeek.zhao) / 待用户审核 |
| 状态 | 生效中 |
| 适用 | manifests 组镜像池消费侧（DSN-20261128-017-v1.0） |

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
| JWE 私钥 | 与构建公钥（仓库 `keys/jwe.pub`）配对的私钥，本机存放 `.secrets/jwe.key`（600） |
| Python 3.10+ | 仅标准库 |
| token（可选） | 镜像公开后匿名可拉；若镜像仍为 private，导出 `GH_PAT` |

## 3. 还原命令

### 3.1 还原 private 仓库（加密层）

```bash
python3 tools/pool_restore.py \
  --image ghcr.io/zeek-zhao/manifests-pool-app:enc \
  --meta  ghcr.io/zeek-zhao/manifests-pool-app:enc-meta \
  --repo kuaidian \
  --key ~/.secrets/jwe.key \
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
