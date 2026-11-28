# manifests 实现文档

## 实现范围

本次实现覆盖以下内容：

1. 新建独立工程 `manifests`
2. 迁移并重构原有 manifest 生成逻辑
3. 支持多个 catalog 文件
4. 支持可选 `linkfile` 配置
5. 增加格式校验和测试
6. 提供使用说明与关键字文档
7. 验证单仓拉取和协议行为

## 实施步骤

### 1. 初始化工程结构

- 建立 `catalogs/`、`docs/`、`tools/`、`manifests/` 目录
- 增加 `README.md`、`.gitignore`、`.pre-commit-config.yaml`

### 2. 迁移配置模型

- 将旧工程中的 `catalog/repositories.json` 拆分为多个 catalog
- 至少提供 `cpp.json` 和 `zeek-zhao.json`
- 生成器增加多文件加载与合并逻辑

### 3. 重构生成器

- 输入目录改为 `catalogs/*.json`
- 输出目录改为 `manifests/`
- 增加 `linkfiles` 渲染逻辑
- 保留 `_remotes.xml`、`default.xml` 和各分类 manifest 的生成能力

### 4. 完善测试

- 多 catalog 合并测试
- owner 协议覆盖测试
- `linkfile` 渲染测试
- 默认入口包含各分类索引测试

### 5. 验证工程

- `python3 -m unittest`
- `python3 tools/generate_manifests.py --check`
- `pre-commit run --all-files`
- 使用 `repo init` + `repo sync` 测试单仓拉取

## 交付物

- 独立新仓库
- 可运行的 manifest 生成脚本
- 多 catalog 示例配置
- 设计与实现文档
- 协议验证记录

## 验证策略

### HTTPS 验证

优先选择公开仓库，如 GitHub 或 Gitee 公共项目，验证 `generated/by-platform/github.xml`（公开仓）。

### SSH 验证

优先选择当前机器已配置访问权限的 `zeek-zhao` 仓库，验证 `generated/by-owner/zeek-zhao.xml`。

### 单仓验证

优先使用只包含一个 `project` 条目的 manifest 文件，以缩短同步时间并降低失败面。

## 提交策略

提交分为三类：

1. 工程骨架与文档
2. 生成器与测试
3. 生成结果与验证记录

如果验证通过，则在新仓库中完成一次或多次清晰提交。

## Excel 化改造（2026-11-28，TSK-20261128-004）

依据 `docs/DSN-20261128-001-excel-manifest-design.md`（v0.5 定稿）完成：

- `generate_manifests.py`：新增 `--excel` 数据源（读 `catalogs/manifests.xlsx`）、`--xlsx` 覆盖路径、`--export-json` 快照导出、Excel 规则校验（name/path/platform/protocol/slug 冲突等）、remotes 代理规则（`use_proxy_https`）、quickstart 改由 config 表驱动。
- `validate_manifests_xlsx.py`（新增）：结构校验 / 规范化（冻结首行、列宽、下拉）/ 快照导出。
- `sync_self_repos.py`（新增）：GitHub API 同步自有仓库（branch/platform/description/visibility 刷新、protocol 清空、path 补齐、上游消失标注、新仓库追加、知识列永不覆盖），支持 `--dry-run`。
- `catalog_to_markdown.py`：数据源改为 Excel，`docs/catalog.md` 随之重生成。
- `.github/workflows/excel-validate.yml` / `excel-sync.yml`（新增人工流转链路）；`.pre-commit-config.yaml` 增加 Excel 校验钩子；`tools/enrich_catalog.py` 退役删除（D6）。
- 验收：`--excel` 与过渡期 JSON 两种数据源的生成产物逐字节一致；`sync_self_repos.py --dry-run` 实测动作与设计预期一致。
