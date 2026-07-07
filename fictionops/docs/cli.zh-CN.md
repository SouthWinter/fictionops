# FictionOps CLI

> 当前 CLI 是无模型调用、无数据库、无第三方依赖的本地工具。第一阶段覆盖项目初始化、书/章创建、章节规划同步、写后复盘、静态审计、范围化上下文包和报告导出。

面向使用者的详细说明见本文档；面向开发者和 Agent 的稳定承诺见 [CLI 契约](cli-contracts.zh-CN.md)。

## 1. 运行方式

源码方式：

```bash
python fictionops/src/fictionops/cli.py --version
```

可编辑安装：

```bash
pip install -e fictionops
fictionops --version
```

## 1.5 `fictionops adopt`

扫描一个已经存在的写作目录，生成迁移诊断报告。这个命令适合在旧项目正式迁入 FictionOps 前运行：

```bash
fictionops adopt existing-novel --out adopt_report.md
```

输出 JSON：

```bash
fictionops adopt existing-novel --format json
```

限制明细数量：

```bash
fictionops adopt existing-novel --max-files 120
```

说明：

- `adopt` 只读扫描旧目录，不创建 FictionOps 项目，不搬移文件，也不修改源文件；
- 它会把旧大纲、人物、设定、正史表、正文、复盘、发布材料和归档材料映射到 FictionOps 层级；
- 它会给出 `migration_phase` 和 `suggested_target_path`，作为人工复制材料时的目标路径参考；
- 默认会忽略 `.git`、`.github`、`fictionops`、`build`、`dist`、`node_modules` 等目录，避免把工具代码或构建产物当成长篇材料；
- 如果要把诊断报告写入旧目录，使用 `--out`；已有输出文件需要 `--force` 才会覆盖；
- 扫描完成后，建议先运行 `fictionops init <new-project>` 建一个干净目录，再按诊断报告分层迁移材料。

## 2. `fictionops init`

初始化一个 FictionOps 长篇项目骨架：

```bash
fictionops init my-novel --title "My Novel"
```

常用参数：

```bash
fictionops init my-novel --dry-run
fictionops init my-novel --language zh-CN
fictionops init my-novel --force
```

说明：

- 默认不会覆盖已有文件。
- `--force` 会覆盖生成文件。
- `--dry-run` 只显示计划动作，不写入文件。

## 3. `fictionops new-book`

创建一本书的书纲、正文目录、章节发动机目录、逐章复盘目录和书级复盘文件。

```bash
fictionops new-book my-novel --book book_02 --title "第二本"
```

默认写入：

```text
04_structure/book_outlines/book_02_outline.md
06_drafts/book_02/chapters/
06_drafts/book_02/chapter_engines/
06_drafts/book_02/draft_briefs/
06_drafts/book_02/revision_notes/
07_audits/book_retrospectives/book_02_retrospective.md
```

书号支持：

- `2`
- `02`
- `book_02`
- `book-02`

安全参数：

```bash
fictionops new-book my-novel --book 2 --dry-run
fictionops new-book my-novel --book 2 --force
```

说明：

- 默认不会覆盖已有书纲和书级复盘；
- `--force` 会覆盖生成文件，目录本身只会确保存在；
- `new-book` 不会自动生成章节，章节仍由 `new-chapter` 逐章创建。

## 4. `fictionops new-chapter`

一次创建一章正文、章节发动机和章节复盘文件。

```bash
fictionops new-chapter my-novel --chapter 002 --title "第二章"
```

默认写入：

```text
06_drafts/book_01/chapters/ch_002.md
06_drafts/book_01/chapter_engines/ch_002_engine.md
06_drafts/book_01/revision_notes/ch_002_retrospective.md
```

指定书目录：

```bash
fictionops new-chapter my-novel --book book_02 --chapter 001 --title "新卷开端"
```

给章节发动机预填视角、章节性质和建议体量：

```bash
fictionops new-chapter my-novel --chapter 002 --viewpoint "某人物" --kind "转场" --target-chars 8200
```

章节编号支持：

- `1`
- `001`
- `ch_001`
- `第1章`

安全参数：

```bash
fictionops new-chapter my-novel --chapter 002 --dry-run
fictionops new-chapter my-novel --chapter 002 --force
```

说明：

- 默认不会覆盖已有章节三件套；
- `--force` 会覆盖正文、发动机和复盘文件，使用前要确认不需要保留旧稿；
- 复盘文件放在 `revision_notes/`，这样 `audit-continuity` 可以做逐章配套检查；
- 这个命令只负责建文件，不替作者填写章节发动机。

## 5. `fictionops plan-chapter`

从书纲的“逐章规划”表读取某一章，把计划填入对应章节发动机。

```bash
fictionops plan-chapter my-novel --book book_01 --chapter 002
```

默认读取：

```text
04_structure/book_outlines/book_01_outline.md
```

默认写入：

```text
06_drafts/book_01/chapter_engines/ch_002_engine.md
```

它会识别书纲中的逐章规划表：

```markdown
| 章 | 标题 | 视角 | Pressure | Desire | Obstacle | Change | Remainder | 体量 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 02 | 第二章 | 某人物 | 外部压力 | 本章欲望 | 阻碍 | 变化 | 余味 | 8200 |
```

支持的章节编号：

- `2`
- `02`
- `002`
- `ch_002`
- `第2章`

指定书纲路径：

```bash
fictionops plan-chapter my-novel --chapter 002 --outline 04_structure/book_outlines/book_01_outline.md
```

安全参数：

```bash
fictionops plan-chapter my-novel --chapter 002 --dry-run
fictionops plan-chapter my-novel --chapter 002 --force
```

说明：

- 默认只填发动机里的空字段；
- 如果发动机已有标题、视角、体量或五列发动机内容，会跳过这些非空字段；
- `--force` 会覆盖非空字段；
- 如果章节发动机不存在，会提示先运行 `new-chapter`；
- 这个命令只负责把“书纲计划”同步到“章节发动机”，不自动写正文。

## 6. `fictionops scene-plan`

把已经填写好的章节发动机转成场景骨架，供写正文前检查压力、信息边界和伏笔回声。

```bash
fictionops scene-plan my-novel --book book_01 --chapter 002
```

默认读取：

```text
06_drafts/book_01/chapter_engines/ch_002_engine.md
```

输出 JSON：

```bash
fictionops scene-plan my-novel --chapter 002 --format json
```

写入场景计划：

```bash
fictionops scene-plan my-novel --chapter 002 --out 06_drafts/book_01/scene_plans/ch_002_scene_plan.md
fictionops scene-plan my-novel --chapter 002 --out 06_drafts/book_01/scene_plans/ch_002_scene_plan.md --force
```

说明：

- 它读取标题、视角、章节性质、目标字数和五列发动机；
- 它会带出连续性、信息边界、伏笔回声、留白要求和风格提醒；
- 如果“场景顺序”已经填写，会尊重作者填写的场景顺序；
- 如果“场景顺序”为空，会按 Pressure、Desire、Obstacle、Change、Remainder 生成默认五段骨架；
- 它不调用模型，不写正文，只负责把章节发动机转成更容易执行的场景层计划。

常见提示：

| Code | 含义 |
| --- | --- |
| `missing_engine_field` | 五列发动机中有空字段，写正文前应补齐 |
| `generated_scene_order` | 场景顺序为空，命令生成了默认骨架，建议作者再手调 |

使用建议：

- `plan-chapter` 之后跑一遍，确认章节发动机能支撑场景；
- 写正文前如果觉得“只有内容点，没有场景”，先跑它；
- 场景计划可以写出到 `scene_plans/`，也可以只看 stdout，不污染草稿层。

## 7. `fictionops draft-brief`

把场景骨架、范围化上下文和写作禁区合成一份写前任务单。它适合交给人类作者，也适合交给正文写作 Agent。

```bash
fictionops draft-brief my-novel --book book_01 --chapter 002
```

输出 JSON：

```bash
fictionops draft-brief my-novel --chapter 002 --format json
```

写入任务单：

```bash
fictionops draft-brief my-novel --chapter 002 --out 06_drafts/book_01/draft_briefs/ch_002_draft_brief.md
fictionops draft-brief my-novel --chapter 002 --out 06_drafts/book_01/draft_briefs/ch_002_draft_brief.md --force
```

默认只列上下文文件清单，不嵌入上下文全文。需要给写作 Agent 打包材料时，可以显式开启：

```bash
fictionops draft-brief my-novel --chapter 002 --include-context-content --max-chars-per-file 4000 --max-total-chars 24000
```

说明：

- 它会内部调用 `scene-plan`，拿到场景任务、信息边界、伏笔回声和留白要求；
- 它会内部调用 `context-pack --task draft`，拿到写作所需上下文和缺失文件；
- 它会输出写前检查、必须做、禁止做、逐场景写作目标、上下文文件表和问题列表；
- 它不调用模型，不写正文，只把“写这一章前必须守住什么”压成任务单。

常见提示：

| Code | 来源 | 含义 |
| --- | --- | --- |
| `missing_engine_field` | `scene-plan` | 五列发动机中有空字段 |
| `generated_scene_order` | `scene-plan` | 场景顺序为空，命令生成了默认骨架 |
| `missing_required_context` | `context-pack` | 写作所需的必读上下文文件缺失 |

使用建议：

- `scene-plan` 之后跑一遍，确认任务单能支撑正式写作；
- 如果 brief 里有 P2 缺失上下文，优先补文件或明确人工豁免；
- 它比 `agent-prompt` 更偏任务材料，比 `context-pack` 更偏写作执行。

## 8. `fictionops post-draft`

检查某一章写完后是否完成了最小闭环：正文不是占位，章节发动机存在，逐章复盘已填写，同步项没有只留在记忆里。

