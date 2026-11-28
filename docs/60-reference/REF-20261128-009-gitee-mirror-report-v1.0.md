# REF-20261128-009 gitee 镜像仓识别报告（TSK-016 阶段一）

| 文档编号 | REF-20261128-009 |
| --- | --- |
| 版本 | v1.0 |
| 日期 | 2026-11-28 |
| 作者 | zeek.zhao（Agent 代笔） |
| 关联 | TSK-20261128-016 |
| 状态 | **已执行（v1.1 追加 §9）** |

## 1. 方法与证据等级

对 manifests.xlsx 全部 **28 个 gitee 平台行**逐一探测：

- **A 级（铁证）**：`git ls-remote` 对比 gitee 仓与 GitHub 候选仓 HEAD commit sha，**完全一致**（gitee 导入镜像保留提交历史）→ 确证同一项目；
- **B 级（强）**：GitHub 同名仓（同 owner 或作者官方 org）+ 描述一致，sha 不等（两平台更新滞后属常态）；
- **C 级（疑似）**：名称有差异/owner 不同/sha 不等，默认不替换，列岀供人工确认；
- 候选来源：同 owner 试探 → 已知官方 org 映射 → GitHub Search API（按 stars 排序）逐一 ls-remote 验证。

## 2. 判定结果汇总

| 分类 | 数量 |
| --- | --- |
| A 级铁证镜像（建议替换） | 12 |
| B 级同名镜像（滞后，建议替换） | 4 |
| C 级疑似（待人工确认，默认不动） | 3 |
| D 级非镜像/不替换 | 9 |

## 3. A 级铁证镜像（12 个，建议替换）

| # | 表格行 | gitee 仓库 | GitHub 原版 | 星数 | 判定依据（双方 HEAD sha） |
| --- | --- | --- | --- | --- | --- |
| 1 | 行5 | Embedfire/embed_linux_tutorial | **Embedfire/embed_linux_tutorial** | 388 | c4ba386356 = c4ba386356 |
| 2 | 行10 | weidongshan/lv_100ask_modules | **100askTeam/lv_100ask_modules** | 0 | 537e7a907c = 537e7a907c（百问网官方 GitHub org） |
| 3 | 行14 | weidongshan/DBoS-Desktop | **cocowts/DBoS-Desktop** | 20 | 4d1a325f24 = 4d1a325f24 |
| 4 | 行17 | weidongshan/awesome-raspberrypipico | **100askTeam/awesome-raspberrypipico** | 0 | 46975e704f = 46975e704f |
| 5 | 行19 | ApolloAuto/apollo | **ApolloAuto/apollo** | 26918 | d53aa3da47 = d53aa3da47（百度 Apollo 官方 GitHub 为原版，gitee 为官方镜像） |
| 6 | 行20 | zhengqingya/docker-compose | **zhengqingya/docker-compose** | 179 | 95a152ee02 = 95a152ee02 |
| 7 | 行22 | junvary/gin-quasar-admin | **Junvary/gin-quasar-admin** | 264 | 79c5bf3724 = 79c5bf3724（GitHub org 名大小写 Junvary） |
| 8 | 行25 | pengxiaotian/datav-vue | **pengxiaotian/datav-vue** | 763 | dcb2b8d4c3 = dcb2b8d4c3 |
| 9 | 行28 | xuliangzhan_admin/vxe-table 见 B-16 | — | — | — |
| 10 | 行70 | fatezrl/cmake-examples | **ttroy50/cmake-examples** | 13076 | 2b27fc75c4 = 2b27fc75c4（cmake-examples 原版） |
| 11 | 行21 | mirrorvim/vim-fast | **chenxuan520/vim-fast** | 103 | c5c216a5ba = c5c216a5ba（gitee mirrorvim 为镜像组织名） |
| 12 | 行11 | weharmony/kernel_liteos_a_note | **kuangyufei/kernel_liteos_a_note** | 427 | 6f7efdc37c = 6f7efdc37c（鸿蒙内核注释，作者 kuangyufei） |
| 13 | 行26 | vdpadmin/variant-form | **vform666/variant-form** | 1988 | 24e62c360b = 24e62c360b（Variant Form 官方 org vform666） |

（注：#9 占位勘误，vxe-table 在 B 级表；A 级实际 12 个 = 上表去掉 #9 行。）

## 4. B 级同名镜像（4 个，sha 滞后但同项目无疑）

| # | 表格行 | gitee 仓库 | GitHub 原版 | 星数 | 判定依据 |
| --- | --- | --- | --- | --- | --- |
| 14 | 行15 | feiyangqingyun/QWidgetDemo | **feiyangqingyun/QWidgetDemo** | 6954 | 同 owner 同名同描述；g_sha 0d3d3c0907 ≠ gh c8f2478c44（平台更新滞后） |
| 15 | 行16 | feiyangqingyun/qtkaifajingyan | **feiyangqingyun/qtkaifajingyan** | 4680 | 同上；a80d533a5e ≠ 1d9c5ccf99 |
| 16 | 行28 | xuliangzhan_admin/vxe-table | **x-extends/vxe-table** | 8633 | 作者本人 GitHub 官方 org（x-extends）；gitee 为作者同步镜像；f5364279b2—sha 3c179f941b（版本线差异） |
| 17 | 行24 | crudapi/crudapi-admin-web | **crudapi/crudapi-admin-web** | 209 | 同 owner 同名同项目；7e84c04f50 ≠ d66004f814 |

## 5. C 级疑似（默认不替换，待人工确认）

