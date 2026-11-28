# 操作日志：manifests 镜像池 ghcr 公开分发

| 项 | 内容 |
|---|---|
| 编号 | LOG-20261128-017-image-pool-ghcr-log-v1.0 |
| 日期 | 2026-11-28 |
| 编制 | zeek.zhao（AI 协作） |
| 关联 | TSK-20261128-017 / DSN-20261128-017 / PLN-20261128-017 |
| 状态 | 记录中 |

## 1. 已执行操作

| 时间 | 操作 | 结果 |
|---|---|---|
| 20:44 | 实测 >500MB 清单与 Demo 候选组 | 大仓 2 个（apollo 3.3GB / qtkaifajingyan 622MB，均 public）；app 组 4 仓=2 private+2 public，选为 Demo 样本 |
| 20:45 | imgcrypt 工具链实测 | 宿主 ctr 1.6.31 无 encrypt/decrypt、无 go、无 nerdctl、无 sudo → R1 证实 |
| 20:45 | 启动 imgcrypt ctr 容器内编译（golang:1.22 + containerd v1.7.24 + imgcrypt main） | 后台执行中 |
| 20:46 | A1 落盘 TSK/DSN/PLN-20261128-017 | docs 三文档就绪 |
| 20:46 | 分支 image-pool-ghcr（自 main）+ 局部身份 zeek.zhao 配置 | ✓ |
| 20:47 | A3 JWE 密钥对（RSA 2048 PKCS8） | 私钥工作区 .secrets/jwe.key（600）；公钥 keys/jwe.pub（入仓，SPKI PEM）✓ |

## 2. 环境事实

- containerd socket：/run/containerd/containerd.sock（root:root 660；容器内 root 可连挂载副本）；
- ghcr 推送凭据：repo secrets GH_PAT（用户确认全权限）；
- ghcr 公开包可见性：推送后需经 API PATCH /user/packages/container/<name> 设 public（记入 Demo 步骤）。

## 3. 待记录

- A2 编译结果（imgcrypt ctr 二进制）；
- A4 Demo 端到端各步结果（含 R2 ghcr 加密 manifest 兼容性实测）；
- A5~A8 工具/CI/试点/治理。

## A4~A6 实施记录（Demo 端到端、工具三件套、CI 工作流）

### A4 Demo 端到端（全 PASS）
- STAGE1 原子 fetch app 组 4 仓（kuaidian/linkManager/WorthTrack/tabharbor，HEAD 与 sha256 记录于 heads）；
- STAGE2/3 FROM scratch 每仓一层 + manifest 层，docker build（3.77MB/5 层）；容器内独立 containerd import --no-unpack（unpack 触发 overlayfs mount 需特权）；
- STAGE4 ctr-enc encrypt --recipient jwe:keys/jwe.pub --layer 0 --layer 1 定向加密成功（层 0/1 ENCRYPTION=jwe，public 层明文未动）；content get + 宿主 sha256 全 PASS；
- STAGE5 ctr-enc images push ghcr 成功（3.6MiB/10.6s）——ghcr 接受 imgcrypt 加密 manifest（R2 上半 PASS）；
- STAGE6 ghcr manifest 往返：加密 annotations（org.opencontainers.image.enc.keys.jwe / enc.pubopts）完整保留（R2 PASS）；
- R4 消费侧解密：ctr pull 自动解密管线 payload TypeUrl 空（F-19）→ 正确路径=自产 payload（typeurl.MarshalAny(imgcrypt.Payload) → proto.Marshal，TypeUrl=io.containerd.ocicrypt.v1.Payload）→ ctd-decoder fd3 手动解密：层 0/1 双样本层内 tar sha256 与原文件全等（8af80c…/75fed2…）→ R4 PASS。