```bash
fictionops post-draft my-novel --book book_01 --chapter 002
```

输出 JSON：

```bash
fictionops post-draft my-novel --chapter 002 --format json
```

写入关门报告：

```bash
fictionops post-draft my-novel --chapter 002 --out 07_audits/post_draft/ch_002_gate.md
fictionops post-draft my-novel --chapter 002 --out 07_audits/post_draft/ch_002_gate.md --force
```

调整占位判断阈值：

```bash
fictionops post-draft my-novel --chapter 002 --min-chapter-chars 800
```

状态：

| Status | 含义 |
| --- | --- |
| `needs_draft` | 正文缺失或仍像占位 |
| `needs_engine` | 章节发动机缺失或仍像模板 |
| `needs_retrospective` | 逐章复盘缺失或仍像模板 |
| `sync_needed` | 复盘中已有同步项，需要进入正史/人物/信息/伏笔同步 |
| `ready_for_review` | 可进入审稿链路 |

说明：

- 它只检查单章的写后关门状态；
- 它会提取复盘里的“需要同步到人物弧线/信息释放表/伏笔回声表/书纲/归档旧案”；
- 它不调用模型，不改正文，不自动同步正史。

## 8.1 `fictionops review-gate`

聚合单章进入正式审修前的关键检查：写后关门、连续性、信息边界、人物记忆、伏笔回声、风格模式和章节体量波形。

```bash
fictionops review-gate my-novel --book book_01 --chapter 002
```

输出 JSON：

```bash
fictionops review-gate my-novel --chapter 002 --format json
```

写入审稿门禁报告：

```bash
fictionops review-gate my-novel --chapter 002 --out 07_audits/review_gate/ch_002_review_gate.md
fictionops review-gate my-novel --chapter 002 --out 07_audits/review_gate/ch_002_review_gate.md --force
```

状态：

| Status | 含义 |
| --- | --- |
| `needs_post_draft` | 先补正文、章节发动机、逐章复盘或同步项 |
| `needs_review_fixes` | 已进入审稿链路，但存在 P0/P1/P2 阻塞问题 |
| `review_notes` | 没有阻塞问题，但存在非阻塞提示 |
| `review_passed` | 当前门禁未发现问题 |

说明：

- 它不替代底层审计；它负责先把阻塞项聚到一张单章表里；
- 它只写报告，不改正文，不调用模型；
- 它适合放在 `post-draft` 之后、`revision-plan` 之前。

## 8.2 `fictionops book-gate`

聚合一本书进入清稿导出前的关键检查：书纲计划覆盖、书/章复盘闭合、修订计划阻塞项、项目表格结构、词频提示和章节体量波形。

```bash
fictionops book-gate my-novel --book book_01
```

输出 JSON：

```bash
fictionops book-gate my-novel --book book_01 --format json
```

写入书级门禁报告：

```bash
fictionops book-gate my-novel --book book_01 --out 07_audits/book_gate/book_01_gate.md
fictionops book-gate my-novel --book book_01 --out 07_audits/book_gate/book_01_gate.md --force
```

状态：

| Status | 含义 |
| --- | --- |
| `needs_book_material` | 缺书纲、计划章节或正文等基础材料 |
| `needs_book_closure` | 存在书级收束阻塞项 |
| `book_notes` | 没有阻塞项，但有非阻塞提示 |
| `ready_for_clean_export` | 可进入 `export-clean` |

说明：

- 它不会导出 clean Markdown；发布稿仍由 `export-clean` 生成；
- 它会显式检查 Markdown 表格结构；普通正文没有表格不会被当作阻塞；
- `scan-words` 在这里只作为书级文字新鲜度提示，不会自动要求改词；
- 它会把某些书级收束问题视为阻塞，即使底层审计里只是 P3/P4；
- 它适合放在 `retrospective` 和 `revision-plan` 之后、`export-clean` 之前。

## 9. `fictionops audit-plan`

检查书纲逐章规划、章节正文和章节发动机是否对齐。

```bash
fictionops audit-plan my-novel --book book_01
```

它会检查：

- 书纲里计划了哪些章节；
- 计划章节是否已有正文文件；
- 计划章节是否已有章节发动机；
- 章节发动机是否已经同步书纲里的标题、视角、五列发动机和体量；
- 是否存在“正文已建，但书纲没有对应行”的章节。

输出 JSON：

```bash
fictionops audit-plan my-novel --book book_01 --format json
```

指定书纲路径：

```bash
fictionops audit-plan my-novel --book book_01 --outline 04_structure/book_outlines/book_01_outline.md
```

常见提示：

| Code | 含义 |
| --- | --- |
| `missing_chapter_file` | 书纲计划了该章，但没有正文文件 |
| `missing_chapter_engine` | 书纲计划了该章，但没有章节发动机 |
| `engine_not_synced` | 章节发动机存在，但没有同步书纲里的计划字段 |
| `unplanned_chapter_file` | 正文文件存在，但书纲没有对应章节行 |
| `no_chapter_plan_rows` | 书纲里没有可解析的逐章规划表 |

使用建议：

- 写正文前跑一遍，确认施工面干净；
- 大纲改动后跑一遍，找出需要重新 `plan-chapter` 的章节；
- 它只检查“计划和文件是否对齐”，不判断章节内容好不好。

## 10. `fictionops retrospective`

汇总一本书的逐章复盘、书级复盘和同步项。

```bash
fictionops retrospective my-novel --book book_01
```

它会检查：

- `06_drafts/book_01/chapters/` 下有哪些正文；
- `06_drafts/book_01/revision_notes/` 下有哪些逐章复盘；
- `07_audits/book_retrospectives/book_01_retrospective.md` 是否存在、是否仍像模板；
- 逐章复盘里是否有待同步项，例如“需要同步到人物弧线”；
- 哪些章节缺逐章复盘，哪些复盘仍是占位模板。

输出 JSON：

```bash
fictionops retrospective my-novel --book book_01 --format json
```

写入报告：

```bash
fictionops retrospective my-novel --book book_01 --out 07_audits/book_retrospectives/book_01_report.md
fictionops retrospective my-novel --book book_01 --out 07_audits/book_retrospectives/book_01_report.md --force
```

常见提示：

| Code | 含义 |
| --- | --- |
| `missing_book_retrospective` | 缺书级复盘文件 |
| `placeholder_book_retrospective` | 书级复盘仍像模板 |
| `missing_chapter_retrospective` | 有正文，但没有对应逐章复盘 |
| `placeholder_chapter_retrospective` | 逐章复盘仍像模板 |
| `open_sync_item` | 逐章复盘里有待同步项 |

使用建议：

- 每写完一章后填对应 `revision_notes/ch_xxx_retrospective.md`；
- 写完一本后跑 `retrospective`，把未同步项处理完，再整理书级复盘；
- 它不判断章节写得好不好，只负责帮你看“写后记忆是否收束”。

## 11. `fictionops stats`

统计 Markdown 文件字数与章节体量分档。

默认只统计“章节文件”：

```bash
fictionops stats my-novel
```

章节文件识别规则：

- 位于 `chapters/` 目录下；
- 文件名形如 `ch_001.md`；
- 文件名含 `第01章`、`第一章` 等章节标记。

统计全部 Markdown：

```bash
fictionops stats my-novel --all
```

指定统计指标：

```bash
fictionops stats my-novel --metric nonspace
fictionops stats my-novel --metric cjk
fictionops stats my-novel --metric chars
```

三种指标：

| 指标 | 含义 | 适合场景 |
| --- | --- | --- |
| `nonspace` | 非空白字符数 | 中文长篇默认推荐，包含标点与拉丁字母 |
| `cjk` | CJK 汉字/汉字兼容区字符数 | 粗略估算中文正文汉字量 |
| `chars` | 原始字符数 | 技术统计，包含空格与换行 |

输出 JSON：

```bash
fictionops stats my-novel --format json
```

指定扫描模式：

```bash
fictionops stats my-novel --pattern "06_drafts/**/*.md"
```

## 11.1 `fictionops scan-words`

扫描 Markdown 文件中的高频词、短语和指定关注词。

```bash
fictionops scan-words my-novel
```

默认只扫描章节文件。若要扫描所有 Markdown：

```bash
fictionops scan-words my-novel --all
```

指定关注词：

```bash
fictionops scan-words my-novel --watch "不是,没有,旧城遗藏"
```

调整输出数量和最低命中次数：

```bash
fictionops scan-words my-novel --top 30 --min-count 3
```

输出 JSON：

```bash
fictionops scan-words my-novel --format json
```

说明：

- `scan-words` 是通用词频扫描，不判断某个词一定该删；
- 中文会做粗粒度短语统计，英文会按单词统计；
- 更偏风格诊断的章节开头/结尾模式，仍由 `audit-style` 负责。

## 11.2 `fictionops check-tables`

检查 Markdown 表格是否存在结构或占位风险。

```bash
fictionops check-tables my-novel --all
```

默认只检查章节文件；项目模板、人物表、正史表等通常需要 `--all`：

```bash
fictionops check-tables my-novel --all --pattern "**/*.md"
```

提高“有效行”要求：

```bash
fictionops check-tables my-novel --all --min-filled-cells 2
```

输出 JSON：

```bash
fictionops check-tables my-novel --all --format json
```

它会提示：

- 空表头；
- 重复表头；
- 有表头但没有正文行；
- 行宽和表头列数不一致；
- 正文行有效单元过少；
- 文件里没有表格。

说明：

- `check-tables` 只检查 Markdown 表格结构和占位情况，不理解剧情；
- 具体人物、信息、伏笔等领域表格，还应继续使用 `audit-characters`、`audit-info` 和 `audit-echoes`。

## 12. 体量分档

