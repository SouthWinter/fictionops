# 故事事实账本与逐场景写作

## 为什么需要这一层

长篇写作中的数量、路程耗时和物件位置，不能只靠模型“记得差不多”。FictionOps 先让因果模拟器把相关事实声明为结构化规则，再由控制器在正文生成前检查算式、时间窗和场景状态交接。

这一层保存的是当前章节的执行断言，不会自动修改正史。缺少换算规则或必要机制时，因果模拟应返回 `blocked`，不能临时编造答案。

## 事实账本

每次新章工作流会生成：

```text
story_fact_ledger.json
```

账本当前支持：

- `quantities`：运算类型、操作数、期望值、单位、容差和正文禁止出现的错误说法；
- `timelines`：起点、终点、最短/最长耗时和计划给出的实际耗时断言；
- `objects`：物件初始状态、稳定状态码、按序 transition id、绑定 event id 的转移和禁止状态；
- `unit_conversions`：本章允许使用的明确换算关系；
- `issues`：错误算式、时间越界、单位冲突、物件同时处于多个状态、相邻场景交接不一致等阻断项。

结构化规则来自模型，但控制器不接受模型自证。例如 `2000 * 3 = 5000` 会在写正文前失败。自然语言状态允许写得具体，连续性只比较稳定 `code`；能够从 transition assertions 唯一推导出的抄写错误由控制器规范并留痕，事件映射或语义冲突仍会阻断。

章节目标字数、段落数、场景数和 token budget 属于写作控制参数，不是故事内数量，会在 causal parse 时从事实账本剥离。

正文里没有显式复述的隐性数量或时序矛盾，仍由 `adversarial-reviewer` 和八维 evaluator 检查。事实账本提高确定性，不声称替代文学语义审读。

## 逐场景写作

默认模式仍用一次模型调用写完整章。对于场景较多、状态交接复杂或通用 API 模型容易遗忘前文的章节，可以启用：

```bash
fictionops agent-write-workflow path/to/chapter.md \
  --engine path/to/chapter_engine.md \
  --outline path/to/book_outline.md \
  --scene-by-scene \
  --runner python examples/agent_runner_openai_chat.py
```

此模式会：

1. 由 planner 给每场声明 `scene_id`、视角、功能、权重、入口状态和出口状态；
2. 按章节目标体量与场景相对权重归一分配柔性目标字数，planner 不能让各场总量漂离章节虚目标；
3. 每场单独调用 `scene-writer`，输入本场契约、事实账本、项目记忆、前一场出口状态和前一场末尾最多 3000 字符；
4. 拒绝带标题、分析或包装说明的场景输出；
5. 按计划顺序组装 `candidate.md`，并写出 `scene_execution.json`；
6. 单场明显欠长或超长时最多修复两次，再对组装后的完整章节运行与整章模式相同的四层验证。

`scene_execution.json` 记录每场目标/实际字符数、入口/出口状态、输出路径和哈希，便于定位是哪一场造成断裂。

## 当前重写策略

逐场景初稿整章验证失败后，系统保留每场入口/出口状态和原始输出。controller 会把 reviewer 的原文证据与失败的 `scene_id` 路由到具体场景，只调用这些场景的 rewriter；未命中的场景逐字保留。证据无法定位或属于全章静态失败时，才回退为全场复修。重新组装后仍做整章复核，复修目标沿用归一后的场景体量，允许删除重复动作和解释，但不能靠压缩到欠长解决问题。

真实 DeepSeek dogfood 表明，这条路径能保持体量与物件连续性，但会显著增加调用数。此后新增的 `--max-model-calls` 与 `--max-runtime-seconds` 会在每次模型调用前执行本地硬门禁，并将证据写入 `model_budget.json`；预算耗尽不会继续调用 runner。详见 [逐场景真实模型 Dogfood](dogfood-scene-writing-2026-07-11.zh-CN.md)。

## 权限边界

- 模型输出只进入 run 目录；
- 事实账本不是正史，不会自动写回设定；
- 场景组装不会创建或覆盖正式章节；
- 只有整章通过全部门禁后，作者才能用 `agent-accept-revision` 显式采纳。
