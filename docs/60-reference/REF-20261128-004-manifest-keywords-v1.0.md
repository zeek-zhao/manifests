## manifests 关键字指南

- `revision`
  指定项目的修订版本。可以是具体 commit，也可以是分支名。
  - 如果是 commit，`repo sync` 会检出到固定提交。
  - 如果是分支，`repo sync` 会跟随分支最新提交。

- `upstream`
  指定项目上游分支。
  - 当 `revision` 是分支名时，`upstream` 通常不生效。
  - 当 `revision` 固定为 commit 时，可用于标记该 commit 所属分支。

- `dest-branch`
  指定代码上传（例如 `repo upload`）时的目标分支。

- `path`
  指定项目在本地工作区中的目录。
  - 未指定时默认与 `name` 一致。
  - 必须唯一，且不能包含 `..`，不建议以 `/` 开头。

- `name`
  项目标识，通常是 `owner/repo.git`。

- `remote`
  绑定到已定义的 `<remote>` 名称。
  - `fetch` 决定拉取地址基准。
  - `pushurl` 可单独指定推送地址。

- `groups`
  项目分组（逗号分隔）。
  - 可用 `repo sync -g <group>` 只同步指定分组。
  - 支持排除写法，例如 `app,-tests`。

- `sync-c`
  仅抓取 manifest 当前分支所需引用，减少网络与磁盘占用。

- `sync-s`
  控制是否同步子模块。

- `sync-tags`
  控制是否同步 tags。

- `force-sync`
  强制同步并重置本地状态到远端，可能覆盖本地未提交变更。

- `clone-depth`
  浅克隆深度（例如 `1`），可减少下载量。

- `copyfile`
  同步后从项目中复制单文件到工作区指定位置。

- `linkfile`
  同步后创建符号链接或等价映射。
  - 在 `manifests` 工程中，`linkfile` 为可选字段，不配置则不生成对应节点。

- `annotation`
  为项目附加键值元数据。
  - `keep="false"` 时，`repo manifest -r` 导出可剥离该注释。

- `extend-project`
  在不重复定义项目主体的前提下，扩展或覆盖局部属性。

- `remove-project`
  从上游 include 的 manifest 中移除指定项目。

- `include`
  引入外部 manifest 片段，适合分层组织和复用。

- `default`
  定义全局默认属性（如 `remote`、`revision`、`dest-branch`、`sync-j`）。

- `sync-j`
  在 `<default>` 中设置默认并发同步线程数。

### 常用查看与调试

- `repo manifest -r`：查看当前锁定后的 manifest。
- `repo diffmanifests old.xml new.xml`：比较两份 manifest 的项目差异。
- `repo list -f`：查看项目与本地路径映射关系。