| # | 表格行 | gitee 仓库 | 疑似 GitHub 原版 | 疑点 |
| --- | --- | --- | --- | --- |
| C1 | 行4 | weidongshan/imx6ull_NoosProgramProject | 100askTeam/100ask_imx6ull_NoosProgramProject（12★） | 仓库名有 100ask 前缀差异；sha 28f6721811 ≠ bd607452ea |
| C2 | 行6 | weidongshan/stm32mp157-m4 | 100askTeam/STM32MP157-M4_Examples（4★） | 仓库名差异较大；sha d50d10f582 ≠ 7f7f535671 |
| C3 | 行23 | was666/as-editor | qq9068149/AS-Editor（267★） | owner 不同、sha 351d0b157f ≠ f83b272d5a；名称大小写差异 |

## 6. D 级：判定为非镜像或不宜替换（9 个，维持 gitee）

| 表格行 | gitee 仓库 | 不替换理由 |
| --- | --- | --- |
| 行3 | weidongshan/esp32_100ask_project | 百问网 gitee 主发；GitHub 100askTeam 无此仓（ls-remote not found） |
| 行7 | xiebaoyou/linux-2.6.12 | 自建内核注释仓；GitHub 2.6.11.12 注释仓为不同项目（sha 不等） |
| 行8 | AllOpenOS/linux0.11_note | 社区 gitee 官方；**且该 gitee 仓匿名访问要求认证（疑似私有）**，另见 §8 风险 |
| 行9 | weidongshan/Buildroot | 百问网定制 fork（含 100ask 补丁），上游 buildroot/buildroot 非其"原版"——替换会丢失定制 |
| 行13 | weidongshan/qemu | 同上，百问网 qemu 定制 fork（上游 qemu/qemu） |
| 行18 | weidongshan/pico-micropython | 百问网改版（raspberrypi/pico-micropython-examples 为官方示例仓，非镜像关系，sha 不等） |
| 行12 | openatom-university/openharmony-oer | 开放原子官方 gitee 主发，GitHub 无对应 org 仓 |
| 行27 | MTrun/vue-big-screen-plugin | GitHub MTrun 无同名/近似仓（not found），作者主发 gitee |
| 行107 | zeek-zhao/alpu | **自有仓**（excel-sync 管），不存在"原版托管"问题 |

## 7. 建议替换方案（A+B 共 16 行，待确认）

1. **行级变更**：`platform` gitee→github；`name` 改 GitHub 原版全名（含大小写修正：Junvary/gin-quasar-admin、vform666/variant-form、x-extends/vxe-table、cocowts/DBoS-Desktop、chenxuan520/vim-fast、kuangyufei/kernel_liteos_a_note、ttroy50/cmake-examples）；`path` **保持不变**（检出路径不动，本地工作区零迁移）；`branch` 按 GitHub default_branch 刷新（如 gin-quasar-admin main）；`仓库属性/仓库大小(MB)/language/description` 随 GitHub API 刷新；`groups` 不动。
2. **remote 影响**：project 的 remote 由 `gitee_https` 变 `github_https`（生成器自动，无手工 remote 编辑）；`by-platform/gitee.xml` 28→12 行、`github.xml` 89→105 行；与既有 github 行**无重名冲突**（已核验 16 个原版名均不在现有 89 行内，不产生双行）。
3. **统计联动**：平台分布公式（COUNTIF platform）自动跟随；动态统计 sheet 行 platform 列同步改 github；REF-008 的 gitee size 缺失口径变为 github 有 size。
4. **验证**：迁移脚本 `--dry-run` 先行 → normalize → generate → `--excel --check` → zip 断言 → 9 钩子 → PR → CI → --no-ff 合并（ls-remote 核验后删分支）→ LOG-016。

## 8. 风险与说明

- **B 级滞后**：替换后本地检出以 GitHub 版为准，gitee 上可能领先/落后的提交不再可见（各仓均为活跃上游 GitHub 侧，风险低）。
- **C 级若后续确认**：按同一流程补替换（单独小 PR）。
- **私有仓**：AllOpenOS/linux0.11_note 匿名不可读，建议用户人工确认该行可见性；其余 27 行 gitee 匿名可拉取。
- 替换不删除任何行；检出路径不变，已有本地 `repo sync` 目录无需重建。

## 9. 执行记录（v1.1 追加）

- **用户决策**（对话确认）：「abc 同意 was666/as-editor 删除 不需要了」→ A(12)+B(4)+C(2，imx6ull_NoosProgramProject→100askTeam/100ask_imx6ull_NoosProgramProject、stm32mp157-m4→100askTeam/STM32MP157-M4_Examples) 共 **18 行替换**；**was666/as-editor 行删除**（C3 其余两项仍执行替换）。
- **执行结果**（迁移脚本一次通过，0 错误）：replaced=18/18、deleted=1/1；branch/仓库属性/仓库大小(MB)/language/description 均按 GitHub API 刷新（gin-quasar-admin/datav-vue/vxe-table branch=main，其余 master）；path/groups/topic/知识列未动。
- **产物核验**：normalize OK（129 repositories, 4 platforms, owners=[zeek-zhao]）；by-platform 行数 gitee 28→**9**、github 90→**108**（obsidian 双 path 行在内）、gitlab 8、yoctoproject 4；`--excel --check` exit 0；catalog.md 272 行（--check 过）；合计行 SUM(O3:O131)；动态统计 107/108 github 仓有指标（orgflow-devops1 上游已删常态 404）；pre-commit 9 钩子全绿。
- 语言新增 slug：vue×3、vim-script×1（by-language 维度自动扩充，与 TSK-010 #7 单例保留策略一致）。
