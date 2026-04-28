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

## .pre-commit-config.yaml 使用方法

当前仓库使用 pre-commit 保证 JSON、XML 和生成结果一致性。配置文件是 .pre-commit-config.yaml，包含以下类型检查：

- pre-commit-hooks：check-xml、check-json、行尾与空白规范
- pretty-format-json：统一 JSON 格式（2 空格，保持原 key 顺序）
- 本地钩子 generate-manifests-check：执行 python3 tools/generate_manifests.py --check

首次安装与启用：

```bash
python3 -m pip install --user pre-commit
pre-commit install
```

常用命令：

```bash
# 手动检查全部文件
pre-commit run --all-files

# 只执行某一个 hook
pre-commit run generate-manifests-check --all-files

# 更新 hook 版本后回写 .pre-commit-config.yaml
pre-commit autoupdate
```

当 JSON 被自动格式化后，重新 git add 再提交即可。

## 常用初始化命令

```bash
# owner 维度：zeek-zhao（默认走 SSH）
repo init -u git@github.com:zeek-zhao/manifests.git -b main -m manifests/generated/by-owner/zeek-zhao.xml
repo init -u git@github.com:zeek-zhao/manifests.git -b main -m manifests/generated/by-owner/zeek-zhao.xml -g gitee,sample

# 协议维度：仅 HTTPS
repo init -u git@github.com:zeek-zhao/manifests.git -b main -m manifests/generated/by-protocol/https.xml

# 平台维度：仅 github
repo init -u git@github.com:zeek-zhao/manifests.git -b main -m manifests/generated/by-platform/github.xml

# 最小示例：单仓快速拉取
repo init -u git@github.com:zeek-zhao/manifests.git -b main -m manifests/examples/quickstart-zeek-zhao.xml
```

## repo 环境设置

Linux 环境推荐先安装 repo，再配置镜像与 Git 全局设置。

```bash
# 下载并安装 repo 工具
curl https://mirrors.tuna.tsinghua.edu.cn/git/git-repo -o repo
sudo mv repo /usr/local/bin/repo
sudo chmod +x /usr/local/bin/repo

# 可选：设置 repo 镜像源（国内网络建议）
echo 'export REPO_URL=https://mirrors.tuna.tsinghua.edu.cn/git/git-repo' >> ~/.bashrc
source ~/.bashrc

# 初始化 repo 配置（会写入用户名邮箱）
repo init --config-name
```

建议的 Git 全局配置：

```bash
git config --global pull.rebase true
git config --global fetch.prune true
```

## 配置 Git 凭证管理

如果你使用 HTTPS 拉取仓库，建议配置凭证管理，避免频繁输入用户名密码。

基础方案（跨平台简单可用）：

```bash
git config --global credential.helper store
```

Ubuntu 安全方案（libsecret）：

```bash
sudo apt-get update
sudo apt-get install -y libsecret-1-0 libsecret-1-dev
cd /usr/share/doc/git/contrib/credential/libsecret
sudo make
git config --global credential.helper /usr/share/doc/git/contrib/credential/libsecret/git-credential-libsecret
```

也可以使用 netrc：

```bash
touch ~/.netrc
chmod 600 ~/.netrc
cat >> ~/.netrc <<'EOF'
machine gitee.com
login your-username
password your-token-or-password
EOF
```

长期推荐使用 SSH 免密：

```bash
ssh-keygen -t ed25519 -C "your-email@example.com"
cat ~/.ssh/id_ed25519.pub
```

将公钥添加到对应 Git 平台后，可直接使用 git@... 地址初始化。

## repo 常用命令

```bash
# 并行同步
repo sync -j30
repo sync -j$(nproc)

# 仅同步当前 manifest 分支，减少下载量
repo sync -c -j30

# 查看项目与路径
repo list -f

# 导出锁定版本清单
repo manifest -r -o locked.xml

# 比较两份清单
repo diffmanifests old.xml new.xml

# 同步失败时强制覆盖本地 .repo/project-objects
repo sync --force-sync

# 保存当前代码状态，生成带有日期的清单文件
repo manifest -o $(date +%Y-%m-%d)_default.xml -r

# 移除清单中的 upstream 属性（可选）
sed -i s/' upstream="[^"]*"'//g $(date +%Y-%m-%d)_default.xml

# 使用本地清单文件
repo init -u file://$(pwd)/default.xml
```

## 常见问题

1) repo: command not found

- 确认 repo 在 PATH 中：which repo
- 如果在 /usr/local/bin/repo，确认 shell 环境加载了该路径

2) HTTPS 拉取反复要求输入密码

- 检查 git credential.helper 是否已配置
- gitee/github 建议使用 Token，不建议长期使用账号密码
- 检查 ~/.netrc 权限是否为 600

3) repo sync 报权限或认证错误

- SSH 模式：确认公钥已上传平台，ssh -T git@github.com 或 ssh -T git@gitee.com 验证
- HTTPS 模式：清理旧凭证后重试

```bash
git credential-cache exit
rm -f ~/.git-credentials
```

4) 本地 manifest 与 catalogs 不一致

- 重新生成并检查：

```bash
python3 tools/generate_manifests.py
python3 tools/generate_manifests.py --check
```

5) pre-commit 卡在某个 hook

- 单独运行该 hook 查看详情：pre-commit run <hook-id> --all-files
- 执行 pre-commit clean 后重试

## 参考文档

- `docs/quickstart.md`
- `docs/manifest-keywords.md`
- `docs/design.md`
- `docs/implementation.md`
- `docs/pre-commit.md`
- [Git Repo - Google](https://gerrit.googlesource.com/git-repo/)
- [Repo 清单格式文档](https://gerrit.googlesource.com/git-repo/+/HEAD/docs/manifest-format.md)
- [Android 官方 Repo 命令参考资料](https://source.android.com/source/using-repo?hl=zh-cn)