`stats` 会按所选 `--metric` 给每个文件分档：

| 档位 | 范围 |
| --- | --- |
| `short` | 小于 6000 |
| `lean` | 6000-7999 |
| `standard` | 8000-9999 |
| `heavy` | 10000-11999 |
| `very_heavy` | 12000 及以上 |

这些分档不是质量判断，只是让作者看见章节体量波形。短章可以很好，长章也可能松；关键是体量是否服务章节压力。

## 12.1 `fictionops audit-wave`

检查章节体量波形是否过平、连续同档过久，或相邻章节体量突跳。

```bash
fictionops audit-wave my-novel
```

默认只扫描章节文件，统计口径与 `stats --metric nonspace` 一致。常用参数：

```bash
fictionops audit-wave my-novel --flat-tolerance 200
fictionops audit-wave my-novel --min-spread-ratio 15
fictionops audit-wave my-novel --max-flat-run 4
fictionops audit-wave my-novel --format json
```

它不会判断短章或长章本身好坏，只提示三类需要复看的节奏信号：

- 整本章节体量过于接近，像是在机械填目标字数；
- 连续多章落在同一体量档，读感可能缺少呼吸；
- 相邻章节体量突然大跳，需要确认是否服务情节压力。

如果要把所有 Markdown 都纳入波形检查，可以使用：

```bash
fictionops audit-wave my-novel --all
```

## 13. `fictionops audit-style`

扫描 Markdown 正文中的风格模式。

```bash
fictionops audit-style my-novel
```

默认只扫描章节文件。若要扫描所有 Markdown：

```bash
fictionops audit-style my-novel --all
```

输出 JSON：

```bash
fictionops audit-style my-novel --format json
```

指定关注词：

```bash
fictionops audit-style my-novel --watch "不是,没有,有人,忽然,其实"
```

调整重复句首阈值：

```bash
fictionops audit-style my-novel --min-repeat 5
```

### 5.1 它检查什么

| 层级 | 检查项 | 作用 |
| --- | --- | --- |
| 词层 | `不是`、`没有`、`有人`、`忽然`、`其实` 等关注词 | 发现解释、否定、排比、突转的密度 |
| 句式层 | 重复句首，如“某某道：”“他没有……” | 发现对话节奏或叙述手势是否过于同款 |
| 章节层 | 开头/结尾类型 | 发现章节是否总以相似方式进出 |

默认关注词：

```text
不是, 没有, 无人, 有人, 所有人, 每个人, 忽然, 突然, 其实, 真正, 原来, 只是, 也许, 仿佛, 像是, 因为, 所以, 仍然
```

### 5.2 开头/结尾类型

`audit-style` 会粗略把每个文件的开头和结尾分成：

- `dialogue`：对话开头；
- `setting`：天气、空间、物件、环境；
- `body`：身体、伤痛、手眼动作；
- `summary`：时间概述或认知总结；
- `action`：动作推进；
- `other`：无法归类。

这只是启发式分类，不是文学判断。它的价值是让作者看见波形：如果三十章里二十章都以同一种方式开头，就值得回看。

### 5.3 如何解读

`audit-style` 不负责宣布“好/坏”。它只回答：

- 哪些词出现得多？
- 哪些句首重复得多？
- 哪些章节开头/结尾类型过于集中？
- 哪些文件最需要人工复看？

高频不一定错。比如政治朝堂章大量出现“某某道：”可能合理，但如果同时读感变平，就可以考虑用动作、沉默、错听、文书、眼神或场景调度替代一部分直白对话。

## 14. `fictionops audit-continuity`

检查 FictionOps 项目的维护连续性。

```bash
fictionops audit-continuity my-novel
```

它不会判断剧情是否精彩，也不会自动修正文。当前版本只检查两类缺口：

1. 项目级记忆文件是否存在、是否仍像未填模板；
2. 章节是否有对应章节发动机、复盘或修订记录。

### 6.1 常用参数

跳过标准项目文件检查，只看章节配套：

```bash
fictionops audit-continuity my-novel --skip-standard
```

输出 JSON：

```bash
fictionops audit-continuity my-novel --format json
```

调整“占位章节”阈值：

```bash
fictionops audit-continuity my-novel --min-chapter-chars 500
```

指定扫描模式：

```bash
fictionops audit-continuity my-novel --pattern "06_drafts/**/*.md"
```

### 6.2 它如何匹配章节发动机

`audit-continuity` 会识别：

- 每章一个发动机文件，如 `ch_001_engine.md`；
- 中文章节标记，如 `第01章`；
- 一张整本发动机表，只要文件名或正文中含 `engine`、`发动机`，并且正文中出现该章编号。

因此，整本“逐章发动机表”可以覆盖多章，不必强制拆成每章一个文件。

### 6.3 它如何匹配复盘

当前版本会寻找：

- 文件名或路径含 `retrospective`；
- 文件名或路径含 `revision_notes`；
- 文件名含 `复盘`；
- 且文件名或正文里能匹配该章编号。

如果一本书只有一个总复盘文件，但没有逐章行，当前会报告缺逐章复盘。这是有意设计：FictionOps 更关心“章节级压力、信息边界、人物残留有没有被记录”，不是只看有没有一个总结文件。

### 6.4 严重等级

| 等级 | 含义 |
| --- | --- |
| `P1` | 必需项目记忆缺失，如 `project.yml`、信息释放表、伏笔表 |
| `P2` | 章节缺发动机，写作前压力链不可追踪 |
| `P3` | 章节缺复盘或文件明显占位，后续接手成本高 |
| `P4` | 文件存在但仍像模板，属于可延后但应清理的问题 |

这些等级不是文学质量判断，而是项目维护风险。

## 15. `fictionops audit-echoes`

检查伏笔回声表的维护状态。

```bash
fictionops audit-echoes my-novel
```

它会自动寻找文件名或路径中含以下标记的 Markdown：

- `foreshadowing`
- `echo`
- `伏笔`
- `回声`

也可以手动指定表：

```bash
fictionops audit-echoes my-novel --table "05_canon/foreshadowing_echo_table.md"
```

输出 JSON：

```bash
fictionops audit-echoes my-novel --format json
```

关闭章节文本粗略扫描：

```bash
fictionops audit-echoes my-novel --no-text-scan
```

调整“太久没有回声”的章节间隔：

```bash
fictionops audit-echoes my-novel --stale-after 10
```

### 7.1 它能解析什么表

当前版本支持 Markdown 表格，并识别这些列：

| 语义 | 英文列名 | 中文列名 |
| --- | --- | --- |
| 伏笔名 | `Thread` | `线程`、`伏笔`、`线索` |
| 初次埋下 | `First Plant` | `初次埋下`、`初种`、`首次埋下` |
| 上次回声 | `Last Echo` | `上次回声`、`最后回声`、`最近回声` |
| 当前状态 | `Current State` | `当前状态`、`读者记忆` |
| 下一次轻回声 | `Next Light Echo` | `下一次轻回声`、`下次回声` |
| 禁提前解释 | `Do Not Reveal Yet` | `禁止提前解释`、`禁提前解释` |
| 兑现方向 | `Payoff Direction` | `兑现方向`、`兑现/转化方向`、`转化方向` |

### 7.2 它检查什么

| 检查 | 等级 | 含义 |
| --- | --- | --- |
| 缺伏笔表 | `P1` | 项目没有可追踪的伏笔回声表 |
| 找到表但没解析出伏笔 | `P2` | 表仍是空模板，或列名不兼容 |
| 缺初次埋下 | `P2` | 不知道这条线从哪里来 |
| 缺上次回声 | `P3` | 不知道读者上次何时被提醒 |
| 缺下一次轻回声 | `P3` | 后续没有维护计划 |
| 缺兑现方向 | `P3` | 伏笔可能变成只埋不收 |
| 缺禁提前解释 | `P4` | 信息释放边界不稳 |
| 章节文本无命中 | `P4` | 伏笔名未在章节中粗略出现，抽象伏笔可忽略 |
| 上次回声太久 | `P3` | 表中记录的上次回声距最新章节超过阈值 |

### 7.3 解读限制

`audit-echoes` 只能做维护检查，不能替代作者判断。

尤其注意：

- 章节文本命中只是粗略字符串匹配；
- 抽象伏笔可能不会直接出现伏笔名；
- 一张“复盘建议表”可能能被解析，但缺初种/上次回声等字段；
- 工具提示缺字段，不代表故事有问题，只代表项目记忆还不够可维护。

## 15.1 `fictionops audit-info`

检查信息释放表的维护状态。

```bash
fictionops audit-info my-novel
```

默认会寻找 `05_canon/information_release_table.md` 或文件名中带有 information / secret / 信息 / 秘密的 Markdown 表格。

指定信息释放表：

```bash
fictionops audit-info my-novel --table "05_canon/information_release_table.md"
```

输出 JSON：

```bash
fictionops audit-info my-novel --format json
```

关闭正文粗扫：

```bash
fictionops audit-info my-novel --no-text-scan
```

它会检查：

- 表格是否存在；
- 是否能解析出信息/秘密条目；
- 条目是否填写作者真相、读者当前认知、角色/公共/官方版本、下一次释放和禁止提前暴露；
- 若开启正文粗扫，禁止提前暴露项或信息标签是否已经在章节正文中命中；
- 若计划释放位置写成 `ch_010` 这类形式，正文命中是否早于计划释放章节。

常见风险等级：

| 检查 | 等级 | 含义 |
| --- | --- | --- |
| 缺信息释放表 | `P1` | 当前项目没有可维护的信息边界表 |
| 表存在但没有条目 | `P2` | 表仍像空模板，或列名不兼容 |
| 缺作者真相 | `P2` | 无法区分作者真相和角色认知 |
| 正文提前命中禁止项 | `P2` | 可能有提前泄密，需要人工复看 |
| 缺读者/世界内版本 | `P3` | 读者或角色知道什么没有记录 |
| 缺下一次释放 | `P3` | 这条信息后续如何展开不清楚 |
| 缺禁止提前暴露说明 | `P4` | 信息边界缺少保护线 |

