# PLN-20261128-011 复查与修复落地计划

| 文档编号 | PLN-20261128-011 |
| --- | --- |
| 版本 | v1.0 |
| 日期 | 2026-11-28 |
| 作者 | zeek.zhao（Agent 代笔） |
| 关联 | TSK-20261128-011 |
| 状态 | 已完成 |

## 里程碑

- **M1 复查诊断**（只读）：解包 xlsx 验 DV XML；交叉核对 default.xml/维度文件/catalog.md；alpu 与 orgflow-devops1 行现状；sync 删行能力确认。产出 R1–R8 清单 → 用户确认「全部修复」。
- **M2 修复实施**：
  - validate：DV 范围 `{letter}1:{letter}1000`（两处）+ `_refresh_readme`（README_ROWS）；
  - sync：倒序遍历 + 上游消失删行 + docstring/GONE_NOTE 清理；
  - 数据：临时脚本删 orgflow-devops1 行 + orgflow-devops relations 修正。
- **M3 重生成与验证**：normalize → stats_report（带 GH_TOKEN）→ generate --excel → catalog.md → 快照导出 → XML 验 sqref/图表数/行数 → 双 --check。
- **M4 文档与交付**：TSK/PLN/LOG-011 + GUIDE/REF-003 更新 → 9 钩子 → PR → CI → 本地 --no-ff 合并 → 分支删 → LOG 补录。

## 风险与对策

- R1 删行影响统计公式：统计 sheet 全部使用整列引用（$A:$A/$N:$N），行删除不影响 ✓
- R2 同名双行（obsidian）误删：倒序+seen_before（序号更小同名首行）语义保持 ✓
- R3 GitHub API 限流：stats_report/sync 均要求 GH_TOKEN/GITHUB_TOKEN；匿名调用 60/h 不足 90 仓拉取（执行中实际踩坑一次，见 LOG-011 §3）
- R4 normalize 与动态统计 sheet 冲突：normalize 四表循环不含该 sheet；实测 4 图表保留 ✓
