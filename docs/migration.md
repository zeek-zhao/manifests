# 迁移说明

## 迁移来源

新工程来源于旧目录 `/home/zeek/work/.repo/manifests`，迁移内容包括：

- manifest 生成逻辑
- manifest 分类与协议策略
- 格式校验配置
- 使用说明和关键字说明

## 本次迁移的主要变化

### 单文件配置改为多 catalog

旧工程使用单个 `catalog/repositories.json`。新工程改为 `catalogs/*.json`，便于按 owner、主题或用途拆分维护。

当前初始化拆分如下：

- `catalogs/cpp.json`
- `catalogs/zeek-zhao.json`
- `catalogs/community.json`

### 输出目录独立

旧工程直接在仓库根目录输出。新工程统一输出到 `manifests/` 下：

- `manifests/_remotes.xml`
- `manifests/_hooks.xml`
- `manifests/default.xml`
- `manifests/generated/**`

### 新增 linkfile 支持

生成器现在原生支持 `linkfiles` 字段。未配置时不输出；配置后会生成对应 `<linkfile />` 节点。

### 新增拆分脚本

`tools/split_legacy_catalog.py` 用于将旧的单文件配置拆分到新工程的多个 catalog。

## 推荐迁移流程

1. 在旧工程更新仓库配置。
2. 运行新工程的拆分脚本生成 `catalogs/*.json`。
3. 运行新工程的生成器输出新 manifests。
4. 使用 `pre-commit` 和 `repo init` 做验证。