`audit-info` 是静态维护工具，不负责判断“这个伏笔是不是应该提前给读者”。它只把可能泄漏或缺记录的位置摆出来。

## 15.2 `fictionops audit-characters`

检查人物弧线、智慧模式、口吻资料和人物索引的维护状态。

```bash
fictionops audit-characters my-novel
```

输出 JSON：

```bash
fictionops audit-characters my-novel --format json
```

指定扫描模式：

```bash
fictionops audit-characters my-novel --pattern "03_characters/**/*.md"
```

它会优先寻找：

- `03_characters/character_index.md`：人物索引；
- `03_characters/intelligence_profiles.md`：智慧模式表；
- `03_characters/voice_profiles.md`：口吻资料表；
- `03_characters/relationship_map.md`：人物关系图；
- `03_characters/character_arcs/*.md`：人物弧线文件。

它会检查：

- 索引里的人物是否有对应弧线；
- 弧线文件是否仍像模板或占位；
- 弧线是否记录身份起点、起始状态、智慧模式、口吻、关系锚点、成长路径和失误路径；
- 人物是否在智慧模式表和口吻表里有资料；
- 弧线文件是否游离在人物索引之外。

常见风险等级：

| 检查 | 等级 | 含义 |
| --- | --- | --- |
| 缺人物索引 | `P3` | 角色名单不可维护 |
| 缺人物弧线目录或弧线文件 | `P3` | 角色成长无法追踪 |
| 索引人物缺弧线 | `P2` | 主要角色可能变成工具人 |
| 缺身份起点、起始状态、智慧模式、口吻或成长路径 | `P2` | 角色区分度和前后变化不稳 |
| 缺失误路径 | `P3` | 角色容易变成永远正确的执行器 |
| 缺关系锚点 | `P4` | 关系网仍可维护，但厚度不足 |

`audit-characters` 只审维护资料是否足够支持长线写作，不判断某个角色是否“写得好”。它适合在写新幕或做人物复盘前运行，帮助作者确认谁的弧线、说话方式和智慧模式还缺记录。

## 15.3 `fictionops model-config`

生成或写出本地模型供应商配置。

```bash
fictionops model-config my-novel --provider local --planning-model planner --drafting-model writer --audit-model auditor
```

常用写法：

```bash
fictionops model-config my-novel --provider openai --planning-model gpt-planner --drafting-model gpt-writer --audit-model gpt-auditor --api-key-env OPENAI_API_KEY
fictionops model-config my-novel --provider local --planning-model planner --drafting-model writer --audit-model auditor --write
fictionops model-config my-novel --provider local --format json
```

它会输出：

- 供应商名；
- 规划、正文、审计三类任务模型；
- API key 环境变量名，以及当前环境是否已经设置；
- base URL；
- 上下文、输出 token 和超时软限制；
- 配置问题清单。

`model-config` 不保存真实 API key，也不调用模型。它只把“后续 Agent 应该怎么找模型配置”记录成 `00_management/model_config.json` 这样的本地文件。

## 15.4 `fictionops agent-prompt`

生成角色专属 Agent 提示词。

```bash
fictionops agent-prompt my-novel --role draft-writer --chapter 001
```

支持的角色：

- `architect`
- `canon-keeper`
- `character-auditor`
- `info-boundary-auditor`
- `foreshadowing-auditor`
- `chapter-planner`
- `draft-writer`
- `style-auditor`
- `publisher`

常用写法：

```bash
fictionops agent-prompt my-novel --role draft-writer --chapter 001
fictionops agent-prompt my-novel --role info-boundary-auditor --task review --chapter 002 --include-context
fictionops agent-prompt my-novel --role canon-keeper --task canon-sync --chapter 010 --format json
fictionops agent-prompt my-novel --role publisher --out 00_management/publisher_prompt.md
```

它会输出：

- 角色边界；
- 输入偏好；
- 必须做；
- 禁止做；
- 工作顺序；
- 输出契约；
- 推荐本地命令。

`agent-prompt` 不调用模型，只生成可交给模型或人类协作者使用的提示词。启用 `--include-context` 时，它会把 `context-pack` 的结果附在提示词后面；若同时启用 `--include-context-content`，可用 `--max-chars-per-file` 和 `--max-total-chars` 控制上下文体量。

## 15.4.1 `fictionops eval-agent`

在临时 fixture 副本上跑一条无网络 Agent harness 评估链。它验证任务包、暂存输出、收件箱复核边界和 controller 下一步停止行为，不调用真实模型供应商，也不修改源项目。

```bash
fictionops eval-agent examples/demo_novel --chapter 002 --out docs/agent-evaluation-smoke.md
```

常用写法：

```bash
fictionops eval-agent examples/demo_novel --chapter 002 --format json
fictionops eval-agent examples/demo_novel --chapter 002 --runner openai-chat-dry-run --out docs/agent-evaluation-smoke.md --force
fictionops eval-agent examples/demo_novel --chapter 002 --dry-run
```

报告会列出 T1-T5 任务链、实际运行的 FictionOps 命令、暂存输出指标、`doctor` 状态、`agent-next` 是否停在人类复核边界，以及下一步建议。它衡量的是 workflow harness 是否可审计、可复核、可恢复，不判断小说文本质量。

## 15.5 `fictionops agent-run`

准备一个可交给人或外部模型 runner 的 Agent 任务包。

```bash
fictionops agent-run my-novel --role draft-writer --chapter 001 --out-dir 00_management/agent_runs/ch_001
```

常用写法：

```bash
fictionops agent-run my-novel --role draft-writer --chapter 001 --out-dir 00_management/agent_runs/ch_001
fictionops agent-run my-novel --role info-boundary-auditor --task review --chapter 002 --out-dir 00_management/agent_runs/review_ch_002 --no-context-content
fictionops agent-run my-novel --role canon-keeper --task canon-sync --chapter 010 --format json
```

它会输出或写出：

- `README.md`：人读说明；
- `request.json`：机器可读任务元数据；
- `prompt.md`：角色提示词；
- `context_pack.md`：范围化上下文；
- `draft_brief.md`：写作任务且有章节时生成。

`agent-run` 当前是 `prepare_only` 模式：它不调用模型、不保存 API key、不覆盖正文。它只是把 `agent-prompt`、`context-pack`、`model-config` 和可选 `draft-brief` 编排成一个稳定任务包。外部 runner 或人工协作者应读取这个目录，把输出写到 staging 文件，再由作者或后续门禁决定是否应用。

## 15.6 `fictionops agent-exec`

把一个已经生成的 Agent run 任务包交给外部 runner 命令执行，并把 runner 的 stdout 保存为暂存输出。

```bash
fictionops agent-exec my-novel/00_management/agent_runs/ch_001 --runner python run_model.py
fictionops agent-exec my-novel/00_management/agent_runs/ch_001 --runner python fictionops/examples/agent_runner_echo.py
fictionops agent-exec my-novel/00_management/agent_runs/ch_001 --runner python fictionops/examples/agent_runner_openai_responses.py --dry-run --model your-model
fictionops agent-exec my-novel/00_management/agent_runs/ch_001 --output-name draft.staging.md --runner local-agent --model writer
fictionops agent-exec my-novel/00_management/agent_runs/ch_001 --dry-run --runner python run_model.py
```

`--runner` 后面的所有参数都会原样传给外部命令；FictionOps 自己的选项必须放在 `--runner` 之前。命令会把 `request.json`、`prompt.md`、`context_pack.md` 和可选 `draft_brief.md` 组合为 stdin。runner 成功退出且 stdout 非空时，stdout 会写入 `output.md` 或 `--output-name` 指定的暂存文件，同时写出 `execution.json` 作为执行回执。

`agent-exec` 可以接真实模型 runner，但 FictionOps 本体不读取真实 API key、不保存 API key、不覆盖正文、不自动应用输出。输出仍需经过 `agent-inbox`、人工审阅和后续门禁。

`examples/agent_runner_echo.py` 是不调用模型的管线示例：它读取 FictionOps stdin，输出一份暂存 Markdown，适合先验证 runner 接入路径。

`examples/agent_runner_openai_responses.py` 是 OpenAI Responses API 外部 runner 示例。先用 `--dry-run` 确认任务包和模型名，再设置 `OPENAI_API_KEY` 去掉 `--dry-run` 运行真实模型；输出仍然只是 staging 文件。

## 15.7 `fictionops agent-inbox`

检查外部 runner 或人工协作者写回 Agent run 目录的暂存输出。

```bash
fictionops agent-inbox my-novel
```

常用写法：

```bash
fictionops agent-inbox my-novel
fictionops agent-inbox my-novel/00_management/agent_runs/ch_001
fictionops agent-inbox my-novel --output-name output.md --format json
```

它会检查：

- `00_management/agent_runs/**/request.json` 是否存在且可解析；
- `request.json` 是否仍声明 `prepare_only` 和安全策略；
- `prompt.md`、`context_pack.md` 等任务包文件是否还在；
- run 目录里是否有唯一、非空的输出文件；
- 输出进入下一步前应该跑哪些 FictionOps 门禁。

默认识别的输出文件名包括 `output.md`、`response.md`、`result.md`、`staging.md`、`model_output.md`、`agent_output.md` 和 `*.staging.md`。如果同一个 run 目录里出现多个候选输出，`agent-inbox` 会标记为 `needs_attention`，要求人工明确保留哪一个。

