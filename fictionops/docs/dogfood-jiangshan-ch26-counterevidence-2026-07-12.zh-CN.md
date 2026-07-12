# 《江山》第一本第26章 Counterevidence Dry-run

本轮使用当前第26章正文的逐字副本，SHA-256 为 `3c2cff24708ccf9d0ba2d760615dcf6ed2801682915c13824289a8b0cb7225b4`。所有模型输出与 ledger 均位于 `~/.fictionops/evidence/jiangshan-ch26-counterevidence-v1`；真实小说正文没有写入。

## 目标

只处理作者此前明确指出的“不是”过多问题，不混入旧 v4 候选同时处理的冷系词和“忽然”。Finding 最终收窄为两处：

- `不是因为凶。`
- `不是怕脏。是怕这东西真的已经成了自己手的一部分。`

必要辨认、人物对话和其他节奏性否定全部进入 preserve boundary。

## 真实轨迹

1. 第一次全章 re-verification 试图把35处“不是”全部解释为仁孜的防御性认知，并给出 `withdraw/high`。模型引用带文件名前缀的统计说明，无法逐字落到正文，controller 将其降为 `still_insufficient`。
2. 补入作者已有决定，并把断言收窄到两处精确引文。第二次 re-verification 返回 grounded `uphold/high`。
3. 最小 reviser 只改两处，但生成“他宁愿对方凶一点。凶一点反而好。”。独立 verifier 自报通过，新增的确定性句界重复门禁将其降为 `needs_revision_attention`。
4. 整章重试多次回到同一局部答案，暴露 full-chapter regeneration 的成本与 no-progress 风险。旧 candidate/execution 随后改为编号归档。
5. 局部修复器只返回一个唯一替换，将相关句子改为“他宁愿对方凶一点。凶反而好对付。”；其输出仅98 token。
6. 最终独立验证通过：两条 candidate evidence 逐字落地，无无关修改、无新增正史、author guard 保留、局部回归为空，change ratio 为 `0.002753`。
7. `agent continue --execute` 停在作者权限的 `review_counterevidence_candidate`；`accept-revision --dry-run` 通过，但没有写入沙箱原章或真实正文，也没有生成 acceptance 文件。

## 工程结论

本次共11次真实模型调用，约13.6万 total token。成本主要来自整章 reviser 与 verifier，而最终局部 repair 只需5691输入、98输出。对长篇 agent，更有效的失败恢复不是不断重新生成全章，而是：

- 先把含混审美问题收窄成可逐字验证的局部断言；
- 模型 verdict 必须受 grounding 与确定性回归门禁约束；
- contracted fix 已完成时，降阶为唯一锚定 patch；
- 对 byte-identical retry 明确停止，不允许廉价 API 造成无限空转。

公开聚合见 [`deepseek-jiangshan-ch26-counterevidence-v1.json`](evidence/deepseek-jiangshan-ch26-counterevidence-v1.json)。

## 成本优化重放

实现 deterministic-first 与 delta-only verifier 后，对同一最终候选再次调用同一 DeepSeek 模型：

- 输入 token：`12351 -> 1861`，下降 `84.93%`；
- 输出 token：`444 -> 266`；
- prompt 字符数：`4694`；
- verdict 仍为 grounded `ready_for_approval`；
- dry-run、沙箱 source 和真实第26章哈希仍全部不变。

对于含新增句界重复的失败候选，新版本在 API 调用前即返回 `deterministic_preflight/model_call_count=0`。因此原轨迹中多次让 verifier 阅读整章的成本，不会在同类后续运行中重现。

## 补证窗口优化重放

原 escalated re-verifier 同时发送 packet 中的全章和 escalation 中的全章，同一正文发生重复。Evidence-window compiler 上线后，这条 finding 因具有两处精确引文、active author guard 和“只改两处”的保留边界，被编译为 `bounded_claim_windows`：

- 模型可见证据：`13205 -> 387` 字符，下降 `97.07%`；
- 输入 token：`11313 -> 1757`，下降 `84.47%`；
- prompt 字符数：`4443`；
- verdict 仍为 grounded `uphold/high`，模型调用数为1；
- grounding 只使用模型实际见过的窗口，真实第26章仍未写入。

一般性的章级功能、全章节奏或长线回声判断不会套用该局部策略，而是进入 `full_scope_deduplicated`，保留一份完整章节并去掉重复副本。
