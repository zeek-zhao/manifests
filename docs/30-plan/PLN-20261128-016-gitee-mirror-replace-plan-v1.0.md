# PLN-20261128-016 gitee 镜像替换落地计划

| 文档编号 | PLN-20261128-016 |
| --- | --- |
| 版本 | v1.0 |
| 日期 | 2026-11-28 |
| 作者 | zeek.zhao（Agent 代笔） |
| 关联 | TSK-20261128-016 / REF-20261128-009 |
| 状态 | 已完成 |

## 用户决策（m02066）

「abc 同意 was666/as-editor 删除 不需要了」→ A（12）+B（4）+C（2，排除 as-editor）共 **18 行替换**；**was666/as-editor 行删除**。

## 替换映射（18）

| gitee 旧名 | GitHub 新名 | 等级 |
| --- | --- | --- |
| Embedfire/embed_linux_tutorial | Embedfire/embed_linux_tutorial | A |
| weidongshan/lv_100ask_modules | 100askTeam/lv_100ask_modules | A |
| weidongshan/DBoS-Desktop | cocowts/DBoS-Desktop | A |
| weidongshan/awesome-raspberrypipico | 100askTeam/awesome-raspberrypipico | A |
| ApolloAuto/apollo | ApolloAuto/apollo | A |
| zhengqingya/docker-compose | zhengqingya/docker-compose | A |
| junvary/gin-quasar-admin | Junvary/gin-quasar-admin | A |
| pengxiaotian/datav-vue | pengxiaotian/datav-vue | A |
| fatezrl/cmake-examples | ttroy50/cmake-examples | A |
| mirrorvim/vim-fast | chenxuan520/vim-fast | A |
| weharmony/kernel_liteos_a_note | kuangyufei/kernel_liteos_a_note | A |
| vdpadmin/variant-form | vform666/variant-form | A |
| feiyangqingyun/QWidgetDemo | feiyangqingyun/QWidgetDemo | B |
| feiyangqingyun/qtkaifajingyan | feiyangqingyun/qtkaifajingyan | B |
| xuliangzhan_admin/vxe-table | x-extends/vxe-table | B |
| crudapi/crudapi-admin-web | crudapi/crudapi-admin-web | B |
| weidongshan/imx6ull_NoosProgramProject | 100askTeam/100ask_imx6ull_NoosProgramProject | C |
| weidongshan/stm32mp157-m4 | 100askTeam/STM32MP157-M4_Examples | C |

删除：was666/as-editor（1 行）。

## 里程碑

- **M1 迁移**：/tmp/tsk016_replace.py（按 gitee 旧名定位；platform→github、name 改名、branch/仓库属性/仓库大小(MB)/language/description 按 GitHub API 刷新，path/groups/topic/知识列不动；删除 as-editor 行；幂等）→ stats_report（GH_TOKEN）→ normalize → generate → catalog.md → 快照。
- **M2 验证**：by-platform 行数（gitee 9 / github 107）、`--excel --check`、validate、zip 断言、平台分布公式、9 钩子。
- **M3 交付**：REF-009 补执行状态与用户决策、REF-008 gitee 行数口径更新（28→9）、LOG-016 → PR → CI → --no-ff 合并（ls-remote 核验）→ LOG 补录 → 汇报。

## 风险与对策

- R1 改名后 name 与快照/catatlog 唯一键漂移 → 迁移脚本一次完成且 generate --check 兜底
- R2 C 级仓 default_branch 未知 → API 读取后写入（STM32MP157-M4_Examples 等）
- R3 删行使后续行号上移 → 迁移自底向上删行（只删 1 行且在校验前）