`agent-inbox` 只读检查，不调用模型、不保存 API key、不应用输出、不覆盖正文。它解决的是“AI 回来的东西有没有被接住、能不能进入门禁”，不是“自动把它写进正史”。

## 15.8 `fictionops agent-next`

为外部 controller 选择下一条安全命令。

```bash
fictionops agent-next my-novel --book book_01 --chapter 001
```

常用写法：

```bash
fictionops agent-next my-novel --format json
fictionops agent-next my-novel --book book_01 --chapter 003 --no-text-scan --format json
fictionops agent-next old-project --format json
fictionops agent-next future-project --format json
fictionops agent-next fictionops --format json
```

它会优先检查：

- 目标是否需要 `init` 或 `adopt`；
- `06_drafts/import_queue/` 是否还有旧稿待归入章节；
- `agent-inbox` 是否有待处理、待复核或多候选输出；
- 指定章节是否缺脚手架、发动机、正文或审稿门禁；
- `doctor`、`book-gate`、`release-gate` 是否提示应该先修订或进入发布链。
- 如果目标是 FictionOps 包目录本身，则读取 `audit-stable-core` 的结构化行动项，选择发布证据、持续 dogfood 或稳定窗口等治理下一步，而不是建议 `adopt`。

JSON 输出包含 `selected_command`、`selected_reason`、`candidates` 和 `evidence`。`agent-next` 只读，不执行选出的命令，不调用模型，不保存密钥，不把暂存输出应用到正文或正史。它解决的是 Level 2 controller 的“下一步该跑哪条安全命令”，不是替作者自动决定小说内容。

## 15.8.1 `fictionops audit-agent-workflow`

审计当前项目是否适合接入外部 AI runner 或 controller。它不调用模型，不执行 controller，只检查项目骨架、暂存输出状态、模型配置和下一步边界。

```bash
fictionops audit-agent-workflow my-novel --level runner
fictionops audit-agent-workflow my-novel --level controller --book book_01 --chapter 001 --format json
fictionops audit-agent-workflow my-novel --level model-runner
```

`--level` 支持：

- `manual`：适合手动把 `context-pack` / `agent-prompt` 交给聊天式 AI；
- `runner`：适合 `agent-run` + `agent-exec` + `agent-inbox`；
- `controller`：适合外部 controller 读取 `agent-next` 并串联安全命令；
- `model-runner`：适合真实模型 runner，额外要求模型供应商配置不能停在占位状态。

输出状态包括：

- `ready`：当前接入层级没有阻塞问题；
- `not_ready`：存在阻塞问题，先修；
- `needs_human_review`：已有暂存输出需要人工复核，controller 应停下；
- `missing_project` / `not_standard_project`：目标还不是可接入的标准项目。

这条命令回答的是“现在能不能安全接 agent”，`agent-next` 回答的是“下一步建议跑哪条命令”。

## 15.9 `fictionops context-pack`

生成范围化上下文包，给写正文、审正文、交接或正史同步使用。

```bash
fictionops context-pack my-novel --task draft --chapter 001
```

常用任务：

```bash
fictionops context-pack my-novel --task draft --chapter 001
fictionops context-pack my-novel --task review --chapter 002 --no-content
fictionops context-pack my-novel --task handoff --max-total-chars 80000 --out 00_management/context_pack.md
fictionops context-pack my-novel --task canon-sync --chapter 010 --format json
```

它会输出：

- 本任务必须先回答的问题；
- 本任务需要读取的文件；
- 哪些文件是必读、哪些只是辅助；
- 哪些必读文件缺失；
- 默认内嵌文件内容，超过 `--max-chars-per-file` 或 `--max-total-chars` 会截断；文件表会显示实际嵌入字符数和截断状态。

任务范围：

- `draft`：书纲、章节发动机、信息边界、上一章和人物/口吻材料；
- `review`：被审章节、发动机、前后章节、信息边界、人物材料；
- `handoff`：当前上下文、交接/决策记录、模型配置、书纲、正史表、人物索引/智慧/口吻资料、复盘、doctor/report、revision-plan、book/release gate 报告；
- `canon-sync`：决策记录、时间线、信息/伏笔表、物件位置、开放问题和可选源章节。

`context-pack` 不调用模型，也不会替作者决定怎么写。它解决的是“这次任务应该喂哪些上下文”的问题，避免 Agent 每次吞全项目，把未来真相泄进当前章节。

## 15.10 `fictionops workflow-plan`

生成分阶段工作流清单，把“从故事种子到发布”的人读流程转成可执行命令、手动步骤和出口标准。

```bash
fictionops workflow-plan my-novel
```

常用写法：

```bash
fictionops workflow-plan my-novel --stage all
fictionops workflow-plan my-novel --stage review --chapter 003
fictionops workflow-plan my-novel --stage publish --book book_01
fictionops workflow-plan my-novel --stage handoff --out 00_management/workflow_plan.md
fictionops workflow-plan my-novel --stage prep --chapter 002 --format json
```

支持的阶段：

| 阶段 | 用途 |
| --- | --- |
| `init` | 项目初始化和可选模型配置边界 |
| `foundation` | 故事种子、世界规则、人物弧线、信息表和伏笔表 |
| `book-plan` | 书级大纲、章节计划和体量波形 |
| `chapter-prep` | 新建章节、同步章节发动机、生成写前上下文 |
| `draft` | 生成正文写手提示词、写草稿、记录写后残留 |
| `review` | 连续性、信息边界、表格、人物、伏笔、词频、风格和体量审计 |
| `book-retrospective` | 书级复盘和长线状态继承 |
| `publish` | 清稿、元数据、manifest、EPUB 和发布审计 |
| `handoff` | doctor/report/context-pack 交接 |

它会输出：

- 分阶段步骤；
- 每步目的；
- 对应本地命令；
- 预计产物；
- 出口标准；
- 可逐条执行的命令列表。

`workflow-plan` 不执行命令、不调用模型、不改正文。它适合在开新阶段前使用，帮助作者和 Agent 确认“现在处于哪一层，下一步先跑什么，哪些事情必须人工判断”。

## 15.11 `fictionops revision-plan`

把现有审计结果整理成按优先级排序的修订任务清单。

```bash
fictionops revision-plan my-novel
```

常用写法：

```bash
fictionops revision-plan my-novel --book book_01
fictionops revision-plan my-novel --format json
fictionops revision-plan my-novel --out 07_audits/revision_plan.md
fictionops revision-plan my-novel --skip-standard --no-text-scan
```

它会复用 continuity、plan、retrospective、echoes、information、characters、scan-words、check-tables、wave、style 和发布层审计，把问题转换成：

- 优先级：P1-P5；
- 区域：连续性、信息边界、计划、表格、伏笔、复盘、节奏、风格、发布；
- 来源命令；
- 问题代码；
- 章节/条目；
- 文件路径；
- 建议动作。

`revision-plan` 不改正文，也不调用模型。它的作用是帮作者决定“先修什么、后修什么”，避免被一堆审计结果淹没。

## 16. `fictionops doctor`

一键运行项目健康总览。

```bash
fictionops doctor my-novel
```

`doctor` 会汇总：

- `stats`：章节体量；
- `audit-wave`：章节体量波形、平直段、同档连续和体量突跳；
- `audit-style`：高频风格标记、重复句首、开头/结尾类型；
- `scan-words`：通用高频词、短语和关注词命中；
- `check-tables`：Markdown 表格结构、重复表头、行宽和占位行；
- `audit-continuity`：章节发动机、复盘、标准项目记忆文件；
- `audit-echoes`：伏笔表、伏笔字段完整度、粗略文本命中；
- `audit-info`：信息释放表、角色/公共/官方认知版本、禁止提前暴露项；
- `audit-characters`：人物索引、人物弧线、智慧模式和口吻资料；
- `audit-plan`：书纲逐章规划、正文文件和章节发动机同步情况；
- `retrospective`：逐章复盘、书级复盘和待同步项收束情况；
- `book-gate`：书级收束门禁的状态、阻塞项和检查摘要；
- `model-config`：模型供应商、任务模型、密钥环境变量名和安全策略；
- `agent-inbox`：Agent run 目录里的回传输出状态；
- `audit-publish`：clean Markdown 发布稿的章节顺序、缺章、草稿标记和短章检查；
- `export-metadata`：发布清单里的作者名、分类、标签、简介和内容提示状态；
- `export-manifest`：发布包 manifest 是否已导出、是否与当前 clean Markdown 和 metadata JSON 匹配；
- `export-epub` / `audit-epub`：EPUB 是否已导出、基础结构是否可打开、是否早于当前 clean Markdown、metadata JSON 或 manifest；
- `release-gate`：发布门禁的最终状态、阻塞项和检查摘要。

输出 JSON：

```bash
fictionops doctor my-novel --format json
```

指定纳入总览的书：

```bash
fictionops doctor my-novel --book book_01
```

指定计划审计使用的书纲：

```bash
fictionops doctor my-novel --book book_01 --outline 04_structure/book_outlines/book_01_outline.md
```

对非标准目录跳过标准项目文件检查：

```bash
fictionops doctor my-book-dir --skip-standard
```

强制检查标准项目文件：

```bash
fictionops doctor my-book-dir --strict-standard
```

包含所有 Markdown，而不是只统计章节：

```bash
fictionops doctor my-novel --all
fictionops doctor my-novel --flat-tolerance 200
fictionops doctor my-novel --min-spread-ratio 15
```

关闭伏笔文本扫描：

```bash
fictionops doctor my-novel --no-text-scan
```

### 13.1 健康状态

