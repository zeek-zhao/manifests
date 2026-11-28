# GUIDE-20261129-001-image-pool-operations-v1.2

| 文档属性 | 内容 |
|---|---|
| 编号 | GUIDE-20261129-001-image-pool-operations-v1.2 |
| 版本 | v1.2（git-mirror 布局与 pool_mirror 落位工具，M15）原 v1.1（2026-11-29）：密钥全生命周期章节、消费套件（kit）构建维护、smoke 冒烟组 |
| 编制 / 审核 | AI Agent (zeek.zhao) / 待用户审核 |
| 状态 | 生效中 |
| 适用 | manifests 仓库组镜像池全流程（使用者 / 管理者操作手册；分支 image-pool-ghcr） |
| 关联 | DSN-20261128-017（方案）、GUIDE-20261128-017-pool-consume（消费侧速查）、DSN-20261129-001（LFS 规划，暂缓实施） |


## 0-. 密钥全生命周期（管理者视角，逐步命令与预期）

| 环节 | 命令 / 操作 | 预期结果 |
|---|---|---|
| 生成 | `openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -out /home/jenkins/zeek_work/.secrets/jwe.key && openssl pkey -in .secrets/jwe.key -pubout -out keys/jwe.pub` | 私钥 PKCS8（600）；公钥 SPKI（可公开入库） |
| 存放 | 私钥仅存工作区 `.secrets/`（权限 600）；提交前 `git status` 确认 `.secrets` 不在跟踪 | `ls -l .secrets/jwe.key` = `-rw-------` |
| 公钥入库 | `git add keys/jwe.pub && git commit -m "feat(pool): JWE 公钥入册" && git push` | CI 加密只读仓库内公钥，私钥永不进 CI/secret |
| 分发 | 带外渠道（加密压缩+另通道告知口令）交授权消费者；台账记录分发对象/日期 | 消费者 `.secrets/jwe.key`（600）与公钥配对可用（对账一致即验证） |
| 验证配对 | 消费者对任意 private 仓跑还原（consume 手册步骤 5） | `RESTORE_OK … sha256 … 对账一致` |
| 轮换 | ①生成新对（新文件名 jwe-v2.key/jwe-v2.pub）②公钥替换入库+推 CI 重建组镜像（新 tag 层用新钥）③新旧私钥并存窗口：旧 tag 用旧钥解、新 tag 用新钥解④通知消费者换钥⑤旧私钥冷存归档后销毁 | 新 tag 解密用新钥通过；旧钥从工作区移除（`.secrets/jwe.key.old` 归档或删除） |
| 泄漏处置 | 视同全量重推：立即轮换（上一步骤）+评估泄漏窗口内被下载的镜像，必要时组镜像下架（ghcr 包 settings） | 新私钥仅新分发名单持有 |

注意：轮换=新 tag 全量重推（旧 tag 仍绑旧公钥 annotations），不改动已发布 tag。

## 0--. 消费套件（kit）构建与维护

- workflow：`.github/workflows/consumer-kit.yml`（push 到自身/pool_restore.py 触发；dispatch 可手动）。
- 产物：`ghcr.io/zeek-zhao/manifests-pool-kit:latest`（pool_restore.py+ctd-decoder 静态二进制+README+checksums.txt；构建后回拉校验 KIT_VERIFY_OK）。
- 更新语义：`tools/pool_restore.py` 每次变更合入即自动重建 latest；消费者 `docker pull` 新 latest 即升级（checksums 变化属预期）。
- 冒烟组 `smoke`（6 仓 ≤10MB，2 public+4 private）专为消费链路演练而设：`config/pool-groups.txt` 含 smoke，每次改动还原工具后建议跑一轮全流程（consume 手册 §0.1）。

## 0. 体系总览

**一句话**：`manifests` 仓库（Excel 清单=事实源）驱动 GitHub Actions（`group-pool.yml`）把仓库按 topic 组打包成公开 OCI 镜像推到 ghcr.io；public 仓库层明文、private 仓库层 JWE 加密；持私钥者在本地一键解密还原。

