# Counterevidence Controller Routing

`agent continue` 会读取项目级 issue ledger 中带 `counterevidence` provenance 的问题，并把机器状态转换为下一步安全动作。普通 `open` issue 不会被误识别为 counterevidence queue。

## 路由表

| Ledger 条件 | Selected action | 权限 | 是否由 `--execute` 自动执行 |
| --- | --- | --- | --- |
| 存在 grounded `open` | `prepare_counterevidence_revision` | controller / R2 | 否，只准备并展示 reviser queue |
| 无 open，存在 `evidence_blocked` | `retrieve_counterevidence` | controller / R1 | 否，需要具体来源参数 |
| 仅剩 `model_withdrawn` | `review_model_withdrawals` | author / R3 | 否，显式停在作者边界 |

既有 `ready_for_approval`、预算耗尽、失败候选、取消、canon sync 等边界优先于 counterevidence。Derived memory 若 stale，则先执行已有的 R0 `rebuild_memory`，再消费 counterevidence 状态。

当多种 counterevidence 状态并存时，优先处理可行动的 grounded open queue，其次补证，最后集中呈现模型撤回项。`agent status` 同时汇总：

- `counterevidence_reviser_queue`；
- `evidence_blocked`；
- `review_model_withdrawals`。

## 执行边界

当前版本只选择并解释下一动作，不自动调用 reviser 或猜测缺失的章节路径。`--execute` 仍只执行原有 R0 安全维护动作；R1/R2 任务需要完整命令参数，R3 必须由作者决定。

## Controlled Dogfood

真实 DeepSeek controlled application 留下 1 个 `model_withdrawn` issue。运行：

```powershell
fictionops agent continue <controlled-project> --execute --format json
```

结果：

- `selected_action=review_model_withdrawals`；
- `risk=R3`；
- `requires_human=true`；
- `executable=false`；
- `executed=false`；
- `stop_reason=human_authority_required`；
- reviser queue 为 0。

公开聚合见 [`deepseek-counterevidence-controller-v1.json`](evidence/deepseek-counterevidence-controller-v1.json)。这证明 controller 正确消费受控 ledger 状态，不代表作者已经确认该撤回。