| 状态 | 含义 |
| --- | --- |
| `pass` | 没有维护缺口 |
| `review` | 只有 P4 级问题，适合清理但不阻塞 |
| `maintenance_needed` | 有 P3 级缺口，如缺复盘或计划字段 |
| `needs_attention` | 有 P2 级缺口，如缺章节发动机或伏笔表无法解析 |
| `critical` | 有 P1 级缺口，如缺必要项目记忆或伏笔表 |

这些状态只代表 FictionOps 项目维护健康度，不代表小说质量。

### 13.2 自动标准项目检查

`doctor` 默认会自动判断目标是否像标准 FictionOps 项目：

- 有 `project.yml`；
- 或有 `00_management`；
- 或有 `05_canon`；
- 或有 `06_drafts`。

如果目标不像标准项目，则自动跳过标准项目文件检查，以便直接审计普通书稿目录。可以用 `--strict-standard` 强制开启。

### 13.3 计划层检查

`doctor` 默认会尝试把 `book_01` 的计划层纳入总览。

- 如果找到 `04_structure/book_outlines/book_01_outline.md`，会汇总计划章节、正文文件、发动机文件、已同步发动机和计划层问题数；
- 如果找不到书纲，Plan 区块会标为 skipped，不会导致 `doctor` 失败；
- 如果显式传入 `--outline`，但路径不存在，则会报错。

### 13.4 写后复盘检查

`doctor` 默认也会尝试把同一本书的写后复盘纳入总览。

- 如果目标目录下存在 `06_drafts/book_01/` 或 `07_audits/book_retrospectives/book_01_retrospective.md`，会汇总正文章数、逐章复盘数、缺失复盘、占位复盘和待同步项；
- 如果没有找到对应书稿或书级复盘，Retrospective 区块会标为 skipped，不会导致 `doctor` 失败；
- `--book` 会同时影响 Plan 和 Retrospective 两个区块；
- 打开待同步项会推高健康状态，因为它表示“写后发现的问题还没有回写到人物、设定、伏笔或后续大纲”。

### 13.5 发布稿检查

`doctor` 会在发现默认 clean Markdown 时自动纳入发布稿检查。

- 默认检查 `08_publish/clean_markdown/book_01.md`；
- 如果 clean Markdown 不存在，Publish 区块会标为 skipped，不会把未进入发布阶段的项目判为失败；
- 如果 clean Markdown 存在，`audit-publish` 的 P2/P3 问题会进入总健康状态；
- `--book` 会影响默认 clean Markdown 路径；
- `--min-chapter-chars` 会同时影响连续性占位检查和发布稿短章检查。

### 13.6 发布元数据检查

`doctor` 会在发布阶段启动后自动纳入发布元数据检查。

- 默认读取 `08_publish/publish_checklist.md`；
- 默认关注 `08_publish/metadata/book_01_metadata.json`；
- 如果 clean Markdown、metadata JSON 和已填写发布清单都不存在，Metadata 区块会标为 skipped；
- 如果 clean Markdown 已经存在，发布清单里的必填元数据缺口会进入总健康状态；
- 如果发布清单已经开始填写，即使 clean Markdown 还没生成，Metadata 区块也会显示当前缺口；
- `--book` 会影响默认 metadata JSON 路径。

### 13.7 发布包清单检查

`doctor` 会在发布包阶段启动后自动纳入 manifest 检查。

- 默认关注 `08_publish/manifest/book_01_manifest.json`；
- 如果 clean Markdown、metadata JSON 和 manifest 都不存在，Manifest 区块会标为 skipped；
- 如果 clean Markdown 或 metadata JSON 已经存在，Manifest 区块会检查发布包输入是否齐全；
- 如果 clean Markdown 和 metadata JSON 都存在，但 manifest 还没导出，会产生维护提示；
- 如果 manifest 已存在，但记录的 hash 和当前 clean Markdown 或 metadata JSON 不一致，会标记为过期；
- `--book` 会影响默认 manifest 路径。

### 13.8 EPUB 检查

`doctor` 会在发布包阶段启动后自动纳入 EPUB 检查。

- 默认关注 `08_publish/epub/book_01.epub`；
- 如果 clean Markdown、metadata JSON、manifest 和 EPUB 都不存在，EPUB 区块会标为 skipped；
- 如果 clean Markdown、metadata JSON 和 manifest 都存在，但 EPUB 还没导出，会产生维护提示；
- 如果 EPUB 已存在，会检查它是否能作为 zip 打开，是否包含 `mimetype`、`META-INF/container.xml`、`OEBPS/content.opf`、`OEBPS/nav.xhtml` 和章节 XHTML；
- 如果 EPUB 早于当前 clean Markdown、metadata JSON 或 manifest，会标记为过期；
- `--book` 会影响默认 EPUB 路径。

### 13.9 模型配置检查

`doctor` 会对标准 FictionOps 项目纳入模型配置检查。

- 如果 `00_management/model_config.json` 不存在，会读取默认占位配置，并提示供应商或模型名仍未配置；
- 如果配置记录了 API key 环境变量名，会检查当前 shell 是否设置了该变量；
- 如果配置允许保存真实 key，会标记为不安全；
- 这个检查不调用模型，也不会读取真实 API key。

### 13.10 Agent 输出收件箱检查

`doctor` 会在发现 `00_management/agent_runs` 时自动纳入 Agent 输出收件箱摘要。

- 如果没有 agent run 目录，Agent Inbox 区块会标为 skipped，不会影响项目健康状态；
- 如果 run 目录里还没有输出文件，会作为轻提示进入收件箱摘要；
- 如果同一个 run 目录里有多个输出候选、空输出或坏 request，会计入项目健康状态；
- 这个检查不调用模型，不应用输出，也不覆盖正文。

## 17. `fictionops report`

把 `doctor` 的项目健康总览输出成可归档报告。报告会包含同样的 Stats、Wave、Style、Continuity、Echoes、Information、Plan、Retrospective、Agent Inbox、Model Config、Publish、Metadata、Manifest 和 EPUB 摘要。

```bash
fictionops report my-novel --out 07_audits/doctor_report.md
```

默认格式是 Markdown；如果不指定 `--out`，报告会直接打印到终端：

```bash
fictionops report my-novel
```

输出 JSON：

```bash
fictionops report my-novel --format json
fictionops report my-novel --format json --out 07_audits/doctor_report.json
```

相对路径的 `--out` 会写入目标目录内部。如果目标是单个文件，则写入该文件所在目录。

默认不会覆盖已有报告：

```bash
fictionops report my-novel --out 07_audits/doctor_report.md
fictionops report my-novel --out 07_audits/doctor_report.md --force
```

`report` 支持与 `doctor` 相同的审计参数，例如：

```bash
fictionops report my-novel --skip-standard --no-text-scan
fictionops report my-novel --all --metric cjk --flat-tolerance 200 --stale-after 10
fictionops report my-novel --book book_01 --out 07_audits/doctor_report.md
```

使用建议：

- 临时查看项目健康度，用 `doctor`；
- 写入阶段性复盘、交接日志或发布前检查，用 `report`；
- Markdown 适合给人读，JSON 适合给后续 agent 或脚本接着处理。

## 18. `fictionops export-clean`

把一本书的章节草稿合并成发布用 clean Markdown。

```bash
fictionops export-clean my-novel --book book_01
```

默认输出：

```text
08_publish/clean_markdown/book_01.md
```

指定标题和输出路径：

```bash
fictionops export-clean my-novel --book book_01 --title "第一本" --out 08_publish/clean_markdown/book_01.md
```

输出 JSON 摘要：

```bash
fictionops export-clean my-novel --book book_01 --format json
```

预览而不写文件：

```bash
fictionops export-clean my-novel --book book_01 --dry-run
```

默认不会覆盖已有 clean Markdown：

```bash
fictionops export-clean my-novel --book book_01
fictionops export-clean my-novel --book book_01 --force
```

说明：

- 只读取 `06_drafts/<book>/chapters/*.md`；
- 按自然章节顺序合并；
- 会移除 `new-chapter` 初始生成的精确草稿标记 `> Draft starts here.`；
- 不修改草稿源文件；
- 这是发布层的最小闭环，不做 EPUB 打包，也不替作者清稿校对。

## 19. `fictionops audit-publish`

检查 clean Markdown 发布稿是否还存在维护风险。

```bash
fictionops audit-publish my-novel --book book_01
```

默认检查：

```text
08_publish/clean_markdown/book_01.md
```

输出 JSON：

```bash
fictionops audit-publish my-novel --book book_01 --format json
```

指定 clean Markdown 文件：

```bash
fictionops audit-publish my-novel --file 08_publish/clean_markdown/book_01.md
```

调整短章阈值：

```bash
fictionops audit-publish my-novel --book book_01 --min-chapter-chars 1000
```

它会检查：

- clean Markdown 文件是否存在；
- 是否还能识别章节标题；
- 源草稿章节数和 clean 章节数是否一致；
- 章节号是否重复、倒退或缺号；
- 是否残留 `Draft starts here`；
- 是否有低于阈值的短章。

说明：

- `audit-publish` 只做发布稿维护检查，不判断文学质量；
- 如果 clean Markdown 不存在，它会把缺失作为审计问题输出，而不是直接失败；
- 如果传入的 `path` 本身是 Markdown 文件，则直接审计该文件。

## 20. `fictionops publish-copy`

根据发布清单、故事种子、书纲和 clean Markdown，生成可编辑的简介、标签和关键词草稿。

```bash
fictionops publish-copy my-novel --book book_01
```

默认读取：

```text
08_publish/publish_checklist.md
01_story_seed/story_seed.md
04_structure/book_outlines/book_01_outline.md
08_publish/clean_markdown/book_01.md
```

默认输出：

```text
08_publish/synopsis/book_01_publish_copy.md
```

输出 JSON 摘要：

```bash
fictionops publish-copy my-novel --book book_01 --format json
```

