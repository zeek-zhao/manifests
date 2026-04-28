## Manifest 关键字指南

- `revision`
  指定项目修订版本，可以是 commit 或分支。

- `upstream`
  当 `revision` 固定为 commit 时，可用于标记该 commit 所属上游分支。

- `dest-branch`
  指定上传或后续协作时的目标分支。

- `path`
  指定项目在本地工作区的目录，必须唯一。

- `name`
  仓库唯一标识，通常是 `owner/repo.git`。

- `remote`
  绑定到 `_remotes.xml` 中定义的 `<remote>`。

- `groups`
  为 repo 分组过滤提供基础；可以配合 `repo sync -g` 使用。

- `copyfile`
  同步后从项目内复制文件到工作区指定位置。

- `linkfile`
  同步后创建链接或等价文件映射。`manifests-next` 中该字段是可选配置，不填则不会生成对应 XML。

- `include`
  引入其他 manifest 片段，适合做分层组织。

- `default`
  为 manifest 设定默认 `remote`、`revision` 或并发参数。

- `remote`
  常见属性包括 `name`、`fetch`、`pushurl`、`review`。

### 调试建议

- 使用 `repo manifest -r` 查看锁定后的 manifest。
- 使用 `repo diffmanifests old.xml new.xml` 比较 manifest 差异。
- 使用 `repo list -f` 校验 manifest 中的路径与实际工作区是否一致。