**参与方与职责**：

| 角色 | 职责 | 需要手动做的事 |
|---|---|---|
| OWNER（管理者） | 清单裁决、密钥持有与分发、触发策略 | 改 Excel 清单、分发私钥、（可选）手动触发、包公开化 UI |
| CI（GitHub Actions） | 拉取/打包/加密/红线校验/推送/对账/清理 | —— 全自动，无需操作 |
| 使用者 | 拉取镜像、解密还原 | 准备 ctd-decoder 与私钥，跑还原命令 |

**两仓联动（详见场景 G）**：`manifests` 仓库决定"打什么"，`ghcr.io/zeek-zhao/manifests-pool-<组>` 承载"打好的包"；两者以 `pools-manifest.json`（随镜像分发）对账。

**当前状态（2026-11-29）**：试点三组 `app`（4 仓）/ `qt`（3 仓）/ `robot`（19 仓）全绿，最新产物 tag `run-26`；>500MB 大仓（apollo、qtkaifajingyan）按决策不入组池；LFS 内容暂以指针语义入池（规划见 DSN-20261129-001）。

## 1. 场景 A：修改仓库清单（manifests 层面怎么改）

### A1 修改既有仓库属性（如 public→private）

1. **【手动】** 编辑 `catalogs/manifests.xlsx` 主表，改目标行的「仓库属性」列（`public`/`private`）。
2. **【自动】** 推送到 `main` 后，`excel-sync` 工作流自动重建快照 `catalogs/manifests-excel-snapshot.json` 并校验（无需手动跑工具）。
   - 预期：snapshot 中该仓 `仓库属性` 与 Excel 一致；Action 全绿。
3. **【手动】** 属性变更影响加密判定：`private`→`public` 的仓库，其已推送的加密层**不会自动解密**（保守策略，防误判泄漏）；如确认需要明文化，按场景 B 以新 tag 重跑一次组构建，并人工核对该层在 ghcr manifest 中无 `enc.keys.jwe` annotation。

> 红线：**不要手改快照 JSON**（工具产物，手改会在下次 sync 被覆盖且校验报错）；Excel 的知识列（purpose/contents 等）永不自动填写。

### A2 新增仓库入池

1. **【手动】** Excel 主表加行：`name`（owner/repo.git）、`path`（组前缀路径）、**「仓库属性」列必填**（加密判定依据）、`groups` 列标所属组（如 `app`）。
2. **【自动】** 同 A1 步骤 2。
3. **【手动】** 若组名是新的，见 A3。

### A3 新增组（扩池）

1. **【手动】** 编辑 `config/pool-groups.txt`（组清单唯一出处，逗号分隔），如追加 `,devops`。
2. **【手动】** 推送 `image-pool-ghcr` 分支——该文件在 CI 触发 paths 内，推送即自动构建新组（见场景 B）。
   - 预期：Actions 出现矩阵 job `pool (devops)`；ghcr 出现 `manifests-pool-devops:run-<N>` 与 `-meta` 两个 tag。

### A4 清单校验（可选）

```bash
python3 tools/validate_manifests_xlsx --check   # 【自动随 excel-sync 执行；手动跑用于本地预检】
```
预期：输出校验通过（0 error）。

## 2. 场景 B：触发仓库同步（从修改到 CI 运行）

同步=重跑 `group-pool.yml`。三种触发方式：

| 方式 | 触发条件 | 谁操作 |
|---|---|---|
| push 自动 | 推送改动命中 paths：`group-pool.yml`、`config/pool-groups.txt`、`tools/pool_*.py`、`keys/jwe.pub` | 【自动】改完推送即触发 |
| workflow_dispatch | workflow 已在默认分支（main）注册后可用：`gh workflow run group-pool.yml --ref main -f groups=app,qt -f tag=my-tag` | 【手动】 |
| workflow_call | 被其他工作流调用 | 【自动/编排】 |

### B1 标准触发流程

