# Author Guard Registry

Author guard 是作者明确授予的“不要自动改坏”约束。它存放在项目根目录 `.fictionops/author_guards.json`，与 reviewer 自己生成的建议分开。

## 创建或更新

```powershell
fictionops agent guard set . `
  --id G-CHAR-YEYER-KNOWLEDGE-001 `
  --kind information_boundary `
  --statement "第一次隔空拔剑前，耶儿和旁人都不能确知剑会响应牵引。" `
  --source "信息释放表/苍裁"
```

省略 `--id` 时，FictionOps 首次根据 kind、source 和 statement 生成稳定 ID。后续修改措辞时应显式复用原 ID，旧版本会进入 `history`。

## 查看

```powershell
fictionops agent guards .
fictionops agent guards . --status active --format json
```

## 退役

```powershell
fictionops agent guard retire . `
  --id G-CHAR-YEYER-KNOWLEDGE-001 `
  --reason "该信息释放节点已在新版大纲中重排。"
```

退役不会删除 guard 或历史，但它不再能授权后续 verifier withdraw。

## 权限边界

- active `G-*` author guard：可以被 verifier 引用，授权直接 withdraw；
- retired guard：只作历史证据；
- reviewer `preserve_constraints`：不具作者权限；
- 没有 active guard id 的模型撤回：自动降为 `needs_counterevidence`；
- guard 只能缩小自动修订集合，不能接受稿件、改写 canon 或替作者作最终决定。

每个 revision run 都保存 `author_guards.json` 快照并纳入 checkpoint 哈希。恢复旧 run 时使用旧快照，不会悄悄读取后来变更的 registry。
