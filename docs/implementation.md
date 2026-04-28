# manifests-next 实现文档

## 实现范围

本次实现覆盖以下内容：

1. 新建独立工程 `manifests-next`
2. 迁移并重构原有 manifest 生成逻辑
3. 支持多个 catalog 文件
4. 支持可选 `linkfile` 配置
5. 增加格式校验和测试
6. 提供使用说明与迁移说明
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

优先选择公开仓库，如 GitHub 或 Gitee 公共项目，验证 `generated/by-protocol/https.xml`。

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
