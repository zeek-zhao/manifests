# 最小示例清单

本工程提供两份面向 `repo init` 的最小示例清单，目标是降低首次使用成本，方便单仓快速拉取和对外说明。

## 文件位置

- `manifests/examples/quickstart-https.xml`
- `manifests/examples/quickstart-zeek-zhao.xml`

这两份文件都只包含一个 `<project>`，并且仍然复用统一的 `manifests/_remotes.xml` 和 `manifests/_hooks.xml`。

## 示例一：公共仓库 HTTPS 拉取

适用场景：首次体验、无需 SSH 密钥、对外演示。

```bash
tmpdir=$(mktemp -d)
cd "$tmpdir"
repo init -u file:///home/zeek/work/.repo/manifests-next -b master -m manifests/examples/quickstart-https.xml
repo sync -c -j1 code/cpp/bazel_examples
```

当前示例仓库：`bazelbuild/examples.git`

## 示例二：zeek-zhao SSH 拉取

适用场景：验证 owner 默认走 SSH、内部协作说明。

```bash
tmpdir=$(mktemp -d)
cd "$tmpdir"
repo init -u file:///home/zeek/work/.repo/manifests-next -b master -m manifests/examples/quickstart-zeek-zhao.xml
repo sync -c -j1 sample/docker-sample
```

当前示例仓库：`zeek-zhao/docker-sample.git`

## 维护约定

- 示例清单由 `tools/generate_manifests.py` 生成，不手工修改。
- 示例仓库应尽量满足“单仓可直接拉取、依赖少、说明成本低”。
- 如果示例仓库变更，应同步更新本文件中的命令和仓库说明。