指定来源文件：

```bash
fictionops publish-copy my-novel --clean-file 08_publish/clean_markdown/book_01.md
fictionops publish-copy my-novel --outline-file 04_structure/book_outlines/book_01_outline.md
fictionops publish-copy my-novel --seed-file 01_story_seed/story_seed.md
fictionops publish-copy my-novel --checklist-file 08_publish/publish_checklist.md
```

预览而不写文件：

```bash
fictionops publish-copy my-novel --book book_01 --dry-run --format json
```

默认不会覆盖已有草稿：

```bash
fictionops publish-copy my-novel --book book_01
fictionops publish-copy my-novel --book book_01 --force
```

它会生成：

- 标题候选；
- 标签候选；
- 关键词候选；
- 短简介与长简介草稿；
- 来源证据摘要；
- 可选来源缺失提示。

说明：

- `publish-copy` 不调用模型，不直接修改 `08_publish/publish_checklist.md`；
- 它生成的是发布文案草稿，不是最终简介；
- 作者确认后，再把接受的简介、标签和关键词写入发布清单，然后运行 `export-metadata`。

## 21. `fictionops export-metadata`

从发布清单中抽取书名、作者名、分类、标签、简介、封面图片和内容提示等发布元数据，导出为 JSON。

```bash
fictionops export-metadata my-novel --book book_01
```

默认读取：

```text
08_publish/publish_checklist.md
```

默认输出：

```text
08_publish/metadata/book_01_metadata.json
```

输出 JSON 摘要：

```bash
fictionops export-metadata my-novel --book book_01 --format json
```

指定发布清单或输出路径：

```bash
fictionops export-metadata my-novel --file 08_publish/publish_checklist.md
fictionops export-metadata my-novel --out 08_publish/metadata/book_01_metadata.json
```

预览而不写文件：

```bash
fictionops export-metadata my-novel --book book_01 --dry-run
```

默认不会覆盖已有 metadata JSON：

```bash
fictionops export-metadata my-novel --book book_01
fictionops export-metadata my-novel --book book_01 --force
```

它会检查：

- 发布清单是否存在；
- 书名、作者名、分类、标签、短简介和长简介是否为空；
- 标签是否过少；
- 简介是否短到像占位；
- 内容提示决策是否记录。

说明：

- `export-metadata` 只从清单提取发布信息，不替作者生成简介或封面；简介和标签候选可先用 `publish-copy` 起草；
- 它会写出机器可读 JSON，方便后续 EPUB、站点发布或 Agent 交接；
- 如果传入的 `path` 本身是 Markdown 文件，则直接读取该文件作为发布清单。

## 22. `fictionops export-manifest`

把 clean Markdown 和 metadata JSON 组合成发布包 manifest，记录路径、文件大小、SHA256 和基础统计。若 metadata JSON 里填写了 `cover_image`，manifest 也会记录封面图片。

```bash
fictionops export-manifest my-novel --book book_01
```

默认读取：

```text
08_publish/clean_markdown/book_01.md
08_publish/metadata/book_01_metadata.json
```

默认输出：

```text
08_publish/manifest/book_01_manifest.json
```

输出 JSON 摘要：

```bash
fictionops export-manifest my-novel --book book_01 --format json
```

指定 clean Markdown、metadata JSON 或输出路径：

```bash
fictionops export-manifest my-novel --clean-file 08_publish/clean_markdown/book_01.md
fictionops export-manifest my-novel --metadata-file 08_publish/metadata/book_01_metadata.json
fictionops export-manifest my-novel --out 08_publish/manifest/book_01_manifest.json
```

预览而不写文件：

```bash
fictionops export-manifest my-novel --book book_01 --dry-run
```

默认不会覆盖已有 manifest：

```bash
fictionops export-manifest my-novel --book book_01
fictionops export-manifest my-novel --book book_01 --force
```

它会检查：

- clean Markdown 是否存在；
- metadata JSON 是否存在；
- metadata JSON 是否能解析；
- clean Markdown、metadata JSON 和可选封面图片的大小和 SHA256 是否能记录进 manifest。

说明：

- `export-manifest` 不替代 `audit-publish` 或 `export-metadata`；
- 它的职责是把已经生成的发布文件组合成可校验清单；
- 后续 EPUB、站点发布或归档流程可以读取这个 manifest，而不是重新猜测文件位置。

## 23. `fictionops export-epub`

从发布 manifest、clean Markdown 和 metadata JSON 导出带基础样式、可选封面的 EPUB3 文件。

```bash
fictionops export-epub my-novel --book book_01
```

默认读取：

```text
08_publish/manifest/book_01_manifest.json
08_publish/clean_markdown/book_01.md
08_publish/metadata/book_01_metadata.json
```

默认输出：

```text
08_publish/epub/book_01.epub
```

输出 JSON 摘要：

```bash
fictionops export-epub my-novel --book book_01 --format json
```

指定 manifest、clean Markdown、metadata JSON、封面或输出路径：

```bash
fictionops export-epub my-novel --manifest-file 08_publish/manifest/book_01_manifest.json
fictionops export-epub my-novel --clean-file 08_publish/clean_markdown/book_01.md
fictionops export-epub my-novel --metadata-file 08_publish/metadata/book_01_metadata.json
fictionops export-epub my-novel --cover-file 08_publish/assets/cover.png
fictionops export-epub my-novel --out 08_publish/epub/book_01.epub
```

预览而不写文件：

```bash
fictionops export-epub my-novel --book book_01 --dry-run
```

默认不会覆盖已有 EPUB：

```bash
fictionops export-epub my-novel --book book_01
fictionops export-epub my-novel --book book_01 --force
```

说明：

- `export-epub` 会生成 EPUB3 包，包含 `mimetype`、`META-INF/container.xml`、`OEBPS/content.opf`、`OEBPS/nav.xhtml`、默认 CSS 和章节 XHTML；
- 如果 metadata JSON 或 manifest 记录了 `cover_image`，或命令行传入 `--cover-file`，EPUB 会加入封面页和封面图片；
- 它不做复杂排版，也不替代专业终校；
- 如果 manifest 不存在，会提示维护问题并尝试使用默认 clean Markdown 和 metadata JSON 路径。

## 24. `fictionops audit-epub`

检查已经导出的 FictionOps EPUB 包是否可作为发布物使用。

```bash
fictionops audit-epub my-novel --book book_01
```

默认检查：

```text
08_publish/epub/book_01.epub
08_publish/manifest/book_01_manifest.json
08_publish/clean_markdown/book_01.md
08_publish/metadata/book_01_metadata.json
```

输出 JSON 摘要：

```bash
fictionops audit-epub my-novel --book book_01 --format json
```

也可以直接检查某个 EPUB 文件：

```bash
fictionops audit-epub 08_publish/epub/book_01.epub
fictionops audit-epub my-novel --file 08_publish/epub/book_01.epub
```

指定对照输入：

```bash
fictionops audit-epub my-novel --manifest-file 08_publish/manifest/book_01_manifest.json
fictionops audit-epub my-novel --clean-file 08_publish/clean_markdown/book_01.md
fictionops audit-epub my-novel --metadata-file 08_publish/metadata/book_01_metadata.json
```

它会检查：

- EPUB 是否存在、是否能作为 zip 打开；
- `mimetype` 是否位于第一项，内容是否为 `application/epub+zip`；
- 是否包含 `META-INF/container.xml`、`OEBPS/content.opf`、`OEBPS/nav.xhtml`、默认 CSS 和章节 XHTML；
- 如果 OPF 声明封面，封面页和封面图片是否真的打进包里；
- EPUB 是否早于 clean Markdown、metadata JSON、manifest 或封面图片。

说明：

- `audit-epub` 不重新生成 EPUB，只检查已有文件；
- `doctor/report` 的 EPUB 区块复用这套审计逻辑；
- 结构损坏是 P2，缺失或过期通常是 P3。

## 25. `fictionops release-gate`

聚合最终发布前的检查：书级收束、clean Markdown、发布元数据、manifest 和 EPUB 是否存在、有效、没有过期。

```bash
fictionops release-gate my-novel --book book_01
```

输出 JSON：

```bash
fictionops release-gate my-novel --book book_01 --format json
```

写入最终发布门禁报告：

```bash
fictionops release-gate my-novel --book book_01 --out 07_audits/release_gate/book_01_release_gate.md
fictionops release-gate my-novel --book book_01 --out 07_audits/release_gate/book_01_release_gate.md --force
```

状态：

| Status | 含义 |
| --- | --- |
| `needs_release_artifacts` | 缺 clean Markdown、metadata、manifest 或 EPUB 等发布物 |
| `needs_release_fixes` | 发布物存在，但存在结构损坏、过期或 hash 不匹配等阻塞问题 |
| `release_notes` | 没有阻塞项，但有非阻塞提示 |
| `ready_for_release` | 可以上传或归档发布包 |

说明：

- 它不生成任何发布物；生成仍由 `export-clean`、`export-metadata`、`export-manifest` 和 `export-epub` 完成；
- 它会先嵌入 `book-gate` 的收束状态；发布包能生成不等于这本书已经完成维护闭合；
- 它会把 metadata JSON 早于发布清单、manifest hash 不匹配、EPUB 早于输入文件等视为发布阻塞；
- 它适合放在 `audit-epub` 之后，作为上传/归档前最后一道本地门禁。

## 26. `fictionops audit-release-evidence`

审计 FictionOps 自身包发布演练证据。它不检查小说项目的发布物，而是检查 `docs/release-trial-evidence.md` 或 workflow 生成的 release trial evidence 草稿是否已经填成真实外部证据。

```bash
fictionops audit-release-evidence . --file docs/release-trial-evidence.md
fictionops audit-release-evidence . --file release-trial-evidence-0.1.0.md --format json
```

