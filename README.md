# manifests

`manifests` 是多仓库 repo manifest 管理工程。它基于多个 catalog 文件生成标准 XML 清单，支持按协议、平台、语言、主题和 owner 维度拆分使用。

## 快速使用

```bash
repo init -u git@github.com:zeek-zhao/manifests.git -b main -m manifests/generated/by-owner/zeek-zhao.xml
repo sync -j30
```

## 目录说明

- `catalogs/`：仓库配置数据源，支持多个 JSON 文件
- `manifests/`：生成后的清单目录
- `manifests/generated/`：按维度拆分的清单
- `manifests/examples/`：面向 `repo init` 的最小示例清单
- `tools/`：生成和拆分脚本
- `docs/`：设计、实现、快速上手和关键字文档

## 生成与校验

```bash
cd /path/to/manifests
python3 tools/generate_manifests.py
python3 tools/generate_manifests.py --check
pre-commit run --all-files
```

## 常用初始化命令

```bash
# owner 维度：zeek-zhao（默认走 SSH）
repo init -u git@github.com:zeek-zhao/manifests.git -b main -m manifests/generated/by-owner/zeek-zhao.xml

# 协议维度：仅 HTTPS
repo init -u git@github.com:zeek-zhao/manifests.git -b main -m manifests/generated/by-protocol/https.xml

# 平台维度：仅 github
repo init -u git@github.com:zeek-zhao/manifests.git -b main -m manifests/generated/by-platform/github.xml

# 最小示例：单仓快速拉取
repo init -u git@github.com:zeek-zhao/manifests.git -b main -m manifests/examples/quickstart-zeek-zhao.xml
```

## repo 常用命令

```bash
# 并行同步
repo sync -j30

# 仅同步当前 manifest 分支，减少下载量
repo sync -c -j30

# 查看项目与路径
repo list -f

# 导出锁定版本清单
repo manifest -r -o locked.xml

# 比较两份清单
repo diffmanifests old.xml new.xml
```

## repo 设置建议

```bash
# 凭证缓存
git config --global credential.helper store

# 推荐启用 rebase 同步策略
repo init --config-name
git config --global pull.rebase true
```

## 参考文档

- `docs/quickstart.md`
- `docs/manifest-keywords.md`
- `docs/design.md`
- `docs/implementation.md`