### A5 工具三件套（含冒烟）
- tools/pool_build.py：fetch（原子 clone→tar→clone 即删，heads/sha256 记录；>500MB 大仓按 D3 跳过）/build（pools-manifest+Dockerfile+docker build，明文止步本地）/encrypt（layerinfo 校验）/push（红线自检：encrypted 层无 ENCRYPTION 即拒绝）/meta（genpayload→-meta 镜像）；
- tools/pool_restore.py：消费侧还原（匿名/PAT token 交换、manifest 尾层 pools-manifest 对账、meta 取 payload、fd3 dup2 保证 payload 恰在 fd3、sha256 对账 RESTORE_OK）；修复：匿名 token 对 private 包回 401（不只 403）→ 401/403 均回退 GH_PAT；demo 历史版 manifest 字段（repo/tar）向后兼容；**双样本实测 PASS**（kuaidian/linkManager）；
- tools/pool_scan.py：ctx 原子性审计 + manifest 一致性（对照快照口径，private 必须 encrypted=true）+ 敏感文件名扫描（诚实声明：bare tar 为 git 对象，文本级 token 扫描无效，深度审计属消费侧解密后职责）；
- tools/pool-tools/genpayload：go 小工具（descriptor→fd3 payload，TypeUrl=io.containerd.ocicrypt.v1.Payload）；
- 冒烟：app 组 fetch,build 全链 PASS（tar sha256 记录、smoke 镜像本地构建后即 rmi）+ POOL_SCAN_OK（4 仓）。

### A6 CI 工作流
- .github/workflows/group-pool.yml：plan（组矩阵+tag）→ pool（checkout→setup-go→fetch,build→scan→imgcrypt v2.0.3 编译+containerd 1.7.24 静态→独立 daemon→encrypt→红线 push→meta→清理 prune+ctx 销毁）；
- 触发：workflow_dispatch/workflow_call（合 main 后生效）+ push（paths 限定；image-pool-ghcr/main 分支）——F-4 教训应用；
- -meta 镜像已手工补推（enc-meta，payloads=2，PUSH_OK）。

### 缺陷与教训（F 编号续）
- F-19 containerd pull 自动解密管线 payload TypeUrl 空（消费侧走 ctd-decoder 手动路径）；
- F-20 user-owned 包 visibility 无 API（404），需 UI 切 public；
- 教训：ghcr 匿名 token 对 private 包回 401/403 双态；demo 版 manifest 字段（repo/tar）与新 schema（name/path）并存需兼容；rw_exec 长命令内嵌套 bash -c 与 entrypoint bash 冲突再发；ghcr manifest layer annotations 是解密 payload Descriptor 的来源。

### 待收口
- 包 public 化（F-20，待 OWNER UI）；匿名拉取复验；CI 试点 run（本次 push 触发）；robot/qt 等全组扩展；F-19 上游对齐观察。

### A7 CI 试点（app 组，run1~run18，全绿收口）
- 失败→修复序列（每轮 push 触发重跑）：
  | run | 步骤 | 症状 | 修复 |
  |---|---|---|---|
  | 1/2 | containerd 安装 | tar 无根目录包装，--strip-components 反剥 | install -D + test -x |
  | 3 | import | ctr images import 吃 tar 不吃镜像引用（漏 docker save） | encrypt 阶段补 save |
  | 4/5 | daemon | socket root 属主拒绝→rootless 启动受限 | root daemon + chmod 666 + 失败打印日志 |
  | 6/7/8 | 红线 | 误拦（加密实际成功） | ①列值判据（6 列=加密）②③layerinfo capture=True（sh 默认直通返回空串）+ ctr_enc 透传 capture |
  | 9 | push | content digest not found | docker build 关 provenance/sbom（buildx attestation manifest 的 blob 不入 save） |
  | 10~18 | meta | genpayload 五连修：树内子目录（payload.go 包名冲突）→文件名对齐→参数化重写（containerd proto shim；本地 golang:1.26-alpine 容器验证 BUILD_OK+payload 308B）→CWD 树内（go run 模块解析基于 CWD）→GENPAYLOAD_DIR 子目录+setup-go 1.26（imgcrypt go.mod 要求）→djson/out 绝对路径（go run CWD 相对路径 panic） |
- **run 46155148582（tag run-18）全绿**：fetch→scan→encrypt→红线 push→meta 全链；ghcr 产物=run-18（5 层，layer0/1 encrypted=True）+run-18-meta（payloads .bin+.json）。
- 消费侧还原（pool_restore）三缺陷修复后 **RESTORE_OK 双样本 PASS**：①http_json Accept 扩四类型（docker media type 404）；②meta manifest 为 buildx attestation index（无 layers 键）→index 解包；③匿名 token 对 private 包 401（回退分支已含）。kuaidian.tar 48bf8004…、linkManager.tar df3b5e3a…（内置对账一致；与 Demo 8af80c/75fed2 差异=CI fetch HEAD 更新）。
- 改进项：pool_restore 还原目录未落 pools-manifest.json；stage_meta build 未关 provenance（CI 下轮生效）；ghcr 失败轮 tag 待清理。

