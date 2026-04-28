# manifests-next

`manifests-next` 是新的 repo manifest 生成工程。它使用多个 catalog 文件作为输入，统一生成 `repo init` 可直接使用的 XML 清单。

## 核心能力

- 支持多个 catalog 文件输入
- 支持按协议、平台、语言、主题、owner 分类生成 manifests
- `zeek-zhao` 默认使用 SSH 协议
- 支持可选 `linkfile` 配置
- 支持 `pre-commit` 格式校验

## 目录说明

- `catalogs/`：多个仓库配置文件输入目录
- `manifests/`：生成后的 repo manifests
- `tools/`：生成、拆分和抽取脚本
- `docs/`：设计、实现、迁移和关键字说明文档

## 常用命令

```bash
cd /home/zeek/work/.repo/manifests-next
python3 tools/generate_manifests.py
python3 tools/generate_manifests.py --check
pre-commit run --all-files
```

## 最小示例清单

新工程额外提供两份面向 `repo init` 的最小示例清单，适合单仓快速拉取和对外说明：

- `manifests/examples/quickstart-https.xml`：公共仓库、HTTPS 协议
- `manifests/examples/quickstart-zeek-zhao.xml`：`zeek-zhao` 仓库、SSH 协议

示例命令：

```bash
tmpdir=$(mktemp -d)
cd "$tmpdir"
repo init -u file:///home/zeek/work/.repo/manifests-next -b master -m manifests/examples/quickstart-https.xml
repo sync -c -j1 code/c++/bazel_examples
```

```bash
tmpdir=$(mktemp -d)
cd "$tmpdir"
repo init -u file:///home/zeek/work/.repo/manifests-next -b master -m manifests/examples/quickstart-zeek-zhao.xml
repo sync -c -j1 sample/docker-sample
```

## 从旧工程迁移

```bash
cd /home/zeek/work/.repo/manifests-next
python3 tools/split_legacy_catalog.py
python3 tools/generate_manifests.py
```

详细设计见 `docs/design.md`，实现说明见 `docs/implementation.md`，快速上手见 `docs/quickstart.md`，迁移说明见 `docs/migration.md`。
