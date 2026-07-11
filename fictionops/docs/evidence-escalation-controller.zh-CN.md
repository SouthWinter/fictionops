# Evidence Escalation Controller

`needs_counterevidence` 不应直接等同于“交给作者”。很多争议只是当前 evidence window 与 finding 的断言尺度不匹配：单段材料无法判断全章功能，单句台词无法证明人物如何获得精确库存，相邻段未提供时也不能裁决跨段模板化。

## 命令

对已标注 packet，只处理 `insufficient`：

```powershell
fictionops agent counterevidence escalate counterevidence.annotated.json `
  --chapter path/to/full-chapter.md `
  --out evidence-escalation.json `
  --format json
```

对未标注 packet，controller 会预路由全部 finding。`--chapter` 可省略；省略时 controller 仍生成证据请求，但状态保持 `needs_source`，不会伪造已找到的证据。

## 路由

- `full_chapter`：章节功能、推进速度、高潮/过渡/停顿、伏笔与前后回声；
- `adjacent_paragraphs`：跨段重复、排比、句法与节奏；
- `knowledge_source`：人物知道什么、何时知道、信息从哪里来；
- `character_memory`：人物声音、年龄模式、关系阶段；
- `author_intent`：无法由项目事实裁决，只能回到稳定 author guard。

路由优先读取 finding 的实质断言，不盲信模型 category。例如 category 即使写成 `information boundaries`，problem 若讨论全章 forward momentum，也必须取 `full_chapter`。

## 去重与证据边界

Controller 对 reviewer finding 的 category、evidence、problem 和 suggested action 做确定性精确指纹。完全相同的 finding 合并为一个 evidence request，并保留全部 sample id。它不做模糊语义合并，以免把相似但边界不同的问题错误折叠。

补证结果分为：

- `ready_for_reverification`：已取得请求范围内的材料，可交给独立 verifier 重判；
- `needs_source`：缺少章节或项目来源，应先请求材料；
- 任何状态都不直接改正文。

## 作者盲评 Dogfood

对 16 条作者盲评中的 6 条 `insufficient` 运行 controller：

- 精确去重后形成 4 个请求，折叠 2 条重复 finding；
- 3 个请求需要全章；
- 1 个请求需要相邻段落；
- 因 benchmark 只有匿名片段且未提供原章，4 个请求全部正确停在 `needs_source`；
- 第一轮曾被模型 category 误导，把“全章推进”错路由为知识来源；调整为 problem 语义优先后修正。

公开结果见 [`deepseek-counterevidence-v1.escalation.json`](evidence/deepseek-counterevidence-v1.escalation.json)。这证明的是去重、路由与缺源停止，不证明补证后的模型重判已经完成。