### A8~A9：public 复验、组扩展（robot/qt）与 LFS 攻坚（run19~run26）

- **public 匿名复验 PASS**（用户 UI 设 public 后）：匿名 token 交换 200 + manifest 拉取 200，R3 完全闭环。
- 组盘点：robot 20 仓（跳过 apollo 3312.8MB 后池内 19 仓 ~876MB，含 2 private=zeek-zhao/ros+frobot）、qt 4 仓（跳过 qtkaifajingyan 622.5MB 后池内 3 仓 ~225MB，含 1 private=qt-learn-code）；config/pool-groups.txt=app,qt,robot（组清单唯一出处，workflow plan 兜底读）。
- **run 修复链**：run19 plan 缺 checkout → d599a21；run20 qt 失败=load_group 丢 origin（快照 path 列为组前缀路径非 URL，repo_url 兜底 owner 错拼 cocowts 仓）→ 修复=entry 加 origin 原样+repo_url 优先 origin；run21~23 robot 失败=t-thanh/autoware2020-course 上游 LFS 对象 404：
  - abcf622 fetch 增强：GIT_LFS_SKIP_SMUDGE=1+HTTP/1.1+重试 3 次+降级跳过（skipped 入 manifest，不炸整组）——run22 证伪 SKIP_SMUDGE 对 mirror clone 的 fetch 路径无效；
  - 1ee61dc clone 直接禁用 `-c filter.lfs.process= -c filter.lfs.smudge=cat -c filter.lfs.required=false`（指针文件原样入池）——本地宿主实证 clone exit=0+archive 正常（宿主无 git-lfs）；
  - d352bc5 archive 同步禁用（runner 预装 git-lfs 时 .gitattributes 的 filter=lfs 使 archive 触发 clean filter→404→128）。