```bash
# 1.（手动）清单或组配置改动后推送（改的是触发 paths 内文件则自动构建）
git push origin image-pool-ghcr

# 2.（自动）CI 执行：plan（读组清单出矩阵）→ pool(matrix)：
#    原子 fetch（clone→tar→clone 即删）→ build（每仓一层 FROM scratch）→ pool_scan 门禁
#    → ctr-enc JWE 定向加密 private 层 → 红线自检（未加密 private 层拒绝推送）
#    → push ghcr → -meta payload 镜像 → 构建机清理 prune

# 3.（手动）跟踪
gh run watch   # 或网页 Actions 页
# 预期：plan 与全部 pool (组) job 均 success

# 4.（手动）确认产物
# 预期：ghcr.io/zeek-zhao/manifests-pool-<组>:run-<N> 与 :run-<N>-meta 两个新 tag
```

### B2 失败处理

1. 看失败 job 的失败步骤名（fetch/build/scan/encrypt/push/meta）。
2. `manifest.skipped` 非空=有仓库 fetch 失败被降级跳过（LFS 404/网络），组镜像仍产出，跳过仓清单随镜像分发——**是否接受由 OWNER 裁决**，可修复后重跑。
3. 历史缺陷对照 `docs/40-log/LOG-20261128-017-*`（run1~26 全序列与修复均留档）。

## 3. 场景 C：产物下载与解密还原（消费侧）

### C1 前提准备（一次性）

| 项 | 获取方式 |
|---|---|
| ctd-decoder | 向管理员索取，或自行编译：`git clone -b v2.0.3 https://github.com/containerd/imgcrypt && docker run --rm -v $PWD:/src -e GOPROXY=https://goproxy.cn,direct -w /src golang:1.26-alpine sh -c "cd cmd && go build -o /out/ctd-decoder ./ctd-decoder"`（需还原 private 层才需要） |
| JWE 私钥 | 管理员离线分发（场景 D），存 `.secrets/`（权限 600） |
| Python 3.10+ | 仅标准库 |
| GH_PAT（可选） | 包已公开，匿名可拉；仅排障时需要 |

### C2 还原 private 仓库（加密层）

```bash
python3 tools/pool_restore.py \
  --image ghcr.io/zeek-zhao/manifests-pool-robot:run-26 \
  --meta  ghcr.io/zeek-zhao/manifests-pool-robot:run-26-meta \
  --repo frobot \
  --key .secrets/jwe-pool.key \
  --decoder ./ctd-decoder \
  --out restore/
# 预期输出：token: pat（或 anonymous）→ RESTORE_OK frobot -> restore/pools/robot/frobot.tar（sha256 … 对账一致）
#          manifest -> restore/pools-manifest.json
```

### C3 取 public 仓库（明文层）

```bash
docker pull ghcr.io/zeek-zhao/manifests-pool-app:run-26
docker create --name t ghcr.io/zeek-zhao/manifests-pool-app:run-26
docker cp t:pools/app/WorthTrack.tar .
docker rm t
# 预期：得到 git 快照 tar；或直接用 C2 命令（明文层工具同样对账）
```

### C4 批量还原

对 `pools-manifest.json` 的 `repos[]` 循环 C2（`--repo` 换名）；工具每仓独立对账。

### C5 对账说明

