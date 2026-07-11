# FictionOps Agent 系统设计

## Preservation-Aware Verifier

综合 reviewer 的输出不是直接修订指令。旧章修订链路在 reviewer 与 reviser 之间增加独立 preservation verifier，并保存三层证据：原始 `reviewer_issues`、逐条 `preservation_verification`、最终 `effective issues`。

每条 finding 只能进入以下状态之一：

- `uphold`：问题有章节或权威上下文证据，且修订不会破坏保留约束；
- `withdraw`：finding 自己承认无需修改，或把有意功能误判为缺陷；
- `needs_counterevidence`：可能成立，但证据不足，不能交给 reviser 擅自处理。

确定性规则优先于模型裁决，例如 `No change needed`、`无需修改`、`建议保留` 出现在 issue 内时必须撤回。独立模型不能取得作者权限；它只能缩小自动修订集合，不能接受稿件、改写 canon 或删除原始审计记录。

当前要求级完成度见 [Agent Runtime 完成度审计](agent-runtime-completion-audit.zh-CN.md)。

> 状态：实现中。Memory-first Agent 已落地类型化记忆、显式作者偏好、因果模拟、故事事实账本、逐场景状态契约、独立反证、确定性门禁、选择性场景复修、执行预算和采纳后事件；主要未完成项已转向统一产品入口与项目级 controller。

## 1. 一句话定位

FictionOps Agent 是一个面向长篇小说的、文件优先的有状态写作 Agent。它观察项目状态，编译任务所需上下文，调用模型完成规划、写作、审读或修订，使用确定性工具与语义审稿共同验证结果，在明确权限边界内持续推进，并把每次决定留成可复查的证据。

它不追求“一键写完一本书”。它追求的是：在数百万字、数百章、多卷、多视角、长期伏笔和复杂信息边界下，模型仍能知道现在在做什么、为什么做、哪些不能改，以及做完后如何证明没有伤到别处。

## 2. 设计判断

### 2.1 一个控制器，多个角色

核心运行时采用“确定性 controller + 有边界的模型角色”，不采用多个 Agent 自由对话的松散 swarm。

- controller 负责状态机、权限、任务路由、预算、重试、日志和停止条件；
- 模型负责需要语义判断的规划、写作、审读、修订和候选比较；
- 本地工具负责文件发现、静态扫描、差异比较、哈希、门禁和发布；
- 作者负责审美方向、正史裁决、源文件采纳和外部发布。

“多个角色”首先是同一模型的不同任务契约，并不等于必须调用多个模型。只有当独立判断确实能降低风险时，才并行调用不同 reviewer。

### 2.2 Agent 完成工作，人类行使权威

Agent 不应只给一句“这里有问题”就停下。对于一次章节修订，它应当完成：发现问题、形成修订计划、改写候选、重跑审计、核对不变量、必要时再次修订、生成差异和采纳说明。

人类复核边界应尽量靠后，只保留真正需要作者权威的动作：

- 接受哪一版文字进入正文；
- 修改正史、人物终点、信息释放计划等高层事实；
- 删除或覆盖源材料；
- 发布到外部平台。

因此，“不自动覆盖正文”不等于“Agent 没有完成修订”。完成态应是一个已经复检、可以采纳的候选补丁，而不是一份未经处理的模型输出。

### 2.3 JSON 是机器契约，Markdown 是人的视图

所有状态、问题、任务、决策和验收结果先有版本化 JSON schema，再渲染成人可读 Markdown。不能继续让 controller 从自然语言报告中猜下一步。

### 2.4 证据比自信重要

每个结论都应能回答：

- 使用了哪些源文件和版本；
- 哪个模型、角色和提示词作出判断；
- 发现对应正文的哪些位置；
- 候选稿改了什么；
- 哪些门禁通过、失败或被作者豁免；
- 最终由谁在何时采纳。

## 3. 总体架构

```text
作者目标 / 项目状态
        |
        v
1. Observer 观察器
   扫描文件、会话、未闭合问题、变更与门禁
        |
        v
2. Controller 控制器
   选择工作流、风险级别、预算和下一步
        |
        v
3. Context Compiler 上下文编译器
   按任务检索、裁剪、排序并记录来源
        |
        v
4. Worker 模型角色
   规划 / 起草 / 审读 / 修订 / 正史同步建议
        |
        v
5. Verifier 验证器
   静态审计 + 语义不变量 + diff + 完整性检查
        |
        +------ 失败且可恢复 ------> Controller 重规划/重试
        |
        v
6. Approval Gate 采纳门禁
   自动暂存；高风险变更等待作者确认
        |
        v
7. Commit & Memory 写回
   应用补丁、同步复盘、记录事件与经验
```