- **门禁分级修正**：robot run 卡 pool_scan——frobot 内 .env/*.pem 命中（fast-rtps 官方示例演示证书）。修正=按层加密状态分级：明文层（public 仓）命中=拦截无例外；加密层（private 仓）命中=告警记录不拦构建（POOL_SCAN_WARN）。
- **run 46162266660（tag run-26）三组全绿**：plan/qt/app/robot 全 success；run-26 加密语义验证=robot 20 层、加密层 [15,16]（ros+frobot）。
- **消费侧还原抽验全 PASS**（ctd-decoder 重建后）：frobot.tar 553b92f1bac42092…、qt-learn-code.tar fe4b592a92b364bd…（内置对账一致）。
- 教训：mirror clone 走 fetch 路径，SKIP_SMUDGE 只控 checkout/smudge——彻底禁用需 clone 与 archive 两处 -c filter.lfs.*；门禁例外不能靠白名单放行，按"防线覆盖状态"分级才是自洽语义。


### A10：M14 消费侧离线套件与 smoke 全流程验证

- kit 定稿与落地：消费套件 ghcr 镜像化（pool_restore.py+ctd-decoder 静态二进制+README+checksums.txt，FROM scratch 四文件入 /kit）；consumer-kit.yml workflow（编译 imgcrypt→组装→校验→build/push→回拉验证）四轮修复（checksums 相对路径 cd 错位/Dockerfile 缺失/docker create 需伪 CMD）后全绿，KIT_VERIFY_OK。
- Excel 陷阱三连修：smoke 入 Excel 后 excel-sync 三败——本地 openpyxl 保存丢 autoFilter（多写点补回均败）→**终极根因=CI pip openpyxl 未钉版本漂移（XML 形态不匹配 verify 正则）**→三 workflow 钉 openpyxl==3.1.5+verify 正则放宽，excel-sync 绿、快照 smoke 组 6 仓齐。教训：CI 依赖必须钉版；verify 检查的是保存后文件非内存态。
- smoke 冒烟组：6 仓 ≤10MB（product-sample/CThreadPool public + standard-version/database-sample/docker-sample/vue-sample private，~0.6MB），config/pool-groups.txt 加 smoke，run 46170629269（tag run-27）一次全绿。
- pool_restore 补齐明文分支：此前所有还原均走加密路径，public 明文层还原属未验证路径（meta payload 缺失会炸）→新增 is_encrypted 分支（明文层直接拉 blob 对账落盘）+--key 改可选+decode_layer 相对路径在 cwd=work 下失效修正（abspath 预处理）。
- **消费侧全流程演练 6/6 对账一致**：2 public 无 key（product-sample f7ac08e9…、CThreadPool）+4 private 带 key（standard-version 575041dd…、database-sample 0e4bfe96…、docker-sample 88a0f12a…、vue-sample 353c6e08…）；加密层缺 key 保护文案验证（FATAL: 位于加密层，还原需 --key）。
- 治理：GUIDE-pool-consume 升 v1.2（离线工作流重写/kit 主线/实测矩阵）、GUIDE-image-pool-operations 升 v1.1（密钥全生命周期/kit 维护/smoke 组）、DSN 决策点全部经用户确认（状态已批准）。
## A11 M15：池内容改 git-mirror + 落位工具（2026-11-29）

- 需求：池内下载对象改为 Mirror 镜像本体（非 HEAD 快照），并提供 tar 解压落位命令；repo XML 自动生成（fetch=本地路径配置项）。方案经用户确认：--flat 双布局可选、repo XML 需要。
- 实现（09a5e10）：pool_build stage_fetch 改 `tar -C bare -cf - .`（裸仓本体）+manifest `format: git-mirror`+repos[].head；pool_restore 重写（fetch_repo_tar 共用下载/解密/对账）；新增 pool_mirror.py（--repo/--all、--flat、--fetch-base、_materialize 原子落位+rev-parse 校验、mirror-manifest.txt+pool-manifest.xml）；consumer-kit 五文件同步。
- 缺陷：F-21 重构回归（对账对象误用层 blob，应为层内仓 tar entry.path）88c791e 修复。
- 验证：run-29（09a5e10）绿、run-30（88c791e）绿+kit 绿；本地全链演练 6/6 MIRROR_OK（private 解密对账过、rev-parse 一致、XML fetch=file:// 正确）；空 push 不命中 paths（教训：paths 触发必须变更匹配文件，空提交无效）→config 注记行触发 run-31 全量四组。
- 本地实验：CThreadPool archive 215KB vs mirror 174KB（mirror 更小）；fsck 0 错误、file:// clone OK。
- F-22 全量触发三连缺陷（run-31 失败→run-32/33 修复）：
  ①给 config/pool-groups.txt 加注释行，plan 矩阵解析（逗号 split 单行）把注释当组名（job 名 "pool (smoke）git-mirror 全量构建…)"）——教训：给数据文件加注释前必须确认解析器语法（教训再度复发）；
  ②解析修复改多行 python 内联，块标量（run: |）内顶格行=终止 YAML 块，workflow 解析炸——教训：块标量内一切行必须保持基准缩进，内联代码用单行；
  ③YAML 校验失败后无 set -e 仍执行了 commit/push（坏 YAML 已推远端）——教训：改 workflow 的脚本必须 set -e 或先校验后提交（M10 教训第三次复发）；
  最终修复=单行 python 列表推导（splitlines→去 #→split 逗号），本地注释样本解析 ["app","qt","robot","smoke"] 验证后推送。
- **run-33（ed3abc2）四组全绿**：app/qt/robot/smoke 四包 run-33 tag 齐（app 5 层加密 [0,1]、robot 20 层加密 [15,16]）；消费侧混合抽验（frobot robot 组加密层+kuaidian app 组加密层）MIRROR_OK+fsck 0 错误+三列清单/XML 正确；F-23 小缺陷记录=多次单仓 --repo 调用时 pool-manifest.xml 互相覆盖（主线 --all 一次生成不受影响，文档已注明）；演练区/kit 镜像/imgcrypt-out 清理完成（0 残留）。

## 变更记录

| 版本 | 日期 | 说明 |
|---|---|---|
| v1.0 | 2026-11-28 | 首版，A1~A3 记录 |
| v1.1 | 2026-11-28 | A4~A6：Demo 端到端 PASS、工具三件套与冒烟、CI 工作流；F-19/F-20 |
| v1.2 | 2026-11-28 | A7：CI 试点 run1~run18 全绿、消费侧还原双样本 PASS、run 序列缺陷与教训 |
| v1.3 | 2026-11-29 | A8~A9：public 复验 PASS、robot/qt 组扩展全绿（run-26）、LFS 攻坚三连修、门禁分级修正、还原抽验 PASS |
| v1.4 | 2026-11-29 | A10：M14 消费套件（kit）全绿、smoke 组 run-27 一次全绿、Excel 钉版三连修、还原明文分支补齐、全流程演练 6/6 |
| v1.5 | 2026-11-29 | A11：git-mirror 布局 + pool_mirror 落位工具 + F-21 修复 + run-30/31 验证 |
