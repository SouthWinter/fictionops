# FictionOps Memory-first Agent v1

## 定位

Memory-first Agent v1 不修改模型权重。它把长期记忆、作者偏好、章节状态、验证和采纳证据保存在模型外部，每次调用只检索当前任务需要的材料。

## 持久文件

```text
.fictionops/memory/index.json              可重建的分段检索索引
.fictionops/memory/preferences.jsonl        作者明确确认的偏好
.fictionops/memory/acceptance_events.jsonl  已采纳候选的事实记录
.fictionops/memory/stale.json               索引需要重建的标记
```

`index.json` 是缓存，不是正史。Markdown 正史、人物弧线、大纲、已采纳正文和写作指导仍是权威来源。

## 基本命令

```bash
fictionops agent-memory build my-novel
fictionops agent-memory query my-novel --query "鹿煜 当前知识边界"
fictionops agent-memory add-preference my-novel \
  --rule "旁白不要替人物完成成熟理论" \
  --prefer "让物件与行为承担认识变化" \
  --avoid "人物直接总结主题" \
  --scope character_growth \
  --evidence "作者确认的章节修订"
fictionops agent-memory status my-novel
```

偏好必须带作者证据。模型建议、一次偶然改写或未采纳候选不能自动进入长期偏好。

## 写章调用链

`agent-write-workflow` 默认执行：

```text
typed memory retrieval
  -> causal simulator
  -> chapter planner + scene state contract + story fact ledger
  -> full-chapter writer or optional state-aware scene writers
  -> deterministic story audit
  -> independent adversarial reviewer
  -> semantic evaluator
  -> bounded targeted rewrite
  -> hash-guarded human acceptance
  -> acceptance memory event
```

`agent-revise-workflow --review-scope comprehensive` 也使用同一类型化检索层，把相关正史、人物记忆和作者显式偏好加入综合审读与后续修订；旧章不运行新章专用的因果模拟。

写前因果模拟输出利益相关者、已知信息、欲望、恐惧、可用权力、可能失误、事件前置条件、代价转移和未决后果。缺少关键机制时必须 `blocked`，不能用新设定补洞。

如果发动机已经把人物未来应当抵达的主题答案写明，系统保留源文件不变，但会为 planner/writer 生成去答案的执行上下文。计划中任何视角越界或对 theme question 的直接回答都会在写正文前触发最多两次计划修复；仍不通过则停止。

每个计划场景拥有稳定 `scene_id`、视角、入口状态和出口状态。对抗审读必须逐场验证状态是否真正发生，并逐条验证章节契约。

## 硬门禁

v1 已提供：

- 明确禁止结论的文本命中；
- 禁止视角人物连续出现内在动作的可疑场景；
- 奏疏、信件、梦境或回忆等受限长段的长度检查；
- 场景状态与显式约束逐条反证；
- P1/P2 对抗审读问题阻断采纳；
- 源稿与候选哈希保护；
- 采纳后才记录长期接受事件。

当前增强版还会把显式数量运算、旅行时间窗和物件转移编译为 `story_fact_ledger.json`：控制器先验证算式与计划状态，再把账本交给 writer、对抗审读和 evaluator。正文中的隐性语义矛盾与完全可靠的自动视角识别仍不能只靠确定性规则，必须保留模型反证和人工采纳。

场景状态复杂时可传入 `--scene-by-scene`。系统会归一场景目标、分别生成正文、修复明显欠长/超长、传递上一场出口状态和末尾文本，再组装整章并运行相同门禁；验证失败时保持场景状态逐场复修，不再回退成一次整章重写。详见 [故事事实账本与逐场景写作](story-fact-ledger-and-scene-writing.zh-CN.md)。

## 权限边界

- 索引构建和查询不调用模型、不修改正文；
- 因果模拟、写作和审读只写 run 目录；
- 只有 `agent-accept-revision` 可以在哈希一致时应用候选；
- 正史同步建议不会自动写入正史；
- 只有作者明确确认的偏好才能进入 `preferences.jsonl`。
