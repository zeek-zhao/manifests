# PLN-20261128-006 落地计划

对应 TSK-20261128-006。执行顺序（用户 m00761 已授权）：

| # | 步骤 | 操作 | 验证 |
| --- | --- | --- | --- |
| 0 | 本任务书+计划推 main | git commit + push | CI 绿 |
| 1 | T1 分支清理 | `gh api -X DELETE repos/zeek-zhao/manifests/git/refs/heads/<branch>` ×2 + 本地 `git branch -D` | `git ls-remote` 无残留 |
| 2 | T2 sync 实跑 | `gh workflow run excel-sync.yml --ref main` → `gh run watch` | run 绿；main 出现 regenerate 提交；Excel 含 11 新行 |
| 3 | T3 知识列补全 | pull main → 建 `feat/excel-fill-11` → /tmp 填充脚本（读回 API description + 推断填充）→ `--excel` 重生成 + snapshot 导出 → pre-commit → 提交推分支 → PR | 11 行知识列无空值；`--check` 一致；CI 绿 |
| 4 | LOG-20261128-006 记录全程 → main 直推；合并 T3 PR（同合规合并方式） | — | main CI 绿；工作区干净 |

回滚：任何一步失败即停，保留现场报告用户；分支删除可 restore，main 提交可 revert。