状态：

| Status | 含义 |
| --- | --- |
| `missing` | 找不到证据文件 |
| `incomplete` | 仍有空字段、占位值、无效 URL/hash 或缺安装烟测 |
| `deferred` | 证据记录存在，但结论仍是延期 |
| `failed` | 外部演练已经失败，需要修复后重跑 |
| `accepted` | 外部 run、artifact hash、安装烟测和最终结论都已填实 |

说明：

- 只读，不写文件；
- `ready=true` 只会在 `Decision: accepted` 且无阻塞问题时出现；
- 空模板、未复核的 workflow 草稿、`deferred` 记录都不能关闭 0.4 Release Trial。

## 27. `fictionops audit-dogfood-cycle`

审计 1.0 stable core 需要的持续真实项目 dogfood 周期证据。它不重新跑迁移，也不修改项目，只检查 `docs/dogfood-cycle-evidence.md` 或指定证据文件是否已经填成可验收记录。

```bash
fictionops audit-dogfood-cycle . --file docs/dogfood-cycle-evidence.md
fictionops audit-dogfood-cycle . --file dogfood-cycle-2026-07.md --format json
```

状态：

| Status | 含义 |
| --- | --- |
| `missing` | 找不到证据文件 |
| `incomplete` | 仍有空字段、占位值、非 ready 最终状态或非零阻塞项 |
| `deferred` | 周期记录存在，但结论仍是延期 |
| `failed` | 周期暴露回归或契约漂移，需要修复后重跑 |
| `accepted` | 持续周期、收口状态、兼容性说明和恢复说明都已填实 |

说明：

- 只读，不写文件；
- `ready=true` 只会在 `Decision: accepted`、最终状态 ready/complete、`import_queue_files=0`、`blocking_issue_count=0` 且无阻塞问题时出现；
- 0.2 迁移收口记录本身不能替代 1.0 的持续维护周期。

## 28. `fictionops audit-stability-window`

审计 1.0 stable core 所需的稳定窗口证据。它不替代真实经过时间的使用，只检查 `docs/stability-window-evidence.md` 或指定证据文件是否已经填成可验收记录。

```bash
fictionops audit-stability-window . --file docs/stability-window-evidence.md
fictionops audit-stability-window . --file stability-window-2026-07.md --format json
```

状态：

| Status | 含义 |
| --- | --- |
| `missing` | 找不到稳定窗口证据文件 |
| `incomplete` | 仍有空字段、占位值、非 accepted 结论或阻塞问题 |
| `deferred` | 窗口记录存在，但结论仍是延期 |
| `failed` | 稳定窗口暴露兼容性或恢复问题 |
| `accepted` | 稳定窗口证据已经填实且可作为 1.0 证据 |

说明：
- 只读，不写文件；
- `ready=true` 只会在 `Decision: accepted`，窗口 id、日期、版本范围、release/dogfood 证据引用、兼容性说明、破坏性变化说明和恢复说明都填实，且无阻塞问题时出现；
- 空模板和预填的未来窗口都不能关闭 1.0。

## 29. `fictionops audit-stable-core`

聚合审计 1.0 stable core 是否真的可以关闭。它会同时检查本地治理文件、发布演练证据、持续 dogfood 周期证据、稳定窗口证据、`stable-core-audit.md` 结论和 `milestone-status.md` 状态。

```bash
fictionops audit-stable-core .
fictionops audit-stable-core . --release-file filled-release.md --dogfood-file filled-dogfood.md --stability-file filled-stability.md --format json
```

状态：

| Status | 含义 |
| --- | --- |
| `not_ready` | 至少一个阻塞证据缺失、未 accepted 或文档声明与证据冲突 |
| `ready_needs_docs_update` | 证据已满足，但稳定核心审计/里程碑文档还没有同步 |
| `ready` | 发布证据、dogfood、稳定窗口、本地治理文件和里程碑声明全部一致 |

说明：

- 只读，不写文件；
- 不发布包，不修改证据，不替代外部 GitHub Actions/TestPyPI/PyPI 记录；
- 1.0 完成前应要求它返回 `ready=true`。

## 附录：`adopt --copy-to` 迁移沙盒

`fictionops adopt` 默认只生成诊断报告。传入 `--copy-to <project>` 时，它会把扫描到的候选文件复制到一个已经初始化、带 `project.yml` 的独立 FictionOps 项目中，目标路径来自 `suggested_target_path`。

```bash
fictionops init migrated-novel --title "迁移沙盒"
fictionops adopt existing-novel --copy-to migrated-novel --format json
```

规则：
- 旧目录仍然只读，不会被修改。
- `--copy-to` 目标不能位于被扫描的旧目录内部。
- 已有目标文件默认跳过；传入 `--force` 才覆盖。
- 同一轮复制中如果多个源文件映射到同一目标路径，会自动生成带源路径上下文和短 hash 的唯一目标路径，不会跳过候选材料。
- 实际复制后会写出 `00_management/adopted_handoff/adopt_manifest.json`，记录源路径、目标路径和复制状态，供后续 `import-plan` 辅助判断书/章归属。
- JSON 输出会包含 `copy_to`、`copied_files`、`skipped_files`、`planned_copies` 和 `copy_files`。

## 附录：`adopt-review` 迁移后复查

`fictionops adopt-review` 用于复查迁移沙盒。它不会复制或移动文件，而是聚合 `doctor`、`audit-info`、`audit-characters` 和 `book-gate`，给出迁移后还卡在哪里。

```bash
fictionops adopt-review migrated-novel --book book_01 --format json
fictionops adopt-review migrated-novel --out 07_audits/adopt_review/report.md
```

重点状态：
- `needs_import_sorting`：`06_drafts/import_queue/` 中还有导入正文，需要先归入书/章目录。
- `needs_migration_fixes`：信息边界、人物资料、标准项目文件或书级门禁仍有阻塞项。
- `migration_notes`：没有阻塞项，但还有非阻塞维护提示。
- `ready_for_project_work`：迁移沙盒可以进入常规 FictionOps 工作流。
## 附录：`adopt-plan` 迁移整改计划

`fictionops adopt-plan` 用于把 `adopt-review` 的复查结果转成优先级任务清单。它不移动文件、不修改正文，只告诉你先处理哪些迁移问题。

```bash
fictionops adopt-plan migrated-novel --book book_01
fictionops adopt-plan migrated-novel --out 07_audits/adopt_review/plan.md
fictionops adopt-plan migrated-novel --write-groups 07_audits/adopt_review/repair_groups
fictionops adopt-plan migrated-novel --format json
```

典型用途：
- `adopt-review` 显示 `needs_import_sorting` 后，生成清理 `06_drafts/import_queue/` 的任务。
- 将信息边界、人物资料、书级门禁问题拆成带 `priority`、`area`、`source_command`、`code`、`path` 和 `suggested_action` 的任务。
- 在真实迁移问题较多时，先看 `task_groups` / Markdown 中的 `Repair Groups`，按迁移形状、正史边界、人物记忆、书稿结构、表格清理、体量风格等阶段处理同类问题，再进入逐条任务。
- 需要交给人或 agent 逐组处理时，使用 `--write-groups` 写出 `index.md` 和每个修复组的工作文件；这些文件只记录整改任务，不会修改正文或设定。
- 迁移整改完成后，再跑 `fictionops adopt-review migrated-novel --book book_01` 确认沙盒是否进入常规工作流。

## 附录：`import-plan` 导入队列整理计划

`fictionops import-plan` 用于检查 `06_drafts/import_queue/` 中尚未归入书/章目录的正文类文件。它默认只生成计划；只有传入 `--apply` 时才会移动文件，并且只移动章号明确、目标不存在、目标不重复的文件。若沙盒中存在 `00_management/adopted_handoff/adopt_manifest.json`，它会优先利用旧源路径辅助推断书号。传入 `--apply --create-scaffolds` 时，它还会为已移动章节补齐缺失的章节发动机和逐章复盘，但不会覆盖已有文件。若目标文件只是初始化生成的占位章节，可显式加 `--replace-placeholder-targets` 替换；真实已有正文仍会保留为人工复查。

```bash
fictionops import-plan migrated-novel --book book_01
fictionops import-plan migrated-novel --out 07_audits/adopt_review/import_plan.md
fictionops import-plan migrated-novel --format json
fictionops import-plan migrated-novel --apply
fictionops import-plan migrated-novel --apply --create-scaffolds
fictionops import-plan migrated-novel --apply --create-scaffolds --replace-placeholder-targets
```

典型用途：
- `adopt-review` 显示 `needs_import_sorting` 后，先用 `import-plan` 生成逐文件整理建议。
- 对 `ready` 行，可传入 `--apply` 安全移动到 `06_drafts/<book>/chapters/ch_XXX.md`。
- 对已移动章节，可传入 `--create-scaffolds` 一并生成 `chapter_engines/` 和 `revision_notes/` 中的维护入口。
- 对 `placeholder_target` 行，可在确认目标只是模板占位后传入 `--replace-placeholder-targets` 替换。
- 对 `needs_chapter`、`target_exists`、`duplicate_target` 行，保留人工复查，避免误覆盖或误归书。
- 移动并补齐配套文件后，再重跑 `fictionops adopt-review migrated-novel --book book_01`。

## FictionOps 源码包的 agent 预检

如果 `audit-agent-workflow` 的目标是 FictionOps 源码包 checkout 本身，并且层级为 `--level controller`，命令会进入 package governance 模式：它不会建议 `adopt`，而会复用 `agent-next` 的 stable-core action items。需要真实外部发行、持续 dogfood 或稳定窗口证据的下一步会返回 `needs_human_review`，提醒外部 controller 停下等待维护者确认。
