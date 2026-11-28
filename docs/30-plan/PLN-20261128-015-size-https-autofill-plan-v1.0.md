# PLN-20261128-015 全量大小与协议移除落地计划

| 文档编号 | PLN-20261128-015 |
| --- | --- |
| 版本 | v1.0 |
| 日期 | 2026-11-28 |
| 作者 | zeek.zhao（Agent 代笔） |
| 关联 | TSK-20261128-015 |
| 状态 | 已完成 |

## 里程碑

- **M1 代码改造**：generate（列清单删 protocol、load 校验删、remote 全 https、quickstart 改 zeek-zhao_https、快照列删）；sync（protocol 引用删、合计哨兵+插入合计前）；validate（表头 17 列、enum 删 protocol、_tight_widths 分级、_rebuild_stats 列字母动态、汇总行重建+哨兵跳过、DV 动态列）；markdown（DETAIL_COLUMNS 删 protocol）；新增 tools/autofill_repos.py；workflow excel-autofill.yml。
- **M2 迁移与重生成**：迁移脚本（delete_cols(5) 删协议→仓库属性列移 col5→汇总行写入→github 空大小补抓）；stats→normalize→generate→catalog.md→快照。
- **M3 验证**：zip 断言（17 列表头/E 列仓库属性 DV/无协议 DV/合计行公式/AF/列宽抽查）；--excel --check/validate/catalog --check；9 钩子。
- **M4 交付**：TSK/PLN/LOG-015 + GUIDE（17 列表、合计行、autofill 工作流说明）+ REF-008（大小可得性矩阵）→ PR → CI → --no-ff 合并（ls-remote 核验）→ LOG 补录 → 汇报。

## 风险与对策

- R1 删列后统计公式列位漂移 → D-5 动态列字母一次到位
- R2 汇总行被当作数据仓（generate/sync/markdown 行数 132）→ 哨兵 name=="合计" 四工具统一跳过，--check 兜底
- R3 6 行原 git 协议仓切 https 后 remote 定义变化 → 快照/维度 XML 全量重生成，diff 审查确认 remote={platform}_https
- R4 仓库属性列移动后旧 DV/样式残留 → normalize 全量重建 DV+样式（既有机制）