FictionOps 核心提供 controller、上下文编译、协议、状态、门禁和审计。供应商 adapter 只负责把标准任务发给 OpenAI-compatible API 等模型服务。Codex skill 是同一核心之上的交互入口，不另造一套状态。

## 4. 六层状态与记忆

### 4.1 正史层 Canon

世界规则、人物弧线、信息释放、伏笔、时间线、物件位置和已经采纳的正文。它是高权威、低频修改的记忆。

### 4.2 计划层 Plan

总纲、卷纲、书纲、章节发动机、场景计划与当前创作意图。计划可以变化，但变化必须与正史区分。

### 4.3 工作层 Workspace

当前源章节、候选稿、diff、审读发现和上下文包。这里允许模型反复尝试，不直接代表正史。

### 4.4 会话层 Session

记录一个目标从开始到结束的状态：任务、步骤、模型调用、预算、失败、重试、人工决策和最终结果。会话必须可恢复，不能依赖聊天窗口还在。

### 4.5 问题账本 Issue Ledger

每个问题拥有稳定 ID，而不是每轮审计重新生成一堆互不相干的文字。建议字段：

```json
{
  "issue_id": "iss_ch026_style_negation_003",
  "scope": "chapter",
  "category": "prose.exclusionary_narration",
  "severity": "P2",
  "confidence": 0.86,
  "evidence": [{"file": "...", "start_line": 181, "end_line": 184}],
  "why_it_matters": "旁白连续排除解释，场景被作者判断替代",
  "preserve_constraints": ["保留此处信息遮蔽", "不改变耶儿的认知范围"],
  "status": "open",
  "resolution": null
}
```

状态至少包括 `open`、`planned`、`addressed`、`verified`、`accepted`、`rejected`、`waived` 和 `reopened`。

### 4.6 经验层 Preference Memory

只记录作者明确接受或拒绝过的可泛化偏好，例如：

- 保留有主题作用的“不是”，删除代替场景解释的“不是”；
- 白笈的聪明应低可见，不写成公开谋士；
- 神剑知识按人物认知分层，不让陌生角色默认知道其威力；
- 章节字数目标有弹性，达到目标下限附近即可停止机械补字。

经验必须附带来源决定和适用范围，不能把一次局部修改擅自升级为全书规则。

## 5. 核心运行循环

统一循环采用：`Observe -> Diagnose -> Plan -> Act -> Verify -> Decide -> Commit -> Learn`。

### 5.1 Observe

读取用户目标、Git/文件变更、当前章节状态、未闭合 issue、最近会话和相关门禁。用源文件哈希判断上下文是否已经过期。

### 5.2 Diagnose

先做便宜、可重复的静态审计，再把有争议或高风险的部分交给语义 reviewer。输出结构化 issue，不直接动笔。

### 5.3 Plan

把 issue 合并为有顺序的修改组，明确：

- 本轮必须修什么；
- 必须保留什么；
- 哪些问题互相冲突；
- 成功后怎么验证；
- 允许改动的范围和预算。

### 5.4 Act

reviser 根据源文、问题账本、作者偏好和修订契约生成完整候选稿或最小补丁。默认只生成一个主候选；高风险局部可生成两个方案供比较。

### 5.5 Verify

验证分四层：

1. 文件完整性：标题、场景、人物名、长度和编码没有意外损坏；
2. 确定性审计：高频模式、信息表命中、连续性、章节波形等；
3. 语义不变量：事件、视角、人物意图、知识边界、伏笔遮蔽和语气是否被改坏；
4. 目标验证：原 issue 是否真的解决，是否引入新 issue。

Verifier 不应只看“问题词减少了多少”。它必须比较功能：该重复被保留是因为有节奏和主题作用，还是因为模型漏改。

### 5.6 Decide

控制器依据验证结果选择：