- `pools-manifest.json`（随镜像分发）：`repos[]` 含 name/layer_index/encrypted/**sha256**/head，顶层含 lfs_policy/**skipped**；
- `pool_restore.py` 自动比对「解密层内 tar 的 sha256 == manifest.sha256」，输出"对账一致"即为完整可信；
- 进一步核对 git 版本：解包后 `git -C <解包目录> rev-parse HEAD` 应等于 manifest 的 `head`。

## 4. 场景 D：密钥管理

### D1 生成（一次性，已完成）

```bash
openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -out .secrets/jwe-pool.key     # PKCS#8 私钥
openssl pkey -in .secrets/jwe-pool.key -pubout -out keys/jwe.pub                            # SPKI 公钥
chmod 600 .secrets/jwe-pool.key
```
当前密钥对已生成并在用：公钥入库 `keys/jwe.pub`，私钥仅存本机 `.secrets/`。

### D2 存放

| 密钥 | 存放位置 | 谁持有 |
|---|---|---|
| JWE 公钥 | 仓库 `keys/jwe.pub`（公开无妨） | 所有人 |
| JWE 私钥 | `.secrets/`（600），**不入库、不进日志/聊天/CI** | OWNER 与获授权使用者 |
| GH_PAT | GitHub 仓库 **Secrets**（`MIRROR_SCAN_TOKEN` 同源管理；绝不可放 Variables——public 仓库 Variables 任何人可读） | GitHub 平台 |

### D3 分发（=授权）

- 私钥只走**离线通道**（当面/加密文件传输），收到方自检 `openssl pkey -in jwe.key -noout && chmod 600 jwe.key`；
- 分发即授权：给谁私钥，谁就能还原全部 42 个 private 仓快照——按人授权，登记在案。

### D4 轮换（私钥疑似泄漏或定期）

1. **【手动】** 按新 D1 生成新密钥对；新公钥替换 `keys/jwe.pub` 提交（push 会自动触发全组重建）。
2. **【自动】** CI 用新公钥重新加密推送，新 tag 即新密钥产物。
3. **【手动】** 通知全部持有者换发新私钥；旧镜像 tag（旧密钥加密）删除；旧私钥销毁记 LOG。
- 成本提示：轮换=全量重推（三组约数分钟）+全部持有者换钥；无泄漏场景建议年度轮换。

### D5 泄漏应急

立即执行 D4，并：确认泄漏范围（谁/多久）→ LOG 记录 → 评估是否需要审计还原产物扩散面。

## 5. 场景 E：加密解密方案详述

| 项 | 内容 |
|---|---|
| 加密对象 | **镜像内的 private 仓库层**（粒度=每仓一层；判定依据=快照「仓库属性」列） |
| 技术体系 | OCI 镜像层加密（containerd imgcrypt v2.0.3 / ocicrypt） |
| 算法 | 信封加密：内容层 AES-256-GCM/CTR，层密钥经 **JWE（RSA-OAEP-256，RSA-2048）** 封装给公钥持有者；加密层 mediaType 带 `+encrypted` 后缀，密钥参数存于层 annotation `org.opencontainers.image.enc.keys.jwe` |
| 工具 | 加密 `ctr-enc images encrypt --layer <n> --recipient jwe:keys/jwe.pub`；解密 `ctd-decoder`（payload 走 fd3，由 `tools/pool-tools/genpayload-ci` 生成） |
| 密钥来源 | 构建 CI **只用公钥**（私钥永不上 CI）；消费侧用管理员分发的私钥 |
| 红线 | private 层未加密即拒绝推送（CI 红线自检）；明文 ctx 不出构建机；clone 即删 |

**解密全流程（pool_restore.py 已封装）**：
① 拉镜像 manifest → ② 按 `pools-manifest.json` 找目标仓层 → ③ 拉 `-meta` 镜像取该层解密 payload（.bin）→ ④ `ctd-decoder --decryption-keys-path <私钥目录>` 解出层 tar → ⑤ sha256 对账后落盘。

> 已知限制 F-19：containerd `ctr images pull` 的自动解密路径当前有 payload 兼容缺陷，统一走上述 ctd-decoder 手动路径（实测全部样本 PASS）。

## 6. 场景 F：手动操作 vs 自动化清单

| 环节 | 谁做 | 操作 |
|---|---|---|
| 修改仓库清单/属性 | **手动** | Excel 改后推 main（A1/A2） |
| 快照重建与校验 | 自动 | excel-sync 工作流 |
| 新增组 | **手动** | 改 `config/pool-groups.txt` 推送（A3） |
| 触发组构建 | 自动为主 | push 命中 paths 即跑；手动 dispatch 可选（合 main 后） |
| fetch/打包/加密/红线/推送/meta/对账/清理 | **自动** | group-pool.yml 全链（含失败降级跳过与 skipped 留痕） |
| 产物下载与解密 | **手动** | 场景 C 命令 |
| 包公开化（首次） | **手动** | GitHub UI：Packages→对应包→Change visibility→Public（user 包无 API，F-20；已执行完毕） |
| 私钥生成/分发/轮换 | **手动** | 场景 D |
| 密钥进入 CI | 自动 | 公钥随仓库走；CI 无需私钥 |

## 7. 场景 G：两仓联动机制（manifests ↔ ghcr）

**关联链**：`catalogs/manifests.xlsx`（事实源）→excel-sync→`catalogs/manifests-excel-snapshot.json`（机器可读清单，含仓库属性/groups）→`config/pool-groups.txt`（选组）→`group-pool.yml` run→**ghcr 包** `manifests-pool-<组>:run-<N>`（tag 即版本，只增不改；回滚=拉旧 tag）。

**同步语义**：每次 run 对该组**全量重建**（取各仓当次 HEAD 快照），非增量；清单变更在下次 run 生效。

**对账三查**（任一不符即差异，按场景 B2 处理）：
1. **加密对账**：ghcr manifest 各层 annotation（`enc.keys.jwe`）↔ `pools-manifest.json repos[].encrypted`——CI 的 pool_scan 门禁每次 run 强制（不一致直接构建失败）；
2. **内容对账**：层内 tar sha256 ↔ manifest `repos[].sha256`——消费侧 `pool_restore.py` 每次还原自动执行；
3. **覆盖对账**：组内仓清单 ↔ snapshot `groups` 列 + `skipped` 列表——镜像随附 manifest 可见"哪些仓在池里、哪些被跳过及原因"。

## 8. 故障排查

| 现象 | 原因 | 处置 |
|---|---|---|
| pool_restore 报 401 | 包仍为 private（匿名） | 导出 GH_PAT 或请 OWNER UI 公开化 |
| 红线步骤失败 | private 层加密校验未过 | 属保护性拦截，查 encrypt 步骤日志，勿绕过 |
| fetch 步骤出现"降级跳过" | 上游 LFS 404/网络断流 | 接受（skipped 留痕）或修复上游后重跑 |
| archive 128 | LFS clean filter（已在 CI 修复） | 确认工具版本含 `-c filter.lfs.*` bypass |
| 解密报 payload 错误 | F-19，勿用 `ctr pull` 解密路径 | 统一 pool_restore.py |

## 9. 附录：命令速查与当前状态

```bash
# 触发（合 main 后）：gh workflow run group-pool.yml --ref main -f groups=app -f tag=
# 还原 private：见 C2；取明文：见 C3；对账：pool_restore 自动输出
# 密钥轮换：见 D4
```

当前产物：`run-26`（app/qt/robot）与 `run-31（全量四组后更新至最新 tag；布局自 run-31 起为 git-mirror）`（smoke 冒烟组 6 仓）+ 各组 `-meta`；app 包 public 匿名可拉，其余包待 OWNER UI 公开化（F-20）；扩展组/LFS 内容池规划见 DSN-20261129-001。

## 池内容布局（git-mirror，M15 起）

- 池内 tar = git mirror 裸仓本体（pools-manifest `format: "git-mirror"`，repos[] 含 `head` 字段）；
- 消费侧 `pool_mirror.py`（随 consumer-kit 分发）直接落位裸仓并生成 `mirror-manifest.txt` / `pool-manifest.xml`（`--fetch-base` 自定义 remote fetch）；
- D3 大仓（>500MB）仍不入池，另行按需构建；
- 旧 HEAD 快照布局（run-30 及之前）由 pool_restore 还原为 tar 后手工 `git init` 导入，仍兼容。

## 6. 变更记录

| 版本 | 日期 | 说明 |
|---|---|---|
| v1.0 | 2026-11-29 | 首版：A~G 全场景操作手册（清单/触发/还原/密钥/加密解密/联动对账） |
| v1.1 | 2026-11-29 | 密钥全生命周期（生成/存放/分发/轮换/泄漏处置）；kit 构建维护；smoke 冒烟组 |
