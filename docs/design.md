# manifests 设计文档

## 目标

`manifests` 是一个独立的 manifest 生成工程，用于替代旧的手工维护方式。它需要满足以下目标：

1. 支持从多个仓库配置文件生成 repo manifests。
2. 支持按协议、平台、语言、主题、owner 等维度输出分类清单。
3. 将 `zeek-zhao` 仓库默认配置为 SSH 协议，确保 pull 和 push 一致走 SSH。
4. 支持可选 `linkfile` 配置；未配置时不生成相关 XML。
5. 提供清晰的设计文档、实现文档、使用说明和格式校验。

## 设计原则

### 单一事实来源

所有仓库定义都来自 `catalogs/*.json`。生成器会先加载并合并多个 catalog，再渲染为目标 XML 文件。

### 工程与产物分离

- 源配置位于 `catalogs/`
- 生成脚本位于 `tools/`
- 生成产物位于 `manifests/`
- 文档位于 `docs/`

这样可以明确区分输入、逻辑和输出，降低维护成本。

### 分类可扩展

分类维度不写死为单一文件，而是根据 catalog 中出现的值自动生成。例如新增 `rust`、`java`、`coding` 平台时，不需要额外加模板文件。

### 协议策略统一

协议分为两类：

- `https`
- `git`（实际走 SSH）

生成 `_remotes.xml` 时为每个平台都产出对应 remote。`git` remote 会写入 `fetch` 和 `pushurl`。

### 向后兼容 repo 用法

根入口 `manifests/default.xml` 继续作为默认入口，同时输出协议、平台、语言、owner 等子清单，便于单独初始化。

## 目录设计

```text
manifests/
├── catalogs/
│   ├── cpp.json
│   ├── zeek-zhao.json
│   └── ...
├── docs/
│   ├── design.md
│   └── implementation.md
├── manifests/
│   ├── _hooks.xml
│   ├── _remotes.xml
│   ├── default.xml
│   └── generated/
├── tools/
│   ├── generate_manifests.py
│   ├── extract_repositories.py
│   └── tests/
├── .pre-commit-config.yaml
└── README.md
```

## 数据模型

每个 catalog 文件由以下结构组成：

```json
{
  "remotes": {},
  "owners": {},
  "repositories": []
}
```

其中：

- `remotes` 可选，用于补充或覆盖平台 remote 定义。
- `owners` 可选，用于设置 owner 级别策略，如默认协议、附加 groups。
- `repositories` 必填，用于定义仓库。

单个仓库条目支持如下关键字段：

- `name`
- `path`
- `branch`
- `topic`
- `platform`
- `language`
- `groups`
- `preferred_protocol`（可选）
- `linkfiles`（可选）

`linkfiles` 结构如下：

```json
"linkfiles": [
  {
    "src": ".",
    "dest": "sample/cpp-sample/docker"
  }
]
```

## 关键流程

### 生成流程

1. 读取 `catalogs/*.json`
2. 按顺序合并 `remotes`、`owners` 和 `repositories`
3. 计算每个仓库的协议、remote、groups
4. 渲染 `_remotes.xml`
5. 渲染分类清单
6. 渲染 `default.xml`

### 校验流程

1. `generate_manifests.py --check` 校验生成结果是否与磁盘一致
2. `pre-commit` 负责 XML/JSON/行尾格式校验
3. 单元测试校验 remote 选择、多 catalog 合并、linkfile 输出

## 风险与约束

### 旧仓库不直接覆盖

工程目录可自定义，对外发布名称统一为 `manifests`。

### 协议测试依赖本机环境

`https` 协议可优先验证公开仓库；`git` 协议依赖当前机器已配置 SSH key。如果某些私有仓库没有访问权限，则只能验证公开或当前有权限的仓库。

### repo init 测试依赖本地 bare 仓库或 file URL

为了避免影响线上远端仓库，优先使用本地仓库路径或 `file://` 方式验证生成结果。