- `pass_to_approval`：候选可交给作者；
- `retry_targeted`：只针对失败 issue 再修一次；
- `replan`：修订方案本身有问题；
- `needs_human_decision`：存在审美冲突或正史歧义；
- `abort_recoverable`：模型、上下文或工具失败，可以恢复；
- `abort_unsafe`：源文件变化、权限越界或输出异常。

默认最多自动修订两轮。超过上限继续调用模型通常只会磨平文字，应停下来呈现冲突证据。

### 5.7 Commit

Agent 输出经验证的 `candidate.md`、`changes.diff`、`verification.json` 和简短采纳摘要。只有显式 `accept` 才应用到源文件；应用前再次核对源文件哈希，避免覆盖作者在会话期间的新修改。

### 5.8 Learn

采纳后更新 issue 状态、章节复盘和运行指标。只有作者明确表达或多次稳定选择的偏好，才进入 preference memory。

## 6. 章节状态机

```text
planned
  -> context_ready
  -> candidate_ready
  -> audited
  -> revision_planned
  -> revision_candidate
  -> verifying
       -> retrying -> revision_candidate
       -> needs_human_decision
       -> verified
  -> awaiting_approval
       -> rejected
       -> accepted
  -> applied
  -> canon_sync_pending
  -> closed
```

任一执行状态都可以进入 `failed_recoverable` 或 `blocked_stale_source`。状态迁移写入 append-only event log，由当前快照缓存加速读取。

## 7. 权限模型

| 级别 | 行为 | 默认策略 |
| --- | --- | --- |
| R0 | 读取、扫描、生成报告 | 自动执行 |
| R1 | 调用模型、生成任务包和候选 | 自动执行，受预算限制 |
| R2 | 在 run/session 目录写暂存稿、diff、验证报告 | 自动执行 |
| R3 | 用候选替换正文源文件 | 必须显式接受，写前校验哈希并保留备份/版本记录 |
| R4 | 修改正史、人物弧线、信息释放、总纲 | 按变更组单独确认 |
| R5 | 删除、公开发布、调用外部平台、使用凭据 | 始终由人确认 |

权限由工具声明和 policy engine 判断，不由模型在自然语言里自我授权。

## 8. 模型角色

第一阶段保留七种角色即可：

| 角色 | 主要职责 | 输出 |
| --- | --- | --- |
| Task Planner | 把作者目标转成范围、约束和验收条件 | `task_spec.json` |
| Context Curator | 判断本任务还缺哪些上下文 | 文件请求和相关性理由 |
| Draft Writer | 根据章节发动机写候选正文 | `candidate.md` |
| Semantic Reviewer | 检查人物、信息、连续性、伏笔与读者体验 | `issues.json` |
| Revision Planner | 将问题合并成不互相打架的修订组 | `revision_plan.json` |
| Reviser | 根据计划修改完整章节或局部范围 | `candidate.md` / patch |
| Semantic Verifier | 对照源稿、候选和约束判断是否通过 | `semantic_verification.json` |

正史管理员和发布员可在后续加入。风格、人物、信息边界等 reviewer 可以是 Semantic Reviewer 的不同 profile，不急着拆成独立进程。

## 9. 上下文编译器

当前按字符截断的 `context-pack` 应升级为带来源的分层编译器。

### 9.1 输入层级

1. 强制上下文：目标章节、任务契约、直接相邻章节、相关发动机；
2. 约束上下文：视角人物、信息边界、相关物件和伏笔；
3. 检索上下文：名字、地点、事件、对象的历史出现；
4. 摘要上下文：本书状态、长线人物弧和此前决定；
5. 可选上下文：风格样本、地区口吻、类似场景。

### 9.2 每个上下文片段必须带

- 文件路径和内容哈希；
- 文本范围；
- 被选入的原因；
- 权威级别；
- 是否允许模型据此新增事实；
- 截断说明。

第一版不需要向量数据库。先用结构化索引、实体名、章节邻接、表格关系和全文检索实现可解释召回；当真实 dogfood 证明遗漏主要来自语义召回后，再加入 embedding。

## 10. 一次完整章节修订

以第26章为例，目标命令最终应接近：

```powershell
fictionops agent revise "卷一_冰角/第一本_雪祭暗潮/第26章_冰中四人.md" `
  --goal "全面审读并修订，重点处理低价值的‘不是’，同时检查行文、信息边界、人物、连续性与新引入问题" `
  --provider deepseek `
  --model deepseek-chat
