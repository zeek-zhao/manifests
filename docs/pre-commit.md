# pre-commit 使用说明

本文介绍 manifests-next 仓库中 .pre-commit-config.yaml 的作用、安装方式与常见操作。

## 1. 配置文件位置

- 仓库根目录：.pre-commit-config.yaml

## 2. 当前启用的检查

- check-xml：检查 XML 语法合法性
- check-json：检查 JSON 语法合法性
- pretty-format-json：自动格式化 JSON（2 空格缩进，不排序 key）
- end-of-file-fixer：自动补齐文件末尾换行
- trailing-whitespace：清理行尾空白
- mixed-line-ending：统一换行符
- generate-manifests-check（本地 hook）：执行 python3 tools/generate_manifests.py --check

说明：generate-manifests-check 用于保证 catalogs 与 manifests/generated 的内容一致，防止提交后 CI 才发现差异。

## 3. 安装与启用

```bash
python3 -m pip install --user pre-commit
pre-commit install
```

安装后，每次 git commit 会自动触发对应 hook。

## 4. 常用命令

```bash
# 检查全部文件
pre-commit run --all-files

# 只运行单个 hook
pre-commit run generate-manifests-check --all-files

# 更新 hooks 版本
pre-commit autoupdate

# 清理本地缓存
pre-commit clean
```

## 5. 推荐开发流程

```bash
# 1) 修改 catalogs 或 tools
# 2) 生成 manifests
python3 tools/generate_manifests.py

# 3) 运行 pre-commit 全量检查
pre-commit run --all-files

# 4) 提交
git add -A
git commit -m "feat: ..."
```

## 6. 常见问题

1. pretty-format-json 修改了文件导致提交失败

- 这是正常行为，重新执行 git add -A 后再次提交。

2. generate-manifests-check 失败

- 说明已提交文件与生成结果不一致，执行：

```bash
python3 tools/generate_manifests.py
git add manifests/generated manifests/default.xml
```

3. 首次执行 hook 很慢

- pre-commit 会下载并初始化虚拟环境，首次耗时较高属正常现象。