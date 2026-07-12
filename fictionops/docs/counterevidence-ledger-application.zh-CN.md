# Counterevidence Ledger Application

`agent counterevidence apply` 把 grounded escalated re-verification 的 effective verdict 写入持久 issue ledger。它应用的是**问题状态**，不是小说修改。

```powershell
fictionops agent counterevidence apply escalated-reverification.json `
  --packet counterevidence.packet.json `
  --escalation evidence-escalation.json `
  --run-dir path/to/original-revision-run `
  --format json
```

## 状态映射

| Effective verdict | Ledger status | Reviser 行为 |
| --- | --- | --- |
| `uphold` | `open` | 写入 `counterevidence_reviser_queue.json`，可进入后续 reviser |
| `withdraw` | `model_withdrawn` | 保留审计历史，不进入 reviser，不冒充作者拒绝 |
| `still_insufficient` | `evidence_blocked` | 保持补证边界，不进入 reviser |

`model_withdrawn` 和 `evidence_blocked` 是机器状态，不是作者决定。作者仍可通过现有 `agent issue` 生命周期重新打开、waive 或 reject。

## 权限与一致性

- `accepted/rejected/waived` 属于已存在的作者权限，模型结果不得覆盖；
- `addressed/verified` 属于已有候选修订结果，counterevidence apply 不自动重开；
- `uphold/withdraw` 必须通过 exact-quotation grounding；
- report 中的 packet/escalation SHA-256 必须与实际文件一致，apply 会用两者重新计算 grounding；
- 原章节 SHA-256 必须与 revision run 的 `source_manifest.json` 一致；
- 每个 run 只能应用一次，重复调用被拒绝；
- `--dry-run` 计算全部动作但不写 ledger、queue 或 application receipt；
- 正文始终只读。

每条 issue 的 `counterevidence_history` 保存 report hash、request/sample ids、model/effective verdict、grounded evidence、reason 和时间。Application receipt 同时更新 run-local `issues.before.json` 和项目级 `.fictionops/issues.json`，使状态能够跨 session 延续。

## Controlled Dogfood

上一阶段真实 DeepSeek re-verifier 在取得完整章节后撤回“氛围段是填充”的 finding。将该 grounded report 应用到受控 revision run 后：

- issue 状态由默认 `open` 变为 `model_withdrawn`；
- reviser queue 为 0；
- application receipt、ledger history 和 report/packet/source hashes 全部写入；
- 章节 SHA-256 应用前后均为 `2e9381e6c24d78c6f0fc0a7d6b3287481e814f292449b0157625ba710fe530ae`；
- `manuscript_edited=false`。

公开 application 结果见 [`deepseek-counterevidence-application-v1.json`](evidence/deepseek-counterevidence-application-v1.json)。这是受控状态闭环证据，不是对《江山》真实章节 ledger 的修改。

这些状态如何被 `agent continue` 消费，见 [`counterevidence-controller-routing.zh-CN.md`](counterevidence-controller-routing.zh-CN.md)。