```

内部步骤：

1. 对源章节计算哈希并建立 session；
2. 运行静态审计，调用语义 reviewer，合并为 issue ledger；
3. 生成修订计划和 preserve constraints；
4. 调用 reviser 生成候选稿；
5. 生成源稿与候选 diff；
6. 对候选重跑同一组审计；
7. 调用 verifier 检查事件、人物、知识边界和留白是否受损；
8. 若只剩可修复失败，自动进行一次定向重修；
9. 输出 `ready_for_approval` 候选和验证摘要；
10. 作者接受后原子应用，更新复盘和 issue ledger。

作者看到的重点不是几十条中间命令，而是：改了哪些问题、保住了什么、还剩什么争议、候选稿在哪里、是否可采纳。

## 11. 标准运行产物

```text
00_management/agent_sessions/<session_id>/
  session.json
  events.jsonl
  task_spec.json
  context_manifest.json
  context_pack.md
  issues.before.json
  revision_plan.json
  source.snapshot.md
  candidate.v1.md
  candidate.v2.md              # 只有发生重试时
  changes.diff
  audits.before.json
  audits.after.json
  semantic_verification.json
  decision.json
  acceptance.json              # 人工接受/拒绝后生成
  summary.md
```

`session.json` 是当前快照，`events.jsonl` 是不可变证据。任何文件都不能保存 API key。

## 12. Controller 决策原则

当前 `agent-next` 只选择一条 CLI 命令。下一代 controller 应选择“工作流动作”，并携带前置条件、风险和成功条件：

```json
{
  "action": "revise_candidate",
  "workflow": "chapter_revision",
  "inputs": ["iss_ch026_style_negation_003"],
  "preconditions": ["source_hash_matches", "revision_plan_ready"],
  "risk": "R2",
  "budget": {"max_calls": 1, "max_output_tokens": 12000},
  "success": ["candidate_nonempty", "no_invariant_regression"],
  "on_failure": "verify_and_retry_once"
}
```

CLI 命令只是 action executor 的一种实现。这样 controller 不再被命令字符串和占位符绑死。

## 13. 验证与评价

### 13.1 单次任务指标

- issue precision：作者认为成立的发现比例；
- fix acceptance：候选修改被接受的比例；
- invariant violation：修订引入事件、人物、信息边界错误的次数；
- residual issue：复检后仍开放的问题；
- human edit distance：候选到最终采纳文本还需多少人工改动；
- retries、tokens、费用、耗时；
- stale-context 和恢复是否正确。

### 13.2 长期价值指标

- 相比普通聊天，准备上下文和定位前文节省的时间；
- 每章复盘后的返工轮数是否下降；
- 长线伏笔、正史和人物错误是否更早被发现；
- 作者接受的 Agent 修改是否能在后续章节保持；
- 同一类问题是否因 preference memory 而减少重复沟通。

文学质量不能压成单一分数。研究评估应使用“约束保持 + 有效发现 + 作者采纳 + 成本”的多维结果。

## 14. 故障与安全

必须覆盖这些失败：

- 模型超时、限流、空输出、截断和编码错误；
- 输出混入分析、Markdown 围栏或丢失章节片段；
- 源文件在会话中被作者改过；
- reviewer 与 reviser 对同一约束理解冲突；
- context pack 缺失权威文件或引用旧版本；
- 反复重试导致文字逐渐变平；
- 项目文本中的指令被模型误当系统指令；
- runner 泄露密钥或把敏感文本发给错误供应商。

安全策略：模型只接收任务允许的文本，把小说内容标记为数据；runner 默认无任意工具权限；输出先验证后暂存；应用前核对哈希；重试有上限；事件日志过滤 secret。

## 15. 产品入口

对普通作者，主入口应收束为四个：

```text
fictionops agent write <chapter>
fictionops agent review <chapter-or-book>
fictionops agent revise <chapter>
fictionops agent continue <project>
```

高级 CLI 继续存在，作为可组合工具、调试面和研究接口。默认体验中，用户不需要理解 `agent-run -> agent-exec -> agent-inbox -> review-workflow` 的全部细节。

Codex skill 与通用 API Agent 共用同一 runtime：

- Codex skill 负责把自然语言目标映射到 `fictionops agent ...`，展示 diff，并请求采纳；
- 通用 Agent 通过 Python API/CLI 和 provider adapter 运行；
- 两者读写相同 session schema、issue ledger、policy 和验证结果；
- 不拆成两个 GitHub 仓库，避免协议和行为分叉。

## 16. 实现顺序

### P0：闭环章节修订

这是当前最高价值工作。

- 新增统一 session runtime 和事件日志；
- 把 `review-workflow` 结果转成稳定 `issues.json`；
- 在现有 `agent-revise-workflow` 之后增加 diff 与验证；
- 自动重跑 before/after 审计；
- 增加一次定向重试；
- 产出 `ready_for_approval`，而不是停在 `ready_for_review`；
- 新增显式 `accept`，应用前检查源文件哈希；
- 用第26章进行真实 DeepSeek dogfood。

退出条件：Agent 能独立把第26章从全面审读推进到可采纳候选，作者只需比较、接受或拒绝。

当前实现状态（2026-07-10）：会话快照、事件日志、结构化问题、before/after 审计、diff、静态验证、模型语义不变量验证、最多一次默认定向重修、`ready_for_approval` 和哈希保护的显式 accept 已进入代码与回归测试。真实模型已在一章约 6500 字符的高风险旧章上完成 dogfood：首轮暴露出“只处理两处低风险问题却被批准”的假阳性；加固后，综合审读会读取静态问题账本，核心上下文预算会保留人物、连续性和写作规范，语义复核会同时检查情节不变量与 P1/P2 行文问题簇。复跑中，畸形 reviewer JSON 被一次有界结构修复恢复，浅层候选被否决并触发定向重修，第二版仍未解决核心问题时正确停在 `needs_revision_attention`，没有开放采纳。

这次 dogfood 也留下三项后续研究问题：第一，静态词频只能作为召回信号，模型仍需区分环境性“冷”与心理默认按钮；第二，复核模型可能误报自由间接引语的信息边界，并可能口头声称计数未变，因此结构化 delta 应保持事实优先；第三，降低模板词频不能以合并段落、压扁节奏为代价。下一步应加入“功能标注后的问题簇评估”和段落呼吸/节奏变化检查，而不是继续增加机械词频阈值。

### P1：结构化语义审读

- reviewer 强制输出 issue schema 和证据范围；
- 合并重复 issue，支持 reopen/waive；
- 分离“检测”“修订建议”“是否采纳”；
- 加入人物、信息边界、连续性和行文的 verifier profiles；
- 用已知高风险章节建立回归集。

退出条件：同一章重复运行时，问题身份和状态可追踪，且不会每次生成全新的散乱报告。

当前实现状态（2026-07-11）：项目级 `.fictionops/issues.json` 已保存稳定 issue ID、证据观察、session 和生命周期；同类问题按 metric、原文证据或描述相似度跨运行合并，已解决问题再次出现会 `reopened`。`agent issue` 支持带理由的作者 `waived/rejected/reopened` 决定，排除项不会进入下一轮修订任务。三类匿名高风险 reviewer fixture 覆盖信息边界、人物声音和行文/读者体验。

### P2：上下文编译器 v2

- 建立项目文件索引和权威级别；
- 增加引用原因、哈希和 token 预算；
- 支持实体与章节邻接检索；
- 检测过期摘要和相互冲突的设定；
- 记录实际被模型使用的上下文证据。

退出条件：大多数章节任务不再依赖人工手工挑文件，遗漏能被清楚解释和复现。

### P3：写章与写后闭环

- `agent write` 串联发动机、场景计划、候选正文和基础验证；
- 写后自动生成复盘草稿和正史同步建议；
- 正史变更按组等待确认；
- 下一章可读取已接受的复盘与决定。

退出条件：从章节计划到下一章可继续的状态形成完整循环。

当前实现状态（2026-07-11）：`agent-write-workflow` 已能从直接章节目标、发动机、可选大纲和项目感知上下文开始，依次调用因果模拟器、planner、draft writer、独立对抗审读和八维 evaluator；结构化故事事实账本会在写前检查数量、时间窗与物件交接，复杂章节可逐场景调用并记录状态交接。一次《江山》高风险章节的盲写 DeepSeek dogfood 已完整走过 21 次模型调用并正确拒绝文学质量不足的候选。由此加固了 schema 修复、稳定物件状态码、场景体量归一、证据 grounding、选择性场景复修，以及 `--max-model-calls` / `--max-runtime-seconds` 本地硬预算。成功后仍生成可采纳候选、复盘草稿和正史同步建议；采纳支持“目标原本不存在”的新章并防止并发覆盖。接受后的复盘/正史建议尚未接入通用 controller。

### P4：项目级 controller

- `agent continue` 从 session、issue ledger 和门禁选择工作流动作；
- 支持章节批次、书级清稿和发布准备；
- 增加费用、调用次数和时间预算；
- 支持暂停、恢复、取消和失败恢复；
- 生成面向作者的简洁工作台摘要。

当前实现状态（2026-07-11）：写章与修订闭环已共享持久化模型调用账本；逐场景重试会只复修受影响场景。统一入口和 session-aware `continue` 已落地，下一动作由纯函数 controller policy 根据 state、evidence、budget 和 authority 选择。主要阶段写入带源/产物哈希的 `checkpoint.json`，`agent cancel` 能显式终止未应用会话并阻止隐式恢复。`agent resume` 已支持写章安全阶段、修订审阅后与 `verification_ready` 恢复，恢复时开启新预算分段且不重跑已完成模型调用。runner receipt 已回传 provider/model/request id、token 与显式价格费用，并支持跨分段累计阈值；`agent status` 汇总项目级作者决策面；`trajectory.jsonl` 统一保存上下文归因、模型调用、验证、状态迁移与权限。重试循环任意指令点恢复与批次调度列为 1.x 扩展。

退出条件：controller 可以持续推进低风险工作，并在真正需要作者判断的地方停下。

### P5：Skill、开放 API 与研究证据

- 发布 Codex skill；
- 稳定 Python API、JSON schema 和 provider adapter；
- 建立匿名化 benchmark 与真实 dogfood 数据；
- 对照 raw chat、单次 RAG 和 FictionOps closed loop；
- 报告采纳率、不变量错误、返工、成本与作者时间。

退出条件：同一核心既能作为开源产品使用，也能作为长程 Agent 研究平台复现实验。

## 17. 当前能力映射

| 目标组件 | 当前基础 | 主要缺口 |
| --- | --- | --- |
| Observer | `doctor`、各类 audit、`agent-inbox` | 缺统一状态快照和源哈希依赖图 |
| Controller | `agent continue`、`agent-next`、写章/修订闭环、`model_budget.json` | 已有 session-aware 安全续跑与 R0 自动动作；仍缺跨会话模型调用恢复/取消和批次调度 |
| Context Compiler | `context-pack`、`draft-brief`、project-aware context | 已有路径/实体/相邻章检索、来源哈希与权威说明；后续再用 dogfood 判断是否需要 embedding |
| Model Worker | OpenAI-compatible runner、因果/规划/写作/审读/复修角色 | 章节级角色闭环与 provider 级 token/费用 receipt 已形成；不同供应商仍需各自验证 usage 字段兼容性 |
| Revision | `agent-revise-workflow`、`agent-accept-revision` | 已有候选、diff、复检、定向重试、预算和哈希保护采纳；需继续积累真实采纳率证据 |
| Verifier | 静态审计、语义 verifier、门禁 | 已比较六类不变量；后续需建立高风险章节回归集和独立 reviewer 策略 |
| Session | `agent-session`、revision `session.json`/`events.jsonl` | revision 已有事件溯源；通用 session 尚未统一到同一状态机 |
| Memory | 项目文件、类型化索引、显式 preference、采纳事件、revision issue ledger | 记忆基础已落地；仍缺 controller 自动消费采纳后的复盘/正史同步决定 |
| Evaluation | `eval-agent`、dogfood 文档 | 还未衡量真实修订采纳和人工返工 |

## 18. 最近的工程决策

下一步不继续增加零散审计命令，也不先做 Web UI、向量数据库或多 Agent swarm。P0-P3 的章节闭环已有实现和真实失败证据，后续主线转为 P4：统一 `fictionops agent ...` 产品入口、可恢复的 `agent continue`、跨会话 issue/决定消费，以及 provider token/费用预算。

第26章应成为第一个端到端基准。之后再选择一章信息边界风险高、一章人物口吻风险高的正文，形成三章回归集。这样每次扩展 controller、上下文或模型供应商时，都能证明系统不是“跑通了 API”，而是真的减少了长篇修订中的人工协调成本。
